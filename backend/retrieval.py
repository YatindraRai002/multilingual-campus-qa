from __future__ import annotations

import time
from collections import Counter
from datetime import datetime, timedelta, timezone

from backend.college import COLLEGE, VERIFIED_STATUSES, is_verified, require_benchmark_complete, validate_faq
from backend.modeling import PrerequisiteError
from backend.settings import ROOT, config, digest, read_json, read_jsonl, utcnow, write_json


def chunks(text: str, size: int, overlap: int):
    if not 0 <= overlap < size:
        raise ValueError("Chunk overlap must be smaller than the chunk size")
    start = 0
    while start < len(text):
        end = min(start+size,len(text))
        # Keep combining characters attached to their base character when selecting a boundary.
        import unicodedata
        while end < len(text) and unicodedata.category(text[end]).startswith('M'):
            end += 1
        yield text[start:end]
        if end == len(text):
            break
        next_start = end-overlap
        while next_start > start and unicodedata.category(text[next_start]).startswith('M'):
            next_start -= 1
        # A combining sequence longer than the chunk budget must not loop forever.
        start = next_start if next_start > start else end


class Embedder:
    def __init__(self, model_id: str, revision: str, device="cpu"):
        if not revision:
            raise PrerequisiteError("Pin an embedding revision through embedding evaluation before ingestion.")
        from sentence_transformers import SentenceTransformer
        self.model_id = model_id
        self.model = SentenceTransformer(model_id,revision=revision,device=device,trust_remote_code=False)
    def encode(self, texts: list[str], *, query=False):
        if "multilingual-e5" in self.model_id:
            texts = [("query: " if query else "passage: ")+text for text in texts]
        return self.model.encode(texts,normalize_embeddings=True,batch_size=16,show_progress_bar=False).tolist()


def _client(path=None):
    import chromadb
    from chromadb.config import Settings
    return chromadb.PersistentClient(path=str(path or ROOT/"data"/"chroma"),
                                    settings=Settings(anonymized_telemetry=False))


def accepted_verification(settings):
    statuses=settings.get('accepted_verification_statuses',list(VERIFIED_STATUSES))
    if not statuses or not set(statuses).issubset(VERIFIED_STATUSES):
        raise ValueError('Only explicit source-verified or human-verified records may be indexed')
    return statuses


def ingest():
    require_benchmark_complete()
    settings = config("retrieval")
    if settings["embedding_status"] != "validated":
        raise PrerequisiteError("Evaluate candidate embeddings on reviewed en/hi/ta retrieval validation questions before choosing a model.")
    manifest = read_json(COLLEGE/"manifest.json")
    if not manifest:
        raise PrerequisiteError("No verified FAQ corpus has been collected.")
    records = [validate_faq(r) for r in read_jsonl(COLLEGE/"versions"/manifest["version"]/"faq.jsonl")
               if r["verification_status"] in accepted_verification(settings)]
    now = datetime.now(timezone.utc)
    cutoff = now-timedelta(days=settings["max_source_age_days"])
    records = [r for r in records if datetime.fromisoformat(r["verified_at"]) >= cutoff and
               (not r.get("effective_date") or r["effective_date"] <= now.date().isoformat())]
    if not records:
        raise PrerequisiteError("No fresh, source-verified or human-verified records are available for ingestion.")
    embedder = Embedder(settings["embedding_model"],settings["embedding_revision"],settings["device"])
    version = digest({"corpus":manifest["version"],"settings":settings,"records":records})[:16]
    collection_name = f"{settings['collection']}_{version}"
    client = _client()
    collection = client.get_or_create_collection(collection_name,metadata={"hnsw:space":"cosine","corpus_version":manifest["version"],
                                "embedding_model":settings["embedding_model"],"embedding_revision":settings["embedding_revision"]},embedding_function=None)
    documents, metadata, ids = [], [], []
    for row in records:
        for index, text in enumerate(chunks(row["answer"],settings["chunk_characters"],settings["chunk_overlap"])):
            documents.append(row["canonical_question"]+"\n"+text)
            ids.append(digest([row["faq_id"],row["language"],row["document_version"],index]))
            metadata.append({key: row[key] for key in ["faq_id","language","category","canonical_question","source_url",
                            "source_title","source_document_id","verification_status","document_version","verified_at"]} |
                            {"answer":text,"effective_date":row.get("effective_date") or "", "chunk":index,
                             'reviewer_kind':row.get('reviewer_kind') or 'human',
                             'human_review_status':row.get('human_review_status') or 'reviewed',
                             'translation_status':row['translation_status'],'verified_by':row['verified_by'],
                             'review_method':row.get('review_method') or 'human_review',
                             'evidence_quote':row['evidence_quote']})
    for offset in range(0,len(ids),32):
        collection.upsert(ids=ids[offset:offset+32],documents=documents[offset:offset+32],metadatas=metadata[offset:offset+32],
                          embeddings=embedder.encode(documents[offset:offset+32]))
    result = {"version":version,"collection":collection_name,"corpus_version":manifest["version"],"chunks":len(ids),
              "faq_records":len(records),"languages":dict(Counter(r["language"] for r in records)),
              'reviewer_kinds':dict(Counter(r['reviewer_kind'] for r in records)),
              "configuration":settings,"created_at":utcnow(),"content_fingerprint":digest(sorted(zip(ids,documents,metadata),key=lambda item:item[0]))}
    write_json(COLLEGE/"ingestion"/f"{version}.json",result)
    write_json(COLLEGE/"ingestion_manifest.json",result)
    return result


