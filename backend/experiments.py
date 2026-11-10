from __future__ import annotations

import logging
import os
import subprocess
import sys
from contextlib import ExitStack
from pathlib import Path

from filelock import FileLock, Timeout

from backend.college import COLLEGE
from backend.datasets import current_manifest, load_split
from backend.db import Database
from backend.evaluation.evaluation_runner import evaluate_predictions
from backend.evaluation.inference_runner import infer_record,infer_benchmark_batch
from backend.hardware import audit, readiness
from backend.gpu_memory import memory_policy,apply_inference_memory_policy,memory_observation
from backend.modeling import PrerequisiteError, QwenEngine, adapter_manifest
from backend.settings import ROOT, config, digest, read_json, read_jsonl, utcnow, write_json, write_jsonl

log = logging.getLogger(__name__)
EXPERIMENTS = {
    "A":{"name":"Original Qwen","lora":False,"rag":False},
    "B":{"name":"Qwen + LoRA","lora":True,"rag":False},
    "C":{"name":"Qwen + RAG","lora":False,"rag":True},
    "D":{"name":"Qwen + LoRA + RAG","lora":True,"rag":True},
}


def gpu_lock():
    path = ROOT/".cache"/"gpu-execution.lock"
    path.parent.mkdir(parents=True,exist_ok=True)
    return FileLock(path)


def gpu_available():
    try:
        with gpu_lock().acquire(timeout=0):
            return True
    except Timeout:
        return False


def evaluation_rows(track: str, version: str | None = None):
    if track == "benchmark":
        manifest = current_manifest() if version is None else read_json(ROOT/"data"/"benchmark"/"versions"/version/"manifest.json")
        if not manifest:
            raise PrerequisiteError("The benchmark has not been prepared.")
        return manifest,load_split("test",version=manifest["version"])
    if track == "campus":
        manifest = read_json(COLLEGE/"test_manifest.json") if version is None else read_json(COLLEGE/"test_versions"/version/"manifest.json")
        if not manifest:
            raise PrerequisiteError("No reviewed and sealed campus test questions exist.")
        rows = read_jsonl(COLLEGE/"test_versions"/manifest["version"]/"test.jsonl")
        if digest(rows) != manifest["test_checksum"]:
            raise PrerequisiteError("Campus test checksum mismatch")
        return manifest,rows
    raise ValueError("Track must be benchmark or campus")


def select_records(rows, limit_per_language=None):
    if limit_per_language is None:
        return rows
    # Pilot selection depends only on stable IDs, never answers or test performance.
    counts,selected = {},[]
    for row in sorted(rows,key=lambda r:r["benchmark_id"]):
        language = row["language"]
        if counts.get(language,0) < limit_per_language:
            selected.append(row)
            counts[language] = counts.get(language,0)+1
    return selected


def preflight_evaluation(track, experiment, *, limit_per_language=None):
    if experiment not in EXPERIMENTS or (track == "benchmark" and experiment not in {"A","B"}):
        raise ValueError("The benchmark supports A/B; the campus track supports A/B/C/D.")
    available = gpu_available()
    hardware = audit(check_torch=available)
    ready = readiness(hardware)
    blockers = ready["blockers"][:]
    if not available:
        blockers.append('A local GPU job is already running. Wait for its completion before starting another experiment.')
    model = config("model_config")
    if not model.get("revision"):
        blockers.append("Official model revision is not pinned. Run resolve-model.")
    manifest,rows = None,[]
    try:
        manifest,rows = evaluation_rows(track)
    except PrerequisiteError as exc:
        blockers.append(str(exc))
    adapter = None
    if EXPERIMENTS[experiment]["lora"]:
        try:
            adapter = adapter_manifest()
            if manifest and track == "benchmark" and adapter["dataset_version"] != manifest["version"]:
                blockers.append("Adapter training dataset version differs from the current benchmark version.")
        except PrerequisiteError as exc:
            blockers.append(str(exc))
    ingestion = read_json(COLLEGE/"ingestion_manifest.json") if EXPERIMENTS[experiment]["rag"] else None
    if EXPERIMENTS[experiment]["rag"]:
        if not ingestion:
            blockers.append("A validated ChromaDB campus index is required for RAG experiments.")
        elif manifest and manifest["corpus_version"] != ingestion["corpus_version"]:
            blockers.append("Campus test annotations and current retrieval index use different corpus versions.")
    rows = select_records(rows,limit_per_language)
    return {"ready":not blockers,"blockers":blockers,"hardware":hardware,"model":model,
            "manifest":manifest,"rows":rows,"adapter":adapter,"ingestion":ingestion}


