"""Durable stage coordinator. All reported stage IDs refer to actual persisted jobs."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

from backend.db import Database
from backend.settings import ROOT, config, digest, model_directory, read_json, utcnow, write_json
from backend.modeling import PrerequisiteError,adapter_manifest


def study_path(study_id):
    uuid.UUID(study_id)
    return ROOT/'results'/'studies'/study_id


def save_state(study_id,**updates):
    folder = study_path(study_id)
    current = read_json(folder/'state.json',{})
    current.setdefault('study_id',study_id)
    current.update(updates,updated_at=utcnow())
    temporary = folder/f'.state-{uuid.uuid4()}.json'
    write_json(temporary,current,exclusive=True)
    temporary.replace(folder/'state.json')
    with (folder/'events.jsonl').open('a',encoding='utf-8') as stream:
        stream.write(json.dumps({'time':utcnow(),**updates},ensure_ascii=False)+'\n')
    print(json.dumps({'study_id':study_id,**updates},ensure_ascii=False),flush=True)
    return current


def launch_study(*,phase='all',resume=None):
    from backend.datasets import current_manifest
    if phase not in {'all','benchmark','campus'}:
        raise ValueError('Unknown study phase')
    plan = {'model':config('model_config'),'training':config('training'),
            'dataset_version':(current_manifest() or {}).get('version')}
    if not plan['dataset_version']:
        raise PrerequisiteError('Prepare the benchmark before starting the study')
    if resume:
        study_id = resume
        state = read_json(study_path(study_id)/'state.json')
        if not state or state['plan_fingerprint'] != digest(plan):
            raise PrerequisiteError('The saved study plan differs from the active model/training/dataset configuration')
        import psutil
        try:
            running = state.get('pid') and abs(psutil.Process(state['pid']).create_time()-state['process_started'])<1
        except (psutil.Error,KeyError):
            running = False
        if running:
            raise PrerequisiteError('This study coordinator is already running')
        save_state(study_id,next_action=None)
    else:
        study_id = str(uuid.uuid4())
        study_path(study_id).mkdir(parents=True,exist_ok=False)
        write_json(study_path(study_id)/'plan.json',plan,exclusive=True)
        save_state(study_id,status='queued',phase=phase,stage='starting',created_at=utcnow(),
                   plan_fingerprint=digest(plan),run_ids={})
    with (study_path(study_id)/'coordinator.log').open('a',encoding='utf-8') as stream:
        process = subprocess.Popen([sys.executable,'-u','-m','backend.cli','run-study-job','--study-id',study_id,'--phase',phase],
            cwd=str(ROOT),stdout=stream,stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    import psutil
    return save_state(study_id,pid=process.pid,process_started=psutil.Process(process.pid).create_time(),
                      status='running',phase=phase,error=None,ended_at=None)


def cli_json(*arguments):
    process = subprocess.run([sys.executable,'-m','backend.cli',*arguments],cwd=str(ROOT),capture_output=True,text=True,encoding='utf-8')
    if process.returncode:
        raise RuntimeError(process.stderr.strip() or process.stdout.strip())
    return json.loads(process.stdout)


def compatible_run(run,track,experiment,version,model,*,adapter_revision=None,ingestion_version=None,statuses=('completed',)):
    stored = run['configuration']
    return run['status'] in statuses and run['track']==track and run['experiment']==experiment and run['dataset_version']==version \
        and stored.get('limit_per_language') is None and stored.get('model_id')==model['model_id'] \
        and stored.get('model_revision')==model['revision'] and stored.get('generation')==model['generation'] \
        and stored.get('prompt_version')==model['prompt_version'] and stored.get('max_input_tokens')==model['max_input_tokens'] \
        and stored.get('seed')==model['seed'] \
        and (stored.get('inference_execution') or {}).get('maximum_batch_size',1)==(model.get('evaluation_batch_size',1) if track=='benchmark' else 1) \
        and (not model.get('attention_implementation') or (stored.get('model_execution') or {}).get('attention_implementation')==model['attention_implementation']) \
        and (adapter_revision is None or (stored.get('adapter') or {}).get('adapter_revision')==adapter_revision) \
        and (ingestion_version is None or (stored.get('ingestion') or {}).get('version')==ingestion_version)


def wait_run(study_id,run_id,*,poll_seconds=15):
    while True:
        database = Database()
        database.recover_interrupted()
        run = database.run(run_id)
        if not run:
            raise RuntimeError('Evaluation job disappeared from the registry')
        save_state(study_id,active_run_id=run_id,completed_predictions=run['completed'],total_predictions=run['total'],job_status=run['status'])
        if run['status']=='completed':
            return run
        if run['status'] not in {'queued','running'}:
            raise RuntimeError(f"Evaluation {run_id} {run['status']}: {run.get('error')}")
        time.sleep(poll_seconds)


def execute_study(study_id,*,phase='all'):
    from backend.datasets import current_manifest
    from backend.experiments import compare_runs
    state = read_json(study_path(study_id)/'state.json')
    if not state:
        raise ValueError('Study does not exist')
    plan = read_json(study_path(study_id)/'plan.json')
    current = {'model':config('model_config'),'training':config('training'),'dataset_version':(current_manifest() or {}).get('version')}
    if digest(current)!=state['plan_fingerprint']:
        raise PrerequisiteError('The study configuration changed before execution')
    model = plan['model']
    ids = state.get('run_ids',{})
    def evaluate(track,letter,version):
        key = f'{track}_{letter}'
        required_adapter = adapter_manifest()['adapter_revision'] if letter in {'B','D'} else None
        index = read_json(ROOT/'data'/'college_faq'/'ingestion_manifest.json',{}) if letter in {'C','D'} else {}
        existing = next((r for r in Database().runs(limit=10000) if compatible_run(r,track,letter,version,model,
                         adapter_revision=required_adapter,ingestion_version=index.get('version'))),None)
        previous=Database().run(ids[key]) if key in ids else None
        if existing:
            run_id=existing['run_id']
        elif previous and compatible_run(previous,track,letter,version,model,adapter_revision=required_adapter,
                ingestion_version=index.get('version'),statuses=('queued','running','interrupted')):
            run_id=(cli_json('recover-evaluation',previous['run_id'])['run_id'] if previous['status']=='interrupted' else previous['run_id'])
        else:
            run_id=cli_json('run-evaluation','--track',track,'--experiment',letter)['run_id']
        ids[key] = run_id
        save_state(study_id,stage=key,run_ids=ids)
        return wait_run(study_id,run_id)
    try:
        if phase in {'all','benchmark'}:
            evaluate('benchmark','A',plan['dataset_version'])
            try:
                adapter = adapter_manifest()
                if adapter['dataset_version']!=plan['dataset_version'] or adapter['configuration']!=plan['training']:
                    adapter = None
            except PrerequisiteError:
                adapter = None
            if adapter is None:
                save_state(study_id,stage='training',active_run_id=None)
                process = subprocess.run([sys.executable,'-u','-m','backend.cli','train'],cwd=str(ROOT))
                if process.returncode:
                    raise RuntimeError('Training failed; inspect the persisted training run and coordinator log')
                adapter = adapter_manifest()
            save_state(study_id,training_id=adapter['training_id'],adapter_revision=adapter['adapter_revision'])
            evaluate('benchmark','B',plan['dataset_version'])
            comparison = compare_runs(Database(),[ids['benchmark_A'],ids['benchmark_B']])
            write_json(study_path(study_id)/'benchmark_comparison.json',comparison)
            if phase=='benchmark':
                return save_state(study_id,status='benchmark_completed',stage='benchmark_completed',active_run_id=None,ended_at=utcnow())
        from backend.college import COLLEGE,require_benchmark_complete
        require_benchmark_complete()
        corpus = read_json(COLLEGE/'manifest.json')
        campus_test = read_json(COLLEGE/'test_manifest.json')
        ingestion = read_json(COLLEGE/'ingestion_manifest.json')
        if not corpus or not campus_test or not ingestion:
            return save_state(study_id,status='waiting_for_verified_campus_data',stage='campus_ground_truth',active_run_id=None,
                next_action='Collect official sources, review multilingual FAQs/retrieval labels, seal campus test, evaluate embeddings, and ingest. Then resume the campus phase.')
        for letter in 'ABCD':
            evaluate('campus',letter,campus_test['version'])
        comparison = compare_runs(Database(),[ids[f'campus_{letter}'] for letter in 'ABCD'])
        write_json(study_path(study_id)/'campus_comparison.json',comparison)
        return save_state(study_id,status='model_experiments_completed',stage='human_annotations',active_run_id=None,
                          ended_at=utcnow(),next_action='Review source references and response claims in the dashboard to populate human factuality metrics.',
                          note='Human factuality metrics remain pending until actual reviews are recorded.')
    except Exception as exc:
        save_state(study_id,status='failed',error=str(exc),ended_at=utcnow())
        raise