class Retriever:
    def __init__(self, manifest: dict | None = None, *, as_of: str | None = None):
        historical = manifest is not None
        self.manifest = manifest or read_json(COLLEGE/"ingestion_manifest.json")
        if not self.manifest:
            raise PrerequisiteError("ChromaDB has no validated, verified campus index yet.")
        if not historical:
            corpus = read_json(COLLEGE/"manifest.json")
            if not corpus or corpus["version"] != self.manifest["corpus_version"]:
                raise PrerequisiteError("The FAQ corpus changed. Re-ingest before using campus chat so deleted or updated policies are not served.")
        self.settings = self.manifest["configuration"]
        self.as_of = datetime.fromisoformat(as_of) if as_of else datetime.now(timezone.utc)
        self.collection = _client().get_collection(self.manifest["collection"],embedding_function=None)
        if self.collection.count() != self.manifest["chunks"]:
            raise PrerequisiteError("Chroma collection count differs from the sealed ingestion manifest.")
        stored_metadata = self.collection.metadata or {}
        if any(stored_metadata.get(key) != self.settings[key] for key in ["embedding_model","embedding_revision"]):
            raise PrerequisiteError("Chroma embedding metadata differs from the sealed configuration.")
        contents = self.collection.get(include=["documents","metadatas"])
        fingerprint = digest(sorted(zip(contents["ids"],contents["documents"],contents["metadatas"]),key=lambda item:item[0]))
        if fingerprint != self.manifest["content_fingerprint"]:
            raise PrerequisiteError("Chroma document contents differ from the sealed ingestion manifest.")
        self.embedder = Embedder(self.settings["embedding_model"],self.settings["embedding_revision"],self.settings["device"])

    def query(self, question: str, *, language: str | None = None, category: str | None = None):
        start = time.perf_counter()
        filters = [{"verification_status":{"$in":accepted_verification(self.settings)}}]
        # By default search all languages: cross-language retrieval is an explicit experiment condition.
        if language:
            filters.append({"language":{"$eq":language}})
        if category:
            filters.append({"category":{"$eq":category}})
        where = {"$and":filters} if len(filters)>1 else filters[0]
        count = self.collection.count()
        if not count:
            return [], time.perf_counter()-start
        raw = self.collection.query(query_embeddings=self.embedder.encode([question],query=True),
                            n_results=min(count,self.settings["top_k"]*4),where=where,include=["metadatas","distances","documents"])
        cutoff = self.as_of-timedelta(days=self.settings["max_source_age_days"])
        hits, seen = [], set()
        for document_id, metadata, distance in zip(raw["ids"][0],raw["metadatas"][0],raw["distances"][0]):
            if distance > self.settings["max_cosine_distance"]:
                continue
            if datetime.fromisoformat(metadata["verified_at"]) < cutoff:
                continue
            if metadata.get("effective_date") and metadata["effective_date"] > self.as_of.date().isoformat():
                continue
            # Rank distinct documents, preventing multiple chunks from filling every retrieval slot.
            if metadata["source_document_id"] in seen:
                continue
            seen.add(metadata["source_document_id"])
            hits.append({**metadata,"chunk_id":document_id,"cosine_distance":float(distance)})
            if len(hits) >= self.settings["top_k"]:
                break
        return hits, time.perf_counter()-start

    def context(self, hits):
        parts, used = [], []
        for hit in hits:
            part = f"[S{len(used)+1}] {hit['source_title']}\n{hit['canonical_question']}\n{hit['answer']}"
            if hit.get('evidence_quote'):
                part += '\nOfficial source excerpt: '+hit['evidence_quote']
            if len("\n\n".join(parts+[part])) > self.settings["max_context_characters"]:
                break
            parts.append(part)
            used.append(hit)
        return "\n\n".join(parts),used