def submit_evaluation(database: Database, *, track, experiment, limit_per_language=None, recovery_from=None):
    checked = preflight_evaluation(track,experiment,limit_per_language=limit_per_language)
    if not checked["ready"]:
        raise PrerequisiteError("\n".join(checked["blockers"]))
    model = checked["model"]
    configuration = {"model_id":model["model_id"],"model_revision":model["revision"],
            "adapter":checked["adapter"],"prompt_version":model["prompt_version"],"generation":model["generation"],
            "max_input_tokens":model["max_input_tokens"],"seed":model["seed"],"hardware":checked["hardware"],
            "ingestion":checked["ingestion"],"limit_per_language":limit_per_language,"evidence_as_of":utcnow(),
            "context_condition":"supplied_benchmark_context" if track == "benchmark" else
                   ("retrieved_verified_campus_evidence" if EXPERIMENTS[experiment]["rag"] else "closed_book_no_campus_evidence"),
            "test_ids":[r["benchmark_id"] for r in checked["rows"]]}
    configuration['inference_execution'] = {'maximum_batch_size':model.get('evaluation_batch_size',1) if track=='benchmark' else 1,
             'batch_token_budget':model.get('evaluation_batch_token_budget',model['max_input_tokens']),
             'batching_policy':'language/input-length/stable-ID; no reference-answer selection'}
    configuration['model_execution'] = {key:model.get(key) for key in ['attention_implementation','quantization','double_quantization','compute_dtype']}
    configuration['runtime_memory_policy']=memory_policy()
    if track=='campus':
        configuration['reference_annotation_policy']=checked['manifest'].get('reference_annotation_policy',{})
    evaluation_fingerprint = digest([{k:r[k] for k in ["benchmark_id","question","reference_answer","context","language"]} for r in checked["rows"]])
    if recovery_from:
        from backend.recovery import recovery_selection
        source=database.run(recovery_from)
        if source:
            configuration['evidence_as_of']=source['configuration']['evidence_as_of']
        configuration['recovery'],_=recovery_selection(database,recovery_from,configuration=configuration,
            fingerprint=evaluation_fingerprint,dataset_version=checked['manifest']['version'],track=track,experiment=experiment)
    if experiment == "B" and track == "benchmark":
        baselines = [r for r in database.runs() if r["experiment"] == "A" and r["track"] == "benchmark" and
                     r["status"] == "completed" and r["evaluation_fingerprint"] == evaluation_fingerprint and
                     r["dataset_version"] == checked["manifest"]["version"] and
                     r["configuration"]["generation"] == configuration["generation"] and
                     r["configuration"]["model_revision"] == configuration["model_revision"] and
                     r["configuration"]["prompt_version"] == configuration["prompt_version"] and
                     r['configuration'].get('inference_execution',{})==configuration['inference_execution']]
        if not baselines:
            raise PrerequisiteError("A completed, identical original-model baseline is required before LoRA evaluation.")
    database.register_dataset(checked["manifest"])
    run_id = database.create_run(track=track,experiment=experiment,dataset_version=checked["manifest"]["version"],
                                evaluation_fingerprint=evaluation_fingerprint,configuration=configuration,total=len(checked["rows"]))
    folder = result_folder(database.run(run_id))
    folder.mkdir(parents=True,exist_ok=False)
    write_json(folder/"configuration.json",database.run(run_id),exclusive=True)
    try:
        with (folder/"worker.log").open("a",encoding="utf-8") as stream:
            process = subprocess.Popen([sys.executable,"-m","backend.cli","run-job","--run-id",run_id],
                cwd=str(ROOT),stdout=stream,stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            database.register_worker(run_id,process.pid)
    except Exception as exc:
        database.transition(run_id,"failed",error=f"Worker launch failed: {exc}")
        raise
    return database.run(run_id)


def result_folder(run):
    prefix = "baseline" if run["track"] == "benchmark" and run["experiment"] == "A" else "lora" if run["track"] == "benchmark" else "campus"
    return ROOT/"results"/prefix/run["run_id"]


def execute_run(run_id: str):
    database = Database()
    run = database.run(run_id)
    if not run or run["status"] != "queued":
        raise ValueError("Job does not exist or has already started")
    engine = None
    folder = result_folder(run)
    try:
        # Prevent concurrent training/evaluation/chat allocation of the laptop GPU.
        with gpu_lock().acquire(timeout=0), ExitStack() as cleanup:
            database.transition(run_id,"running")
            stored = run["configuration"]
            current = config("model_config")
            for key, stored_key in [("model_id","model_id"),("revision","model_revision"),("prompt_version","prompt_version"),
                                    ("generation","generation"),("max_input_tokens","max_input_tokens"),("seed","seed")]:
                if current[key] != stored[stored_key]:
                    raise PrerequisiteError("The model configuration changed after submission; create a new run.")
            execution = stored.get('inference_execution',{'maximum_batch_size':1,'batch_token_budget':current['max_input_tokens']})
            if stored.get('model_execution') and stored['model_execution']!={key:current.get(key) for key in stored['model_execution']}:
                raise PrerequisiteError('The quantization/attention execution configuration changed after submission')
            _,all_rows = evaluation_rows(run["track"],run["dataset_version"])
            ids = set(stored["test_ids"])
            rows = [r for r in all_rows if r["benchmark_id"] in ids]
            if digest([{k:r[k] for k in ["benchmark_id","question","reference_answer","context","language"]} for r in select_records(rows,stored["limit_per_language"])]) != run["evaluation_fingerprint"]:
                raise PrerequisiteError("Evaluation population fingerprint changed")
            rows = select_records(rows,stored["limit_per_language"])
            retriever = None
            if EXPERIMENTS[run["experiment"]]["rag"]:
                from backend.retrieval import Retriever
                retriever = Retriever(stored["ingestion"],as_of=stored["evidence_as_of"])
            adapter = adapter_manifest(Path(stored["adapter"]["adapter_path"])) if stored.get("adapter") else None
            def append(prediction):
                prediction_id=database.add_prediction(run_id,prediction)
                with (folder/'predictions.jsonl').open('a',encoding='utf-8') as stream:
                    import json
                    stream.write(json.dumps({**prediction,'prediction_id':prediction_id},ensure_ascii=False)+'\n')
            inherited=set()
            if stored.get('recovery'):
                from backend.recovery import restore_observations
                inherited=restore_observations(database,run,append)
                write_json(folder/'recovery_manifest.json',stored['recovery'],exclusive=True)
            memory=apply_inference_memory_policy(stored.get('runtime_memory_policy') or memory_policy())
            engine = QwenEngine(adapter)
            cleanup.callback(engine.close)
            write_json(folder/"loading.json",{"model_loading_seconds":engine.loading_seconds,'runtime_memory':memory},exclusive=True)
            if run['track']=='benchmark' and execution['maximum_batch_size']>1:
                from backend.evaluation.batching import pack_batches
                batches = pack_batches(rows,engine.input_lengths(rows),maximum_size=execution['maximum_batch_size'],
                                       token_budget=execution['batch_token_budget'])
            else:
                batches = ([row] for row in rows)
            for batch in batches:
                restored=[row['benchmark_id'] in inherited for row in batch]
                if all(restored):
                    continue
                if any(restored):
                    raise PrerequisiteError('Recovery would split a generation batch; source observations are inconsistent')
                if len(batch)>1:
                    batch_predictions = infer_benchmark_batch(engine,batch,experiment=run['experiment'])
                else:
                    batch_predictions = [infer_record(engine,batch[0],track=run['track'],experiment=run['experiment'],retriever=retriever)]
                for prediction in batch_predictions:
                    prediction["adapter_revision"] = adapter["adapter_revision"] if adapter else None
                    prediction.update(execution_segment_id=run_id,runtime_memory_policy=stored.get('runtime_memory_policy'))
                    append(prediction)
            observed_memory=memory_observation(engine)
            if observed_memory:
                write_json(folder/'memory.json',observed_memory,exclusive=True)
            # Release model/cache memory before loading all predictions for CPU scoring.
            # The GPU lock remains held until metrics are persisted.
            cleanup.close()
            predictions = database.predictions(run_id,limit=1_000_000)
            metrics = evaluate_predictions(predictions,k=stored["ingestion"]["configuration"]["top_k"] if stored.get("ingestion") else 4)
            metrics.update(run_id=run_id,dataset_version=run["dataset_version"],track=run["track"],experiment=run["experiment"])
            database.store_metrics(run_id,metrics)
            write_json(folder/"metrics.json",metrics,exclusive=True)
            errors = sum(r["evaluation_status"] != "completed" for r in predictions)
        # A coordinator may start the next job as soon as terminal status is visible.
        # Publish that status only after cleanup and GPU-lock release have finished.
        database.transition(run_id,"failed" if errors else "completed",error=f"{errors} record inference failures" if errors else None)
        write_json(folder/"run.json",database.run(run_id),exclusive=True)
        from backend.reporting import write_run_report
        write_run_report(database,run_id)
        return database.run(run_id)
    except Exception as exc:
        if database.run(run_id)["status"] in {"queued","running"}:
            database.transition(run_id,"failed",error=str(exc))
        log.exception("Experiment %s failed",run_id)
        raise
def compare_runs(database, run_ids):
    runs = [database.run(run_id) for run_id in run_ids]
    if not all(runs):
        raise ValueError("One or more experiments do not exist")
    versions={(database.metrics(run['run_id']) or {}).get('definitions_version') for run in runs
              if database.metrics(run['run_id'])}
    if len(versions)>1:
        raise ValueError('Incomparable metric definitions; replay saved predictions with recompute-metrics before comparing')
    for key in ["track","dataset_version","evaluation_fingerprint"]:
        if len({run[key] for run in runs}) != 1:
            raise ValueError(f"Incomparable experiments: different {key}")
    for key in ["model_revision","prompt_version","generation","max_input_tokens","seed"]:
        if len({digest(run["configuration"][key]) for run in runs}) != 1:
            raise ValueError(f"Incomparable experiments: different {key}")
    if len({digest(run['configuration'].get('inference_execution',{})) for run in runs})!=1:
        raise ValueError('Incomparable experiments: different inference execution/batching conditions')
    if len({digest(run['configuration'].get('model_execution',{})) for run in runs})!=1:
        raise ValueError('Incomparable experiments: different quantization/attention execution conditions')
    rag = [run for run in runs if EXPERIMENTS[run["experiment"]]["rag"]]
    if len({digest(r["configuration"]["ingestion"]) for r in rag}) > 1:
        raise ValueError("RAG experiments used different evidence indexes")
    # Match actual retrieval contexts for C/D rather than merely assuming the same index is enough.
    if len(rag) > 1:
        plans = []
        for run in rag:
            predictions = database.predictions(run["run_id"],limit=1_000_000)
            plans.append(digest(sorted([(p["question_id"],p["context"]) for p in predictions])))
        if len(set(plans)) != 1:
            raise ValueError("RAG experiments did not receive the same retrieved evidence")
    memory_policies={digest(run['configuration'].get('runtime_memory_policy')) for run in runs}
    return {"runs":[{"run":run,"metrics":database.metrics(run["run_id"])} for run in runs],
            "evidence_conditions":{run["experiment"]:run["configuration"]["context_condition"] for run in runs},
            'same_runtime_memory_policy':len(memory_policies)==1,
            'timing_interpretation':'Observed desktop timings; recovery runs retain original measurement segments. Memory-policy differences and host contention prevent isolating adapter overhead.',
            "matched_population":True}
