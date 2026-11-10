"""Unscored live-API smoke check using existing validation questions, never test tuning."""
import json
import sqlite3
import time
from pathlib import Path

import httpx

from backend.settings import ROOT, read_json, read_jsonl, utcnow, write_json


def main():
    curation = read_json(ROOT / "data/college_faq/curation_manifest.json")
    queries = read_jsonl(Path(curation["validation_path"]))
    cases = [{"question": q["question"], "language": q["language"], "experiment": "D"}
             for q in queries if q["question_id"].startswith("ktr-vinayagar-temple:") and q["question_id"].endswith(":q1")]
    assert len(cases) == 3
    cases.append({"question": "At SRMIST Kattankulathur, what will my personal hostel room allocation be in 2040?",
                  "language": "en", "experiment": "D"})
    def counts():
        with sqlite3.connect((ROOT / "data/research.sqlite3").as_uri() + "?mode=ro", uri=True) as connection:
            return {table: connection.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]
                    for table in ("predictions", "annotations", "runs")}
    before = counts()
    result = {"started_at": utcnow(), "kind": "functional API verification, unscored",
              "question_source": "original retrieval validation; additional out-of-corpus request", "responses": []}
    for case in cases:
        started = time.perf_counter()
        response = httpx.post("http://127.0.0.1:8765/api/chat", json=case, timeout=240)
        response.raise_for_status()
        answer = response.json()
        assert answer["evaluation_status"] == "completed" and answer["research_scored"] is False
        assert answer["runtime_memory"]["policy"]["per_process_memory_fraction"] == .75
        assert answer["language"] == case["language"]
        if not answer["abstained"]:
            assert answer["citations"]
        for citation in answer["citations"]:
            assert any(citation["document_id"] == hit["source_document_id"] and citation["url"] == hit["source_url"]
                       for hit in answer["retrieved"])
        result["responses"].append({"request": case, "http_status": response.status_code,
                                     "client_seconds": time.perf_counter() - started, "response": answer})
        write_json(ROOT / "results/chat-smoke.json", result)
        print(json.dumps({"language": case["language"], "abstained": answer["abstained"],
                          "citations": len(answer["citations"]), "client_seconds": result["responses"][-1]["client_seconds"]}), flush=True)
    assert result["responses"][-1]["response"]["abstained"]
    assert any(r["response"]["citations"] for r in result["responses"][:3])
    result.update(ended_at=utcnow(), status="passed", research_store_counts_before=before,
                  research_store_counts_after=counts())
    assert result["research_store_counts_after"] == before
    write_json(ROOT / "results/chat-smoke.json", result)


if __name__ == "__main__":
    main()
