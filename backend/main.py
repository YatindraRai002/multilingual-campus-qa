from __future__ import annotations

import csv
import io
import json
import logging
from contextlib import ExitStack, asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, model_validator
from starlette.middleware.trustedhost import TrustedHostMiddleware

from backend.college import college_summary
from backend.campus_chat import detect_chat_language, enforce_reply_language, faq_reply, suggestions, unavailable_reply
from backend.datasets import LANGUAGES, current_manifest, identify_language, load_split
from backend.db import Database
from backend.evaluation.evaluation_runner import evaluate_predictions
from backend.evaluation.inference_runner import infer_record
from backend.experiments import EXPERIMENTS, compare_runs, gpu_lock, preflight_evaluation, submit_evaluation
from backend.hardware import audit, readiness
from backend.gpu_memory import memory_policy,apply_inference_memory_policy
from backend.modeling import PrerequisiteError, QwenEngine, adapter_manifest
from backend.settings import ROOT, config, model_directory, read_json, utcnow

logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(application):
    application.state.db = Database()
    application.state.db.recover_interrupted()
    manifest = current_manifest()
    if manifest:
        application.state.db.register_dataset(manifest)
    model = read_json(ROOT/"results"/"model_registry.json")
    if model:
        application.state.db.register_model(model)
    yield


app = FastAPI(title="Campus QA Research",version="0.1.0",lifespan=lifespan)
app.add_middleware(TrustedHostMiddleware,allowed_hosts=["127.0.0.1","localhost","[::1]","testserver"])


@app.exception_handler(PrerequisiteError)
async def prerequisites(request,exc):
    return JSONResponse(status_code=409,content={"detail":str(exc),"status":"prerequisites_missing"})


def database():
    return app.state.db


def require_run(run_id):
    run = database().run(run_id)
    if not run:
        raise HTTPException(404,"Experiment not found")
    return run


@app.get("/api/health")
def health():
    return {"status":"ok","time":utcnow(),"service":"campus-qa-research"}


@app.get("/api/system")
def system():
    hardware = audit()
    manifest = current_manifest()
    return {"hardware":hardware,"inference":readiness(hardware),"training":hardware["training_readiness"],
            "dataset_ready":manifest is not None,"dataset_training_blockers":manifest.get("training_languages_missing",[]) if manifest else list(LANGUAGES),
            "model":config("model_config"),"training_configuration":config("training"),
            "retrieval_configuration":config("retrieval"),"experiments":EXPERIMENTS,
            "execution_policy":'User-approved Qwen2.5-1.5B local GPU study; original 7B configuration is archived.' if config('model_config').get('study_amendment') else 'Original selected model study.',
            "last_cuda_audit":read_json(ROOT/"results"/"environment.json",{}).get("cuda_test","not_run")}


@app.get("/api/datasets/summary")
def datasets_summary():
    manifest = current_manifest()
    return {"status":"ready" if manifest else "not_prepared","manifest":manifest}


@app.get("/api/datasets/languages")
def dataset_languages():
    manifest = current_manifest()
    maximum = max(manifest["splits"]["test"]["languages"].values(),default=1) if manifest else 1
    return {"languages":[{"code":code,"name":name,
             "splits":{split:manifest["splits"][split]["languages"].get(code,0) if manifest else 0 for split in ["train","validation","test"]},
             "test_bar_percent":100*manifest["splits"]["test"]["languages"].get(code,0)/maximum if manifest else 0,
             "evaluation_dataset":"SQuAD-v1.1" if code == "en" else "ai4bharat/IndicQA",
             "training_dataset":"SQuAD-v1.1" if code == "en" else 'l3cube-pune/indic-squad (approved supplement)',
             "parallel_mapping":False} for code,name in LANGUAGES.items()]}


