"""Check persisted retrieval in a fresh process using validation queries only."""
import json
from collections import defaultdict
from pathlib import Path

from backend.college import COLLEGE
from backend.retrieval import Retriever
from backend.settings import ROOT, read_json, read_jsonl, utcnow, write_json


def main():
    retriever = Retriever()
    queries = read_jsonl(Path(read_json(COLLEGE / "curation_manifest.json")["validation_path"]))
    scores, observations = defaultdict(list), []
    for row in queries:
        assert row["split"] == "validation"
        hits, seconds = retriever.query(row["question"])
        context, used = retriever.context(hits)
        ranks = [i for i, h in enumerate(hits, start=1) if h["source_document_id"] in row["relevant_document_ids"]]
        reciprocal = 1 / min(ranks) if ranks else 0
        scores[row["language"]].append(reciprocal)
        assert all(h["verification_status"] in {"source_verified", "human_verified"} for h in used)
        observations.append({"question_id": row["question_id"],
            "retrieved_document_ids": [h["source_document_id"] for h in hits],
            "context_document_ids": [h["source_document_id"] for h in used],
            "reciprocal_rank": reciprocal, "retrieval_seconds": seconds, "context_characters": len(context)})
    result = {"checked_at": utcnow(), "split": "validation only", "index_version": retriever.manifest["version"],
        "persistent_chunks": retriever.collection.count(), "configuration": retriever.settings,
        "languages": {language: {"queries": len(values), "mrr_after_calibrated_cutoff": sum(values) / len(values),
            "recall_at_k_percent": 100 * sum(v > 0 for v in values) / len(values)} for language, values in scores.items()},
        "observations": observations, "human_response_annotations_created": 0}
    assert set(scores) == {"en", "hi", "ta"} and all(v["mrr_after_calibrated_cutoff"] > 0 for v in result["languages"].values())
    assert result["persistent_chunks"] == retriever.manifest["chunks"]
    path = ROOT / "results" / "retrieval_validation" / f"{retriever.manifest['version']}.json"
    write_json(path, result, exclusive=True)
    write_json(COLLEGE / "retrieval_validation_manifest.json",
               {"index_version": retriever.manifest["version"], "path": path.relative_to(ROOT).as_posix()})
    print(json.dumps({k: v for k, v in result.items() if k not in {"observations", "configuration"}}, indent=2))


if __name__ == "__main__":
    main()