def evaluate_embeddings(path, *, select: bool = False):
    """Use source-reviewed validation labels with disclosed reviewer provenance, never test questions."""
    require_benchmark_complete()
    queries = read_jsonl(path)
    settings = config("retrieval")
    manifest = read_json(COLLEGE/"manifest.json")
    if not manifest:
        raise PrerequisiteError("Import verified FAQs before embedding evaluation")
    records = [validate_faq(r) for r in read_jsonl(COLLEGE/"versions"/manifest["version"]/"faq.jsonl")
               if r["verification_status"] in accepted_verification(settings)]
    if not records:
        raise ValueError("No verified FAQ records")
    if {r.get("language") for r in queries} != {"en","hi","ta"}:
        raise ValueError("Embedding validation requires reviewed queries in all three languages")
    from backend.datasets import canonical
    held = read_json(COLLEGE/"test_manifest.json")
    held_questions = set()
    if held:
        held_questions = {canonical(r["question"]) for r in read_jsonl(COLLEGE/"test_versions"/held["version"]/"test.jsonl")}
    document_ids = {r["source_document_id"] for r in records}
    for query in queries:
        if query.get("split") != "validation" or not query.get("reviewer") or not query.get("relevant_document_ids"):
            raise ValueError("Every retrieval validation query requires a reviewer, validation split, and relevance labels")
        if query.get('reviewer_kind') not in {'human','ai'}:
            raise ValueError('Retrieval labels must disclose human or AI review provenance')
        if query['reviewer_kind']=='ai' and query.get('human_review_status')!='pending':
            raise ValueError('AI-reviewed retrieval labels must retain pending human review')
        if canonical(query["question"]) in held_questions:
            raise ValueError("Retrieval validation question overlaps the held-out campus test set")
        if not set(query["relevant_document_ids"]).issubset(document_ids):
            raise ValueError("A relevance label refers to an unknown verified document")
    import numpy as np
    import httpx
    results = []
    for model_id in settings["candidate_models"]:
        pinned_revision = settings.get('candidate_revisions',{}).get(model_id)
        endpoint = f"https://huggingface.co/api/models/{model_id}" + (f"/revision/{pinned_revision}" if pinned_revision else '')
        response = httpx.get(endpoint,timeout=60)
        response.raise_for_status()
        revision = response.json()["sha"]
        if pinned_revision and revision != pinned_revision:
            raise PrerequisiteError('Embedding checkpoint metadata does not match the pinned candidate revision')
        embedder = Embedder(model_id,revision)
        document_embeddings = np.asarray(embedder.encode([r["canonical_question"]+"\n"+r["answer"] for r in records]))
        query_embeddings = np.asarray(embedder.encode([q["question"] for q in queries],query=True))
        by_language = {}
        for language in ["en","hi","ta"]:
            hits,mrr,distances = [],[],[]
            for index, query in enumerate(queries):
                if query["language"] != language:
                    continue
                similarity = document_embeddings @ query_embeddings[index]
                ranked,seen = [],set()
                for i in np.argsort(-similarity):
                    doc = records[int(i)]["source_document_id"]
                    if doc not in seen:
                        ranked.append((doc,float(1-similarity[i])))
                        seen.add(doc)
                ranks = [rank for rank,(doc,_) in enumerate(ranked[:settings["top_k"]],start=1) if doc in query["relevant_document_ids"]]
                hits.append(float(bool(ranks)))
                mrr.append(1/min(ranks) if ranks else 0)
                distances += [distance for doc,distance in ranked[:settings["top_k"]] if doc in query["relevant_document_ids"]]
            by_language[language] = {"queries":len(hits),"recall_at_k":100*sum(hits)/len(hits),"mrr":sum(mrr)/len(mrr),
                                     "relevant_hit_distances":distances}
        results.append({"model_id":model_id,"revision":revision,"languages":by_language,
                        "selection_score":min(v["mrr"] for v in by_language.values())})
        del embedder
    result = {"created_at":utcnow(),"corpus_version":manifest["version"],"query_fingerprint":digest(queries),
              "split":"validation","candidates":results,"selection_policy":"maximize worst-language MRR",
              'query_reviewer_kinds':dict(Counter(q['reviewer_kind'] for q in queries))}
    if select:
        best = max(results,key=lambda r:r["selection_score"])
        distances = [v for language in best["languages"].values() for v in language["relevant_hit_distances"]]
        if not distances or any(v["mrr"] == 0 for v in best["languages"].values()):
            raise PrerequisiteError("No candidate retrieved relevant documents in every language")
        from backend.evaluation.statistics import percentile
        settings.update(embedding_model=best["model_id"],embedding_revision=best["revision"],embedding_status="validated",
                        max_cosine_distance=percentile(distances,.95),validation_query_fingerprint=digest(queries))
        import yaml
        (ROOT/"config"/"retrieval.yaml").write_text(yaml.safe_dump(settings,sort_keys=False),encoding="utf-8")
        result["selected"] = settings
    write_json(COLLEGE/"embedding_evaluation"/f"{digest(result)[:16]}.json",result,exclusive=True)
    return result
