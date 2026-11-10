"""Reports are generated from persisted records, never from invented experiment outcomes."""
import json

from backend.settings import ROOT, digest, utcnow, write_json


def report_run(run):
    """Keep large question-ID lists in the immutable run export, not in prose reports."""
    configuration = dict(run["configuration"])
    if "test_ids" in configuration:
        identifiers = configuration.pop("test_ids")
        configuration["test_ids_summary"] = {"count": len(identifiers), "sha256": digest(identifiers),
            "location": f"/api/experiments/{run['run_id']}/export?format=json"}
    return {**run, "configuration": configuration}


def metric_text(metric):
    if not metric or metric.get("value") is None:
        return "Pending"
    suffix = "%" if metric.get("unit") == "percent" else ""
    result = f"{metric['value']:.2f}{suffix}"
    interval = metric.get("confidence_interval")
    if interval and interval.get("lower") is not None and interval.get("upper") is not None:
        result += f" [{interval['lower']:.2f}, {interval['upper']:.2f}]"
    return result


def write_evaluation_report(database):
    """Summarize only saved metrics; running predictions never imply completed results."""
    runs = database.runs(limit=10000)
    lines = ["# Evaluation report", "", f"Updated from persisted records: {utcnow()}.", "",
        "The active study uses the user-approved Qwen2.5-1.5B model on the local GPU. "
        "Original 7B settings are archived; 1.5B outcomes are not 7B outcomes.", "",
        "English SQuAD and Hindi/Tamil IndicQA are separate evaluation populations. "
        "Benchmark and campus tracks are reported separately. No cross-source aggregate accuracy is computed.", "",
        "Human factuality metrics remain **Pending** until all eligible responses in their scope have actual human annotations. "
        "EM and F1 measure reference overlap and must not be relabeled semantic accuracy.", ""]
    if not runs:
        lines += ["Evaluation not yet performed. No actual run records are available.", ""]
    for track in ("benchmark", "campus"):
        selected = [run for run in runs if run["track"] == track]
        lines += [f"## {track.title()} track", ""]
        if not selected:
            lines += ["No runs recorded for this track.", ""]
            continue
        for run in selected:
            lines += [f"### Experiment {run['experiment']} — {run['run_id']}", "",
                f"Status: **{run['status']}**. Persisted predictions: {run['completed']:,}/{run['total']:,}. "
                f"Dataset: `{run['dataset_version']}`. Model: `{run['configuration'].get('model_id', 'unrecorded')}`.", ""]
            if run.get("error"):
                lines += [f"Recorded error: {run['error']}", ""]
            recovery=run['configuration'].get('recovery')
            if recovery:
                lines += [f"Recovery provenance: {recovery['reused_count']:,} saved observations reused from "
                    f"`{recovery['source_run_id']}`; {recovery['pending_count']:,} questions require new generation. "
                    "The source run and measurements remain intact. Original measurement segments and allocator-policy "
                    "differences limit latency interpretation; reused observations are not new independent generations.", ""]
            if track == 'campus':
                policy = run['configuration'].get('reference_annotation_policy', {})
                lines += ["Reference review provenance: `"+json.dumps(policy, ensure_ascii=False, sort_keys=True)+"`. "
                    "AI-curated references support pilot overlap/retrieval results; independent human certification "
                    "and human response factuality scores require actual human review.", ""]
            metrics = database.metrics(run["run_id"])
            if not metrics:
                lines += ["No calculated metric snapshot exists yet.", ""]
                continue
            lines += ["Values in brackets are 95% bootstrap confidence intervals, when available.", "",
                "| Source population | Language | Completed | EM | F1 | Human accuracy | Hallucination incidence |",
                "|---|---|---:|---:|---:|---:|---:|"]
            for source, population in metrics.get("populations", {}).items():
                for language, group in population["languages"].items():
                    lines += [f"| {source} | {language} | {group['count']:,} | "
                        f"{metric_text(group.get('exact_match'))} | {metric_text(group.get('f1'))} | "
                        f"{metric_text(group.get('accuracy'))} | {metric_text(group.get('hallucination_incidence'))} |"]
            lines += ["", f"Full definitions, denominators, retrieval and latency measurements: "
                f"`/api/experiments/{run['run_id']}/metrics`. Immutable configuration and predictions: "
                f"`/api/experiments/{run['run_id']}/export?format=json`.", ""]
    lines += ["## Measurement conditions", "",
        "Benchmark requests use length-grouped batches of up to four. Each request's latency is its actual batch-completion "
        "window; it is not divided by batch size. Throughput counts each shared generation duration once. "
        "Model loading is measured separately. Campus requests run singly.", "",
        "Original test contexts are retained, with a 9,216-token input capacity. Prompts, deterministic generation settings, "
        "checkpoint revision, precision, input capacity and batching policy are frozen for paired A/B evaluation.", "",
        "Failed predictions remain in the run history and exclusion count. A partial or failed run does not establish the "
        "completed benchmark required for campus acquisition. Human metrics and one-sample confidence intervals are never imputed.", "",
        "Detailed metric definitions and limitations: [METRIC_DEFINITIONS.md](METRIC_DEFINITIONS.md).", ""]
    (ROOT/"docs").mkdir(parents=True, exist_ok=True)
    (ROOT/"docs"/"EVALUATION_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def write_run_report(database, run_id):
    run = database.run(run_id)
    metrics = database.metrics(run_id)
    payload = {"run":report_run(run),"metrics":metrics}
    title = ("LoRA evaluation" if run["experiment"] == "B" else "Original model baseline") if run["track"] == "benchmark" else "Campus evaluation"
    population_note = ("English SQuAD and Hindi/Tamil IndicQA are separate populations. " if run['track']=='benchmark' else
                       "Campus reference-review provenance is recorded in the run configuration. AI-curated references "
                       "support pilot overlap/retrieval scores and remain pending independent human certification. ")
    report = (f"# {title} report\n\nGenerated from the persisted experiment at {utcnow()}.\n\n"
              f"Run ID: {run_id}\n\nStatus: {run['status']}\n\nTrack: {run['track']}\n\n"
              f"Dataset version: {run['dataset_version']}\n\n"
              +population_note+"Null factuality metrics mean "
              "insufficient human annotations, not zero error or zero accuracy. Confidence intervals and metric denominators "
              "are included with the calculated results. Failed-record exclusions remain explicit.\n\n"
              "```json\n"+json.dumps(payload,ensure_ascii=False,indent=2)+"\n```\n")
    (ROOT/"docs").mkdir(parents=True, exist_ok=True)
    # Per-run reports retain history when another run or annotation is added later.
    folder = ROOT/"results"/"reports"/run_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder/"report.md").write_text(report, encoding="utf-8")
    if metrics:
        snapshot=folder/f"metrics-{digest(metrics)[:16]}.json"
        if not snapshot.exists():
            write_json(snapshot,metrics,exclusive=True)
    name = "LORA_EVALUATION_REPORT.md" if run["track"] == "benchmark" and run["experiment"] == "B" else "BASELINE_EVALUATION_REPORT.md" if run["track"] == "benchmark" else "CAMPUS_EVALUATION_REPORT.md"
    (ROOT/"docs"/name).write_text(report,encoding="utf-8")
    (ROOT/"docs"/"EXPERIMENT_STATUS.md").write_text(
        "# Experiment status\n\nUpdated: "+utcnow()+"\n\n```json\n"+
        json.dumps([{"run_id":r["run_id"],"track":r["track"],"experiment":r["experiment"],"status":r["status"],
                     "dataset_version":r["dataset_version"],"created_at":r["created_at"],"ended_at":r["ended_at"],
                     "completed_predictions":r["completed"],"metrics":database.metrics(r["run_id"])} for r in database.runs()],
                   ensure_ascii=False,indent=2)+"\n```\n",encoding="utf-8")
    write_evaluation_report(database)
