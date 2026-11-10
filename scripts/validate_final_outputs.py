"""Read-only audit of the completed local experiment and its frozen follow-up."""
import hashlib
import json
import sqlite3
from collections import Counter

from backend.settings import ROOT, config, digest, read_json, read_jsonl, utcnow, write_json
from backend.source_attribution import verbatim_source_label

PRIMARY = "0f3dfb3d-298f-47c1-a020-4be01eb4bcec"
FOLLOWUP = "9ed4cb93-716a-4953-b588-606e6d999d88"
ADAPTER = "3e2e65278413ed82c219d9b0c60c88cea0c1bfc22243f6af9772d13df1b2798d"


def main():
    connection = sqlite3.connect((ROOT / "data/research.sqlite3").as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    states = {name: read_json(ROOT / "results/studies" / sid / "state.json")
              for name, sid in (("primary", PRIMARY), ("followup", FOLLOWUP))}
    assert all(state["status"] == "model_experiments_completed" for state in states.values())
    cohorts = {
        "benchmark": {e: states["primary"]["run_ids"][f"benchmark_{e}"] for e in "AB"},
        "primary_campus": {e: states["primary"]["run_ids"][f"campus_{e}"] for e in "ABCD"},
        "followup_campus": {e: states["followup"]["run_ids"][f"campus_{e}"] for e in "ABCD"},
    }
    expected_sizes = {"benchmark": 13921, "primary_campus": 63, "followup_campus": 45}
    audit = {"checked_at": utcnow(), "database_access": "read_only", "status": "passed",
             "human_annotations": connection.execute("SELECT COUNT(*) FROM annotations").fetchone()[0],
             "cohorts": {}, "adapter_revision": ADAPTER}
    for cohort, runs in cohorts.items():
        configurations, signatures, contexts, records = {}, {}, {}, {}
        for experiment, run_id in runs.items():
            run = dict(connection.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone())
            cfg = json.loads(run.pop("configuration"))
            predictions = [json.loads(row[0]) for row in connection.execute(
                "SELECT payload FROM predictions WHERE run_id=? ORDER BY question_id", (run_id,))]
            metric_row = connection.execute(
                "SELECT payload,computed_at FROM metrics WHERE run_id=? ORDER BY metric_id DESC LIMIT 1", (run_id,)).fetchone()
            metrics = {**json.loads(metric_row[0]), "computed_at": metric_row[1]}
            assert run["status"] == "completed" and run["error"] is None
            assert run["completed"] == run["total"] == len(predictions) == expected_sizes[cohort]
            assert len({p["question_id"] for p in predictions}) == len(predictions)
            assert all(p["evaluation_status"] == "completed" for p in predictions)
            assert metrics["definitions_version"] == "qa-metrics-v3-all-retrieval-queries"
            assert cfg["model_id"] == "Qwen/Qwen2.5-1.5B-Instruct"
            assert cfg["model_revision"] == "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"
            assert all(p["adapter_revision"] == (ADAPTER if experiment in "BD" else None) for p in predictions)
            assert all(p["generation_settings"] == cfg["generation"] for p in predictions)
            assert all(p["prompt_version"] == cfg["prompt_version"] for p in predictions)
            signatures[experiment] = digest([{k: p.get(k) for k in (
                "question_id", "language", "question", "reference_answer", "reference_answers",
                "answerable", "relevant_document_ids", "source_dataset")} for p in predictions])
            contexts[experiment] = digest([(p["question_id"], p["context"]) for p in predictions])
            configurations[experiment] = cfg
            folder = ROOT / "results" / ({"A": "baseline", "B": "lora"}[experiment]
                      if cohort == "benchmark" else "campus") / run_id
            memory = read_json(folder / "memory.json")
            loading = read_json(folder / "loading.json")
            if cohort != "benchmark":
                budget = loading["runtime_memory"]["allocator_budget_bytes"]
                assert cfg["runtime_memory_policy"]["per_process_memory_fraction"] == .75
                assert memory["peak_reserved_bytes"] <= budget
            citation_counts = Counter()
            for p in predictions:
                if experiment not in "CD":
                    continue
                used_ids = p.get("context_document_ids", [])
                by_id = {h["source_document_id"]: h for h in p["retrieved"]}
                used = [by_id[doc] for doc in used_ids]
                for citation in p["citations"]:
                    assert citation["document_id"] in used_ids
                    assert citation["url"] == by_id[citation["document_id"]]["source_url"]
                    assert p["generated_answer"].find("[" + citation["label"] + "]") >= 0
                if not p["abstained"]:
                    assert p["citations"]
                    citation_counts[p.get("citation_origin", "model_emitted")] += 1
                if p.get("citation_origin") == "verbatim_source_attribution":
                    label = verbatim_source_label(p["raw_generated_answer"], used)
                    assert label is not None and "[" + label + "]" in p["generated_answer"]
            populations = {source: {lang: values for lang, values in pop["languages"].items()}
                           for source, pop in metrics["populations"].items()}
            assert all(v["accuracy"]["value"] is None and v["hallucination_incidence"]["value"] is None
                       for languages in populations.values() for v in languages.values())
            records[experiment] = {"run": run, "populations": populations,
                "abstentions": sum(p["abstained"] for p in predictions),
                "abstention_reasons": dict(Counter(p.get("abstention_reason", "model_abstention")
                    for p in predictions if p["abstained"])),
                "citation_origins": dict(citation_counts), "memory": memory, "loading": loading,
                "metric_sha256": digest(metrics),
                "predictions_sha256": hashlib.sha256((folder / "predictions.jsonl").read_bytes()).hexdigest()}
        assert len(set(signatures.values())) == 1
        for field in ("model_revision", "prompt_version", "generation", "max_input_tokens", "seed",
                      "inference_execution", "model_execution"):
            assert len({digest(c.get(field)) for c in configurations.values()}) == 1, field
        if cohort == "benchmark":
            assert contexts["A"] == contexts["B"]
        else:
            assert contexts["C"] == contexts["D"]
            assert digest(configurations["C"]["ingestion"]) == digest(configurations["D"]["ingestion"])
            assert len({digest(c["runtime_memory_policy"]) for c in configurations.values()}) == 1
        audit["cohorts"][cohort] = {"matched_population": True, "population_sha256": next(iter(signatures.values())),
            "matched_rag_evidence": cohort != "benchmark", "runs": records}
    protocol = read_json(ROOT / "results/citation-policy-followup/sealed_protocol.json")
    execution = read_json(ROOT / "results/citation-policy-followup/execution.json")
    assert hashlib.sha256((ROOT / "results/citation-policy-followup/sealed_protocol.json").read_bytes()).hexdigest() == execution["protocol_sha256"]
    assert digest(config("model_config")) == protocol["model_configuration_sha256"]
    for source, checksum in protocol["source_sha256"].items():
        assert hashlib.sha256((ROOT / source).read_bytes()).hexdigest() == checksum, source
    for e, checksum in protocol["primary_metric_sha256"].items():
        assert audit["cohorts"]["primary_campus"]["runs"][e]["metric_sha256"] == checksum
    college = ROOT / "data/college_faq"
    old_faq = read_jsonl(college / "versions/652d19bfd9f0b4cc/faq.jsonl")
    new_faq = read_jsonl(college / "versions/b07405a784a7045c/faq.jsonl")
    new_by_id = {(r["faq_id"], r["language"]): r for r in new_faq}
    assert all(new_by_id[(r["faq_id"], r["language"])] == r for r in old_faq)
    old_documents = {r["source_document_id"] for r in old_faq}
    fresh_test = read_jsonl(college / "test_versions/29ed6c44573105ff/test.jsonl")
    # Campus sealing stores a canonical JSON digest, independent of JSONL newlines.
    assert digest(fresh_test) == protocol["followup_test_checksum"]
    test_documents = {doc for r in fresh_test for doc in r["relevant_document_ids"]}
    assert len(test_documents) == 6 and not test_documents & old_documents
    old_validation = read_jsonl(college / "curation_versions/068baf91-6d5a-48be-bd23-0cbc54f63bd2/retrieval_validation.jsonl")
    new_validation = read_jsonl(college / "curation_versions/406c2868-079d-4927-8d2b-4b53326eb3bf/retrieval_validation.jsonl")
    assert old_validation == new_validation
    assert digest(new_validation) == protocol["validation_query_fingerprint"]
    for version in ("d7d31923b9ecac7f", "6e044fab88609b53"):
        settings = read_json(college / "ingestion" / f"{version}.json")["configuration"]
        settings.pop("citation_policy", None)
        if version == "d7d31923b9ecac7f":
            original_settings = settings
        else:
            assert settings == original_settings
    assert all(audit["cohorts"]["followup_campus"]["runs"][e]["citation_origins"] for e in "CD")
    audit["frozen_protocol_unchanged"] = True
    audit["primary_metric_snapshots_unchanged"] = True
    audit["original_corpus_records_preserved"] = True
    audit["fresh_test_source_disjoint"] = True
    audit["original_validation_and_retrieval_settings_preserved"] = True
    audit["prediction_count"] = sum(r["run"]["completed"] for c in audit["cohorts"].values() for r in c["runs"].values())
    audit["human_reference_certification"] = "pending"
    write_json(ROOT / "results/final-model-validation.json", audit)
    connection.close()
    print(json.dumps({k: v for k, v in audit.items() if k != "cohorts"}, indent=2))


if __name__ == "__main__":
    main()