@app.get("/api/datasets/records")
def dataset_records(split: Literal["train","validation"]="validation",language: Literal["en","hi","ta"]="en",
                    offset: int=Query(0,ge=0),limit: int=Query(5,ge=1,le=50)):
    # Test examples are intentionally absent from interactive browsing/prompt optimization screens.
    try:
        rows = [r for r in load_split(split) if r["language"] == language]
    except ValueError as exc:
        raise HTTPException(409,str(exc))
    return {"records":rows[offset:offset+limit],"total":len(rows),"split":split}


@app.get("/api/models")
def models():
    return {"base_model":config("model_config"),"official_metadata":read_json(ROOT/"results"/"model_registry.json"),
            "adapter":read_json(model_directory()/"lora_adapter"/"current.json"),"experiments":EXPERIMENTS}


@app.get("/api/training")
def training():
    manifest = current_manifest()
    from backend.study import compatible_run
    selected = config('model_config')
    baseline_available = bool(manifest) and any(compatible_run(r,'benchmark','A',manifest['version'],selected) for r in database().runs(limit=10000))
    runs = [r for r in database().training() if r['payload'].get('model_id')==selected['model_id']]
    return {"runs":runs,"configuration":config("training"),
            "baseline_available":baseline_available,
            "readiness":audit()["training_readiness"],"missing_training_languages":(current_manifest() or {}).get("training_languages_missing",list(LANGUAGES))}


@app.get('/api/studies')
def studies():
    states = [read_json(path) for path in (ROOT/'results'/'studies').glob('*/state.json')]
    states = sorted((s for s in states if s),key=lambda s:s.get('updated_at',''),reverse=True)
    return {'studies':states,'latest':states[0] if states else None}


@app.get("/api/experiments")
def experiments():
    runs = database().runs()
    return {"runs":runs,"count":len(runs),"message":"Evaluation not yet performed." if not runs else None}


@app.get("/api/experiments/compare")
def comparison(run_ids: str=Query(...,min_length=1,max_length=2000)):
    ids = run_ids.split(",")
    if not 2 <= len(ids) <= 4:
        raise HTTPException(422,"Select two to four experiments")
    try:
        return compare_runs(database(),ids)
    except ValueError as exc:
        raise HTTPException(409,str(exc))


@app.get("/api/experiments/{run_id}")
def experiment(run_id: str):
    return require_run(run_id)


@app.get("/api/experiments/{run_id}/metrics")
def metrics(run_id: str):
    require_run(run_id)
    return database().metrics(run_id) or {"status":"not_performed","message":"Evaluation not yet performed.","populations":{}}


@app.get("/api/experiments/{run_id}/predictions")
def predictions(run_id: str,offset: int=Query(0,ge=0),limit: int=Query(50,ge=1,le=250),language: Literal["en","hi","ta"] | None=None):
    run = require_run(run_id)
    return {"predictions":database().predictions(run_id,offset=offset,limit=limit,language=language),
            "run_id":run_id,"dataset_version":run["dataset_version"],"offset":offset,"total_run_predictions":run["completed"]}


@app.get("/api/experiments/{run_id}/export")
def export(run_id: str,format: Literal["json","csv","markdown"]="json"):
    run = require_run(run_id)
    records = database().predictions(run_id,limit=1_000_000)
    result = {"run":run,"metrics":database().metrics(run_id),"predictions":records}
    if format == "json":
        return Response(json.dumps(result,ensure_ascii=False,indent=2),media_type="application/json",
                        headers={"Content-Disposition":f'attachment; filename="{run_id}.json"'})
    if format == "csv":
        output = io.StringIO()
        fields = ["prediction_id","question_id","language","question","reference_answer","generated_answer","evaluation_status","total_seconds","input_tokens","output_tokens"]
        writer = csv.DictWriter(output,fieldnames=fields,extrasaction="ignore")
        writer.writeheader()
        for row in records:
            # Spreadsheet-formula injection protection for text opened in Excel.
            writer.writerow({k:("'"+str(row[k]) if isinstance(row.get(k),str) and row[k][:1] in {"=","+","-","@"} else row.get(k)) for k in fields})
        return Response("\ufeff"+output.getvalue(),media_type="text/csv;charset=utf-8",headers={"Content-Disposition":f'attachment; filename="{run_id}.csv"'})
    report = (f"# Research experiment {run_id}\n\nTrack: {run['track']}\n\nConfiguration: {run['experiment']}\n\n"
              f"Status: {run['status']}\n\nDataset: {run['dataset_version']}\n\nStarted: {run['created_at']}\n\n"
              "## Persisted backend metrics\n\n```json\n"+json.dumps(result["metrics"],ensure_ascii=False,indent=2)+"\n```\n\n"
              "Missing human annotations leave factual accuracy and hallucination metrics unscored. English SQuAD is not parallel to IndicQA.\n")
    return Response(report,media_type="text/markdown",headers={"Content-Disposition":f'attachment; filename="{run_id}.md"'})


