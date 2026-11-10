from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from backend.settings import ROOT, config


def parser():
    args = argparse.ArgumentParser(description="Campus QA reproducible research pipeline")
    commands = args.add_subparsers(dest="command",required=True)
    audit = commands.add_parser("audit")
    audit.add_argument("--check-torch",action="store_true")
    for name in ["acquire","prepare","resolve-model","tokenizer-check","preflight","train","collect-sources","ingest","status"]:
        commands.add_parser(name)
    run = commands.add_parser("run-evaluation")
    run.add_argument("--track",choices=["benchmark","campus"],required=True)
    run.add_argument("--experiment",choices=list("ABCD"),required=True)
    run.add_argument("--limit-per-language",type=int)
    job = commands.add_parser("run-job")
    job.add_argument("--run-id",required=True)
    study = commands.add_parser('run-study')
    study.add_argument('--phase',choices=['all','benchmark','campus'],default='all')
    study.add_argument('--resume')
    study_job = commands.add_parser('run-study-job')
    study_job.add_argument('--study-id',required=True)
    study_job.add_argument('--phase',choices=['all','benchmark','campus'],default='all')
    for name in ["import-faq","seal-campus-test"]:
        command = commands.add_parser(name)
        command.add_argument("path",type=Path)
    embedding = commands.add_parser("evaluate-embeddings")
    embedding.add_argument("path",type=Path)
    embedding.add_argument("--select",action="store_true")
    delete = commands.add_parser("delete-document")
    delete.add_argument("document_id")
    importing = commands.add_parser("import-training")
    importing.add_argument("path",type=Path)
    importing.add_argument("--source-name",required=True)
    importing.add_argument("--license",required=True)
    importing.add_argument("--source-url",required=True)
    checking = commands.add_parser("inspect-run")
    checking.add_argument("run_id")
    replay = commands.add_parser('recompute-metrics')
    replay.add_argument('run_id')
    recovery = commands.add_parser('recover-evaluation')
    recovery.add_argument('run_id')
    serving = commands.add_parser("serve")
    serving.add_argument("--port",type=int,default=8000)
    return args


def main():
    args = parser().parse_args()
    logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger('httpx').setLevel(logging.WARNING)
    try:
        command = args.command
        if command == "audit":
            from backend.hardware import save_report
            result = save_report(args.check_torch)
        elif command == "acquire":
            from backend.datasets import acquire
            result = acquire()
        elif command == "prepare":
            from backend.datasets import prepare
            from backend.db import Database
            result = prepare()
            Database().register_dataset(result)
        elif command == "import-training":
            from backend.datasets import import_training
            result = import_training(args.path,source_name=args.source_name,license_name=args.license,source_url=args.source_url)
        elif command == "resolve-model":
            from backend.modeling import resolve_model
            from backend.db import Database
            result = resolve_model()
            Database().register_model(result)
        elif command == "tokenizer-check":
            from backend.modeling import tokenizer_check
            result = tokenizer_check()
        elif command == "preflight":
            from backend.training import preflight
            result = preflight()
        elif command == "train":
            from backend.training import train
            from backend.experiments import gpu_lock
            with gpu_lock().acquire(timeout=0):
                result = train()
        elif command == "run-evaluation":
            if args.limit_per_language is not None and not 1 <= args.limit_per_language <= 1000:
                raise ValueError("Pilot limit must be between 1 and 1000")
            from backend.experiments import submit_evaluation
            from backend.db import Database
            result = submit_evaluation(Database(),track=args.track,experiment=args.experiment,limit_per_language=args.limit_per_language)
        elif command == "run-job":
            from backend.experiments import execute_run
            result = execute_run(args.run_id)
        elif command == 'run-study':
            from backend.study import launch_study
            result = launch_study(phase=args.phase,resume=args.resume)
        elif command == 'run-study-job':
            from backend.study import execute_study
            result = execute_study(args.study_id,phase=args.phase)
        elif command == "inspect-run":
            from backend.db import Database
            database = Database()
            result = {"run":database.run(args.run_id),"metrics":database.metrics(args.run_id)}
            if not result["run"]:
                raise ValueError("Run not found")
        elif command == 'recompute-metrics':
            from backend.db import Database
            from backend.evaluation.evaluation_runner import recompute_run
            result=recompute_run(Database(),args.run_id)
        elif command == 'recover-evaluation':
            from backend.db import Database
            from backend.experiments import submit_evaluation
            database=Database()
            source=database.run(args.run_id)
            if not source:
                raise ValueError('Source evaluation does not exist')
            result=submit_evaluation(database,track=source['track'],experiment=source['experiment'],
                limit_per_language=source['configuration'].get('limit_per_language'),recovery_from=args.run_id)
        elif command == "collect-sources":
            from backend.college import collect_sources
            result = collect_sources()
        elif command == "import-faq":
            from backend.college import import_faq
            result = import_faq(args.path)
        elif command == "seal-campus-test":
            from backend.college import seal_campus_test
            result = seal_campus_test(args.path)
        elif command == "delete-document":
            from backend.college import delete_document
            result = delete_document(args.document_id)
        elif command == "evaluate-embeddings":
            from backend.retrieval import evaluate_embeddings
            result = evaluate_embeddings(args.path,select=args.select)
        elif command == "ingest":
            from backend.retrieval import ingest
            result = ingest()
        elif command == "status":
            from backend.datasets import current_manifest
            from backend.db import Database
            from backend.college import college_summary
            from backend.hardware import audit
            result = {"benchmark":current_manifest(),"hardware":audit(),"runs":Database().runs(),
                      "training":Database().training(),"college":college_summary()}
        elif command == "serve":
            import uvicorn
            uvicorn.run("backend.main:app",host="127.0.0.1",port=args.port,workers=1)
            return
        print(json.dumps(result,ensure_ascii=True,indent=2,default=str))
        if command == "preflight" and not result["ready"]:
            sys.exit(2)
    except Exception as exc:
        print(json.dumps({"status":"blocked_or_failed","error":str(exc)},ensure_ascii=True),file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
