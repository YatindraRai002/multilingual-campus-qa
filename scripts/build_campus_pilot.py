"""Materialize the explicitly AI-reviewed pilot and fact-disjoint validation/test labels."""
from __future__ import annotations

import json
import argparse
import uuid
from collections import Counter
from pathlib import Path

from backend.college import COLLEGE, require_benchmark_complete, validate_faq
from backend.datasets import canonical, identify_language
from backend.settings import ROOT, digest, read_json, read_jsonl, utcnow, write_json, write_jsonl


def campus_question(question, language):
    prefixes = {
        "en": "At SRMIST's Kattankulathur campus: ",
        "hi": "एसआरएमआईएसटी के कट्टनकुलथूर परिसर के बारे में: ",
        "ta": "எஸ்ஆர்எம் காட்டாங்குளத்தூர் வளாகம் குறித்து: ",
    }
    return prefixes[language] + question


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--facts",type=Path,default=COLLEGE/"curation"/"pilot_facts.json")
    parser.add_argument("--append-corpus")
    parser.add_argument("--validation",type=Path)
    arguments = parser.parse_args()
    require_benchmark_complete()
    curated = read_json(arguments.facts)
    assert curated["reviewer_kind"] == "ai" and curated["human_review_status"] == "pending"
    reviewed_at = utcnow()
    faqs, validation, test = [], [], []
    groups = {"validation": set(), "test": set()}
    if arguments.validation:
        validation = read_jsonl(arguments.validation)
        groups["validation"] = {document for row in validation for document in row["relevant_document_ids"]}
    if arguments.append_corpus:
        previous = read_jsonl(COLLEGE/"versions"/arguments.append_corpus/"faq.jsonl")
        assert not {row["source_document_id"] for row in previous} & {f["source_document_id"] for f in curated["facts"]}
        faqs.extend(validate_faq(row) for row in previous)
    for fact in curated["facts"]:
        meta = read_json(COLLEGE / "documents" / fact["source_document_id"] / "metadata.json")
        assert meta and meta["source_document_id"] == fact["source_document_id"]
        group = fact["fact_split"]
        assert group in groups
        groups[group].add(fact["source_document_id"])
        for language in ("en", "hi", "ta"):
            text = fact[language]
            record = {
                "faq_id": fact["id"], "canonical_question": text["question"],
                "language": language, "answer": text["answer"], "category": meta["category"],
                "source_url": meta["source_url"], "source_title": meta["source_title"],
                "source_document_id": meta["source_document_id"],
                "verification_status": "source_verified", "verified_at": reviewed_at,
                "verified_by": curated["reviewer"], "document_version": meta["document_version"],
                "effective_date": None, "campus": "Kattankulathur",
                "translation_status": "native" if language == "en" else "machine_translation_ai_reviewed",
                "reviewer_kind": "ai", "review_method": "official_snapshot_ai_review",
                "human_review_status": "pending", "review_notes": fact["review_notes"],
                "evidence_quote": fact["evidence_quote"],
            }
            faqs.append(validate_faq(record))
            for index, question in enumerate(text["queries"], start=1):
                question = campus_question(question, language)
                assert identify_language(question) == language, (fact["id"], language, question)
                assert canonical(question) != canonical(text["question"])
                row = {
                    "question_id": f"{fact['id']}:{language}:q{index}",
                    "fact_id": fact["id"], "language": language, "question": question,
                    "reference_answer": text["answer"],
                    "reference_answers": list(dict.fromkeys([text["answer"], *text["aliases"]])),
                    "answerable": True, "relevant_document_ids": [fact["source_document_id"]],
                    "split": group, "reviewer": curated["reviewer"], "reviewer_kind": "ai",
                    "review_method": "official_snapshot_ai_review", "reviewed_at": reviewed_at,
                    "human_review_status": "pending",
                }
                (validation if group == "validation" else test).append(row)
    assert not groups["validation"] & groups["test"], "Source documents overlap across query splits"
    for language, questions in curated["unanswerable_queries"].items():
        for index, question in enumerate(questions, start=1):
            question = campus_question(question, language)
            assert identify_language(question) == language
            test.append({
                "question_id": f"ktr-out-of-corpus:{language}:q{index}",
                "fact_id": f"out-of-corpus-{index}", "language": language, "question": question,
                "reference_answer": "", "reference_answers": [""], "answerable": False,
                "relevant_document_ids": [], "split": "test", "reviewer": curated["reviewer"],
                "reviewer_kind": "ai", "review_method": "official_snapshot_ai_review",
                "reviewed_at": reviewed_at, "human_review_status": "pending",
                "answerability_scope": "Not specified anywhere in the sealed FAQ corpus; future or personal allocation request.",
            })
    assert not {canonical(r["question"]) for r in validation} & {canonical(r["question"]) for r in test}
    assert len({r["question_id"] for r in validation + test}) == len(validation + test)
    folder = COLLEGE / "curation_versions" / str(uuid.uuid4())
    write_jsonl(folder / "faq.jsonl", faqs, exclusive=True)
    write_jsonl(folder / "retrieval_validation.jsonl", validation, exclusive=True)
    write_jsonl(folder / "campus_test.jsonl", test, exclusive=True)
    result = {
        "created_at": reviewed_at, "kind": "AI-curated official-source-backed pilot",
        "human_reference_review_complete": False, "reviewer": curated["reviewer"],
        "curation_sha256": digest(curated), "faq_records": len(faqs),
        "curation_path": arguments.facts.resolve().relative_to(ROOT).as_posix(),
        "parent_corpus_version": arguments.append_corpus,
        "faq_languages": dict(Counter(r["language"] for r in faqs)),
        "source_documents_used": len({row["source_document_id"] for row in faqs}),
        "knowledge_only_source_documents": sorted({row["source_document_id"] for row in faqs} - groups["validation"] - groups["test"]),
        "retrieval_validation_queries": len(validation), "campus_test_queries": len(test),
        "test_answerability": dict(Counter("answerable" if r["answerable"] else "unanswerable" for r in test)),
        "validation_source_documents": sorted(groups["validation"]),
        "test_source_documents": sorted(groups["test"]),
        "source_disjoint_query_splits": True,
        "query_context": "Every validation/test question explicitly names the Kattankulathur campus, identically for all four model conditions.",
        "negative_query_limitation": "Three clearly out-of-corpus future/personal requests per language; no general open-domain robustness claim.",
        "faq_path": str(folder / "faq.jsonl"),
        "validation_path": str(folder / "retrieval_validation.jsonl"),
        "test_path": str(folder / "campus_test.jsonl"),
    }
    write_json(folder / "review_manifest.json", result, exclusive=True)
    write_json(COLLEGE / "curation_manifest.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