@app.get("/api/college-faq/summary")
def faq_summary():
    from backend.college import COLLEGE
    return {"corpus":college_summary(),"ingestion":read_json(COLLEGE/"ingestion_manifest.json"),
            "test_set":read_json(COLLEGE/"test_manifest.json"),"source_registry":config("sources")}


@app.get("/api/languages/metrics")
def language_metrics(run_id: str | None=None):
    if run_id:
        require_run(run_id)
    return {"run_id":run_id,"results":database().metrics(run_id) if run_id else None,
            "message":"Evaluation not yet performed." if not run_id else None}


class EvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    track: Literal["benchmark","campus"]
    experiment: Literal["A","B","C","D"]
    limit_per_language: int | None = Field(default=None,ge=1,le=1000)


@app.post("/api/evaluation/preflight")
def evaluation_preflight(body: EvaluationRequest):
    try:
        checked = preflight_evaluation(body.track,body.experiment,limit_per_language=body.limit_per_language)
        return {"ready":checked["ready"],"blockers":checked["blockers"],"record_count":len(checked["rows"])}
    except ValueError as exc:
        raise HTTPException(422,str(exc))


@app.post("/api/evaluation/run",status_code=202)
def evaluation_run(body: EvaluationRequest):
    try:
        run = submit_evaluation(database(),track=body.track,experiment=body.experiment,limit_per_language=body.limit_per_language)
        return {"job_id":run["run_id"],"run_id":run["run_id"],"status":run["status"]}
    except ValueError as exc:
        raise HTTPException(422,str(exc))


@app.get("/api/evaluation/status/{run_id}")
def evaluation_status(run_id: str):
    return require_run(run_id)


class Claim(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1,max_length=8000)
    supported: bool
    evidence_document_ids: list[str]
    @model_validator(mode="after")
    def supported_needs_evidence(self):
        if self.supported and not self.evidence_document_ids:
            raise ValueError("Supported claims require evidence document IDs")
        return self


class AnnotationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reviewer: str = Field(min_length=2,max_length=200)
    correct: bool
    claims: list[Claim]
    claim_inventory_complete: Literal[True]
    notes: str = Field(default="",max_length=10000)


@app.post("/api/predictions/{prediction_id}/annotations")
def annotate(prediction_id: str,body: AnnotationRequest):
    prediction = database().prediction(prediction_id)
    if not prediction:
        raise HTTPException(404,"Prediction not found")
    if prediction["evaluation_status"] != "completed":
        raise HTTPException(409,"Failed predictions cannot be annotated as completed responses")
    evidence = set(prediction.get("context_document_ids",[]))
    if prediction.get("source_document_id"):
        evidence.add(prediction["source_document_id"])
    # Official reference evidence is available to human judges in every campus arm.
    # A/B having no retrieval does not make a factually correct answer hallucinated.
    evidence.update(prediction.get('relevant_document_ids',[]))
    for claim in body.claims:
        if claim.supported and not set(claim.evidence_document_ids).issubset(evidence):
            raise HTTPException(422,"Supported claims must reference the supplied context or sealed official reference evidence")
    if prediction.get("abstained") and body.claims:
        raise HTTPException(422,"Abstained responses cannot have a factual claim inventory")
    if prediction.get('abstained') and prediction.get('answerable',True) and body.correct:
        raise HTTPException(422,'An abstention is not a correct answer to an answerable question')
    try:
        payload = body.model_dump(exclude={"reviewer"})
        run_id = database().annotate(prediction_id,body.reviewer,payload)
    except KeyError:
        raise HTTPException(404,"Prediction not found")
    from backend.evaluation.evaluation_runner import recompute_run
    recompute_run(database(),run_id,reason='human_annotation')
    return {"status":"recorded","run_id":run_id,"metrics_recomputed":True}


