"""Write campus methodology reports from the actual sealed corpus and validation records."""
import json
from collections import Counter
from pathlib import Path

from backend.college import COLLEGE
from backend.settings import ROOT, digest, read_json, read_jsonl, utcnow


def main():
    corpus = read_json(COLLEGE / "manifest.json")
    test_manifest = read_json(COLLEGE / "test_manifest.json")
    index = read_json(COLLEGE / "ingestion_manifest.json")
    curation = read_json(COLLEGE / "curation_manifest.json")
    selection = read_json(ROOT / "results" / "campus-embedding-selection.json")
    validation_pointer = read_json(COLLEGE / "retrieval_validation_manifest.json")
    checked = read_json(ROOT / validation_pointer["path"]) if validation_pointer else read_json(ROOT / "results" / "campus-persistent-retrieval-validation.json")
    faqs = read_jsonl(COLLEGE / "versions" / corpus["version"] / "faq.jsonl")
    tests = read_jsonl(COLLEGE / "test_versions" / test_manifest["version"] / "test.jsonl")
    validation = read_jsonl(Path(curation["validation_path"]))
    assert digest(read_json(ROOT / curation.get("curation_path", "data/college_faq/curation/pilot_facts.json"))) == curation["curation_sha256"]
    assert corpus["version"] == test_manifest["corpus_version"] == index["corpus_version"]
    assert index["version"] == checked["index_version"]
    validation_sources = set(curation["validation_source_documents"])
    test_sources = set(curation["test_source_documents"])
    assert not validation_sources & test_sources
    updated = utcnow()
    english = [r for r in faqs if r["language"] == "en"]
    source_count = len({r["source_document_id"] for r in faqs})
    captured_pages = len({read_json(p)["source_url"] for p in (COLLEGE / "documents").glob("*/metadata.json")})
    lines = ["# College FAQ dataset report", "", f"Generated from sealed records: {updated}.", "",
        "**This is an AI-curated, official-source-backed Kattankulathur pilot. Independent human source, "
        "translation and reference certification remains pending.** Source review does not create human response annotations.", "",
        f"Corpus version: `{corpus['version']}`. Records: **{corpus['count']}** from **{source_count}** official source pages. "
        f"Eligible source-reviewed records: {corpus['eligible_verified_count']}; human-verified records: {corpus['human_verified_count']}.", "",
        "| Language | FAQ records | Retrieval validation queries | Campus test queries | Test answerable / unanswerable |",
        "|---|---:|---:|---:|---:|"]
    for language in ("en", "hi", "ta"):
        values = [r for r in tests if r["language"] == language]
        lines.append(f"| {language} | {sum(r['language']==language for r in faqs)} | "
                     f"{sum(r['language']==language for r in validation)} | {len(values)} | "
                     f"{sum(r['answerable'] for r in values)} / {sum(not r['answerable'] for r in values)} |")
    lines += ["", "## Source scope and review", "",
        f"{captured_pages} public official university/department pages were captured after the full benchmark A, "
        f"training and B workflow completed. {source_count} pages supply this corpus. The initial discovery registry is preserved. "
        "Each capture keeps original HTML, normalized text, a SHA-256 document version, URL and capture timestamp. "
        "FAQ validation checks the exact evidence quotation against that archived text.", "",
        "Campus scope was checked against the Kattankulathur main-site hierarchy, department addresses and KTR hostel references. "
        "Additional official search results corroborated the aquatic complex, temple and astronomy-club identities. "
        "The facts are representations of official published pages, rather than an on-site audit.", "",
        "English questions/answers were authored from those facts. Hindi and Tamil versions were checked by the named AI "
        "reviewer for entity identity, scope and meaning, and use `machine_translation_ai_reviewed`. All records retain "
        "`reviewer_kind: ai`, `human_review_status: pending` and `verification_status: source_verified`. "
        "They are not human-verified records.", "",
        "No current fees, fines, admissions deadlines, changing headcounts, personal student records or dynamic zero-valued "
        "homepage counters are included in the FAQ corpus. Some source pages contain historical information; a recent capture "
        "does not independently establish that every policy on the website is current. Student contact details are not curated "
        "or indexed. Raw page archives remain local and are excluded from the source-only distribution.", "",
        "| Topic ID | Query split | Official source | Document version prefix |",
        "|---|---|---|---|"]
    for row in english:
        group = ("validation" if row["source_document_id"] in validation_sources else
                 "test" if row["source_document_id"] in test_sources else "knowledge only (primary-study fact)")
        lines.append(f"| {row['faq_id']} | {group} | [{row['source_title']}]({row['source_url']}) | "
                     f"`{row['document_version'][:16]}` |")
    lines += ["", "## Query design and sealing", "",
        f"The **{len(validation)}** retrieval-validation queries cover {len(validation_sources)} source documents. "
        f"The **{len(tests)}** held-out campus questions cover {len(test_sources)} different source documents plus explicitly "
        "out-of-corpus future/personal requests. Validation and test source groups are disjoint. "
        "Every question explicitly identifies the Kattankulathur campus, identically for all four conditions.", "",
        "All FAQ facts are intentionally present in the knowledge index. The split holds out retrieval-query facts from "
        "embedding selection; it is evaluation over a fixed knowledge corpus, not a claim about retrieval from unseen corpora. "
        "Each answerable fact has two question variants per language. Those variants are correlated and do not establish "
        "independent evidence of broad generalization.", "",
        f"Test version: `{test_manifest['version']}`; checksum: `{test_manifest['test_checksum']}`. "
        f"The test was sealed at {test_manifest['created_at']}. "
        f"The embedding and threshold choices were fixed on primary validation at {selection['created_at']}. "
        "Reference aliases and answerability labels were fixed before inference on this test version. "
        "Three negatives per language ask about unspecified future fees, future examination dates or personal room allocation; "
        "these are clear out-of-corpus cases, not a comprehensive robustness test.", "",
        "The corpus, retrieval labels and references disclose AI curation. EM, F1 and retrieval scores are conditional on "
        "those annotations. Human accuracy, hallucination incidence, unsupported-claim rate and the corresponding accuracy "
        "gap remain pending until actual human response reviews exist.", "",
        "## Storage and training separation", "",
        f"Versioned FAQ data: `data/college_faq/versions/{corpus['version']}/faq.jsonl`. "
        f"Versioned test: `data/college_faq/test_versions/{test_manifest['version']}/test.jsonl`. "
        "The curation source and review manifest preserve translations, aliases, source assignments and provenance. "
        "The approved LoRA adapter was trained before campus collection, exclusively on benchmark training data; no campus FAQ "
        "was added to supervised fine-tuning.", "",
        "University pages retain their own copyright. Facts are paraphrased, brief evidence excerpts are attributed, and "
        "public availability is not represented as an open-content licence.", ""]
    if curation.get("parent_corpus_version"):
        lines += ["## Follow-up provenance", "",
            "This corpus retains the original 39 FAQs and adds 18 reviewed language records from six new department pages. "
            "The primary study's 63-question test and all four results remain intact. Its strict citation policy rejected "
            "uncited model answers. A separately documented engineering extension attributes only complete verbatim source "
            "matches; the new 45-question test uses source documents absent from the entire original FAQ corpus. "
            "Its questions, references and source assignments were sealed before follow-up inference. "
            "Embedding model, threshold, training, model prompts and generation settings were retained. "
            "Compare arms within a test version; primary/follow-up percentages are not a paired causal estimate. "
            "See [CITATION_POLICY_AMENDMENT.md](CITATION_POLICY_AMENDMENT.md).", ""]
    report = "\n".join(lines)
    (ROOT / "docs" / "COLLEGE_FAQ_DATASET_REPORT.md").write_text(report, encoding="utf-8")
    report_folder = ROOT / "results" / "campus_corpus" / corpus["version"]
    report_folder.mkdir(parents=True, exist_ok=True)
    if not (report_folder / "report.md").exists():
        (report_folder / "report.md").write_text(report, encoding="utf-8")

    settings = index["configuration"]
    rag = ["# RAG implementation report", "", f"Generated from persisted validation and index records: {updated}.", "",
        f"Selected embedding: **{settings['embedding_model']}**, revision `{settings['embedding_revision']}`, on CPU. "
        "Both pinned candidates were actually evaluated before selection. The rule maximizes the worst-language MRR "
        "on primary validation queries, with document-level deduplication. These choices were carried over unchanged "
        "when the follow-up added source documents.", "",
        "| Candidate | English MRR | Hindi MRR | Tamil MRR | Worst-language MRR |",
        "|---|---:|---:|---:|---:|"]
    for candidate in selection["candidates"]:
        languages = candidate["languages"]
        rag.append(f"| {candidate['model_id']} | {languages['en']['mrr']:.4f} | {languages['hi']['mrr']:.4f} | "
                   f"{languages['ta']['mrr']:.4f} | {candidate['selection_score']:.4f} |")
    rag += ["", "These are rankings before the distance gate, with eight positive validation queries per language. "
        "The gate is the predeclared 95th percentile of positive relevant-hit distances, pooled across languages. "
        "It has no negative-query calibration and is not a calibrated probability of factual correctness.", "",
        f"Selected maximum cosine distance: **{settings['max_cosine_distance']:.9f}**. "
        "A separate fresh-process check reopened the real persistent index, verified its content checksum and applied this gate:", "",
        "| Validation language | Recall@4 after gate | MRR after gate |",
        "|---|---:|---:|"]
    for language, group in checked["languages"].items():
        rag.append(f"| {language} | {group['recall_at_k_percent']:.2f}% | {group['mrr_after_calibrated_cutoff']:.4f} |")
    rag += ["", "## Actual ChromaDB index", "",
        f"Collection: `{index['collection']}`. Index version: `{index['version']}`. "
        f"Corpus: `{index['corpus_version']}`. Actual FAQ records: **{index['faq_records']}**; chunks: **{index['chunks']}**. "
        "The short pilot answers each fit one chunk. Persistent storage is `data/chroma/`.", "",
        f"Chunk budget: {settings['chunk_characters']} characters with {settings['chunk_overlap']} overlap. "
        "Combining marks remain attached at chunk boundaries. Embeddings are normalized; multilingual E5 uses its "
        "query/passage prefixes. Ranking searches all three languages, then deduplicates by official source document. "
        "This cross-language condition matches candidate validation.", "",
        f"Retrieval uses top {settings['top_k']} distinct source documents, a {settings['max_source_age_days']}-day review-freshness "
        f"filter, effective-date checks and an aggregate {settings['max_context_characters']}-character context budget. "
        "Only configured source-verified or human-verified records are eligible. All current records are explicitly AI "
        "source-reviewed and pending human review; the configuration can require human verification for a later index.", "",
        "## Generation and citations", "",
        "Campus A/B receive no retrieved context. C/D use this same frozen collection and retrieval settings. "
        "Context construction returns the exact subset of hits actually supplied to the model. Citations are resolved "
        "only against those source labels. The original model-emitted-v1 policy abstains for missing citations. "
        "The current model-or-verbatim-v2 policy additionally attaches a citation when the entire normalized response equals "
        "a complete FAQ answer or evidence quote from exactly one supplied source document. Case, repeated whitespace and "
        "terminal periods/dandas are ignored; internal punctuation, signs and Indic marks remain. No aliases, substrings, "
        "similarity scores or evaluation references enter that decision. Empty evidence, invalid labels, ambiguous matches "
        "and unsupported text still cause abstention. Raw model text and citation origin remain recorded. "
        "This is provenance formatting, not semantic claim certification.", "",
        "Each run records its model/adapter revision, test and index versions, actual retrieved sources, context, raw/final answer "
        "and monotonic retrieval/generation/total durations. Model and embedder initialization occur outside normal request "
        "timers. C/D comparison checks the actual per-question context strings, not just the collection name.", "",
        "## Metric scope and limitations", "",
        "Definitions `qa-metrics-v3-all-retrieval-queries` use every retrieval query in Recall@K and MRR. Explicit empty "
        "relevance lists contribute zero; missing labels leave the scope pending. "
        f"With {sum(r['answerable'] for r in tests)} answerable and {sum(not r['answerable'] for r in tests)} "
        f"unanswerable questions, the maximum all-query Recall@4 is "
        f"{100*sum(r['answerable'] for r in tests)/len(tests):.2f}% and maximum MRR is "
        f"{sum(r['answerable'] for r in tests)/len(tests):.4f}, even with perfect positive retrieval.", "",
        "The index can be rebuilt into a new version after reviewed updates/deletions. Chat refuses a stale index after the "
        "active corpus changes. Historical experiment indexes and records remain available. Stable chunk IDs prevent duplicate "
        "upserts. Freshness is based on attributed review time, which is not proof of an updated university publication date.", "",
        "The local 3 GB CUDA allocator policy applies identically to all four campus workers. A real trained-adapter stress "
        "check passed six varying/repeated shapes, including 9,216-token inputs with 192 forced output tokens, without clearing "
        "the cache between cases. This is allocator-capacity evidence, not a promise of dedicated-memory residency or isolation "
        "from other desktop applications.", "",
        "Actual model results are reported separately in [EVALUATION_REPORT.md](EVALUATION_REPORT.md). Human source/reference "
        "certification and human response factuality metrics remain pending. The small pilot, correlated question variants and "
        "simple negatives do not establish a production-ready campus policy authority.", ""]
    (ROOT / "docs" / "RAG_IMPLEMENTATION_REPORT.md").write_text("\n".join(rag), encoding="utf-8")
    print(json.dumps({"corpus_report": "docs/COLLEGE_FAQ_DATASET_REPORT.md",
                      "rag_report": "docs/RAG_IMPLEMENTATION_REPORT.md",
                      "corpus_records": len(faqs), "validation_queries": len(validation), "test_queries": len(tests)}))


if __name__ == "__main__":
    main()
