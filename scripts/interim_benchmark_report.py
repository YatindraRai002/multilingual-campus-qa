"""Score only fully paired language populations, without changing experiment records."""
from __future__ import annotations

import argparse
import json
import sqlite3
import uuid

from backend.evaluation.evaluation_runner import evaluate_predictions
from backend.reporting import metric_text
from backend.settings import ROOT, digest, read_json, utcnow, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("study_id")
    args = parser.parse_args()
    state = read_json(ROOT / "results" / "studies" / args.study_id / "state.json")
    if not state:
        raise SystemExit("Study does not exist")
    run_ids = {key: state["run_ids"][f"benchmark_{key}"] for key in ("A", "B")}
    # mode=ro prevents this exporter from changing the active research database.
    connection = sqlite3.connect((ROOT / "data" / "research.sqlite3").as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        runs = {}
        for key, run_id in run_ids.items():
            record = connection.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
            if not record:
                raise SystemExit(f"Missing benchmark {key}")
            runs[key] = dict(record)
            runs[key]["configuration"] = json.loads(record["configuration"])
        a, b = runs["A"], runs["B"]
        common_fields = ("model_id", "model_revision", "prompt_version", "generation", "max_input_tokens",
                         "seed", "context_condition", "inference_execution", "model_execution", "test_ids")
        matched = {field: a["configuration"].get(field) == b["configuration"].get(field)
                   for field in common_fields}
        matched.update(dataset_version=a["dataset_version"] == b["dataset_version"],
                       evaluation_fingerprint=a["evaluation_fingerprint"] == b["evaluation_fingerprint"])
        if not all(matched.values()) or a["status"] != "completed":
            raise SystemExit("A complete baseline and identical frozen evaluation settings are required")
        result = {"kind": "interim_completed_language_populations", "created_at": utcnow(),
                  "study_id": args.study_id, "run_ids": run_ids, "full_study_complete": False,
                  "not_for_model_selection": True, "database_access": "read_only",
                  "definitions_version": "qa-metrics-v3-all-retrieval-queries",
                  "metric_registry_modified": False, "matched_settings": matched,
                  "dataset_version": a["dataset_version"],
                  "evaluation_fingerprint": a["evaluation_fingerprint"],
                  "configuration_sha256": {key: digest(run["configuration"]) for key, run in runs.items()},
                  "run_progress_at_export": {key: {field: run[field] for field in ("status", "completed", "total")}
                                             for key, run in runs.items()}, "languages": {}}
        lines = ["# Interim benchmark comparison", "", f"Exported: {result['created_at']}.", "",
                 "**The full experiment is still incomplete.** This read-only export scores only language populations "
                 "whose full question sets have successful paired A/B outputs. Incomplete populations remain pending. "
                 "No model is run, no experiment metrics are overwritten, and these test results are not used for selection.", "",
                 f"Baseline A: `{run_ids['A']}`. Trained B: `{run_ids['B']}`. "
                 f"Dataset: `{a['dataset_version']}`. Model: Qwen2.5-1.5B-Instruct (user-approved local amendment).", "",
                 "English SQuAD and Hindi/Tamil IndicQA are separate populations. EM and F1 measure reference overlap; "
                 "human factuality metrics require actual human response annotations. Brackets show 95% bootstrap "
                 "intervals; responses sharing a source document can be correlated.", "",
                 "| Population | Language | Paired count | A EM | B EM | A F1 | B F1 |",
                 "|---|---|---:|---:|---:|---:|---:|"]
        for language in ("en", "hi", "ta"):
            records = {}
            for key, run_id in run_ids.items():
                saved = connection.execute(
                    "SELECT p.payload,a.payload AS review FROM predictions p LEFT JOIN annotations a "
                    "ON a.annotation_id=(SELECT MAX(a2.annotation_id) FROM annotations a2 "
                    "WHERE a2.prediction_id=p.prediction_id) WHERE p.run_id=? AND p.language=? ORDER BY p.rowid",
                    (run_id, language)).fetchall()
                records[key] = [{**json.loads(row["payload"]),
                                 "annotation": json.loads(row["review"]) if row["review"] else None} for row in saved]
            ids = {key: {row["question_id"] for row in rows} for key, rows in records.items()}
            complete = bool(ids["A"]) and ids["A"] == ids["B"] and all(
                row.get("evaluation_status") == "completed" for rows in records.values() for row in rows)
            group = {"status": "scored" if complete else "pending", "expected_count": len(ids["A"]),
                     "saved_count": {key: len(rows) for key, rows in records.items()},
                     "successful_count": {key: sum(row.get("evaluation_status") == "completed" for row in rows)
                                          for key, rows in records.items()},
                     "question_ids_sha256": {key: digest(sorted(value)) for key, value in ids.items()}}
            if complete:
                group["metrics"] = {key: evaluate_predictions(rows) for key, rows in records.items()}
                for source, population in group["metrics"]["A"]["populations"].items():
                    left = population["languages"][language]
                    right = group["metrics"]["B"]["populations"][source]["languages"][language]
                    lines.append(f"| {source} | {language} | {left['count']:,} | " + " | ".join(
                        metric_text(value) for value in (left["exact_match"], right["exact_match"],
                                                        left["f1"], right["f1"])) + " |")
            else:
                lines.append(f"| Pending | {language} | {len(ids['B']):,}/{len(ids['A']):,} saved | Pending | Pending | Pending | Pending |")
            result["languages"][language] = group
            print(json.dumps({"language": language, "status": group["status"], "saved_count": group["saved_count"]}), flush=True)
        lines += ["", "Timing observations were collected on a shared Windows desktop with changing RAM and GPU contention. "
                  "They do not isolate adapter overhead. Actual batch-completion latency and batch-deduplicated "
                  "throughput remain in the JSON export.", "",
                  "Both sides here use the same v3 scoring code in memory. The active worker remains uninterrupted "
                  "on its loaded v2 definitions; registered A/B metrics will both be replayed only after its full completion.", ""]
        folder = ROOT / "results" / "interim_benchmark" / str(uuid.uuid4())
        folder.mkdir(parents=True, exist_ok=False)
        write_json(folder / "metrics.json", result, exclusive=True)
        report = "\n".join(lines)
        (folder / "report.md").write_text(report, encoding="utf-8")
        (ROOT / "docs" / "INTERIM_BENCHMARK_REPORT.md").write_text(report, encoding="utf-8")
        print(json.dumps({"report": str(folder / "report.md"), "metrics": str(folder / "metrics.json")}), flush=True)
    finally:
        connection.close()


if __name__ == "__main__":
    main()