@app.get('/api/predictions/{prediction_id}/evidence')
def prediction_evidence(prediction_id: str):
    prediction=database().prediction(prediction_id)
    if not prediction:
        raise HTTPException(404,'Prediction not found')
    from backend.review import reference_evidence
    return reference_evidence(database(),prediction)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=3,max_length=2000)
    language: Literal["en","hi","ta"] | None = None
    experiment: Literal["A","B","C","D"] = "D"
    answer_mode: Literal["model", "faq_first"] = "model"


@app.get("/api/chat/suggestions")
def chat_suggestions():
    return suggestions()


@app.post("/api/chat")
def chat(body: ChatRequest):
    language = body.language or (detect_chat_language(body.question) if body.answer_mode == "faq_first"
                                 else identify_language(body.question))
    if not language:
        raise HTTPException(422,"Choose English, Hindi or Tamil explicitly for mixed-script or transliterated questions.")
    if body.answer_mode == "faq_first" and body.experiment in {"C", "D"}:
        answer = faq_reply(body.question, language)
        if answer is not None:
            return answer
    engine = None
    from filelock import Timeout
    try:
        with gpu_lock().acquire(timeout=0), ExitStack() as cleanup:
            adapter = adapter_manifest() if EXPERIMENTS[body.experiment]["lora"] else None
            retriever = None
            if EXPERIMENTS[body.experiment]["rag"]:
                from backend.retrieval import Retriever
                retriever = Retriever()
            memory=apply_inference_memory_policy(memory_policy())
            engine = QwenEngine(adapter)
            cleanup.callback(engine.close)
            row = {"benchmark_id":"interactive-chat","language":language,"context":"","question":body.question,
                   "reference_answer":"","reference_answers":[],"source_dataset":"interactive-unscored"}
            result = infer_record(engine,row,track="campus",experiment=body.experiment,retriever=retriever)
            if result["evaluation_status"] != "completed":
                raise HTTPException(422,result["error"])
            if body.answer_mode == "faq_first":
                result = enforce_reply_language(result, language)
            return {**result,"model_loading_seconds":engine.loading_seconds,'runtime_memory':memory,"research_scored":False,
                    "notice":"Interactive answers are not research evaluation records."}
    except PrerequisiteError as exc:
        if body.answer_mode == "faq_first":
            return unavailable_reply(body.question, language, str(exc))
        raise
    except Timeout:
        if body.answer_mode == "faq_first":
            return unavailable_reply(body.question, language, "The local model is busy with another request.")
        raise HTTPException(409,"The GPU is in use by another training, evaluation or chat request.")
@app.get("/api/docs")
def documents():
    return {"documents":[{"name":path.name,"url":"/api/docs/"+path.name} for path in sorted((ROOT/"docs").glob("*.md"))]}


@app.get("/api/docs/{name}")
def document(name: str):
    import re
    if not re.fullmatch(r"[A-Z_]+\.md",name) or not (ROOT/"docs"/name).is_file():
        raise HTTPException(404,"Report not found")
    return PlainTextResponse((ROOT/"docs"/name).read_text(encoding="utf-8"))


app.mount("/",StaticFiles(directory=ROOT/"frontend",html=True),name="dashboard")
