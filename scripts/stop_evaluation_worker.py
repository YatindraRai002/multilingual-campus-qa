"""Prepare, or explicitly apply, a controlled stop of one verified project evaluation.

The worker is stopped and confirmed dead before the normal interrupted-job
recovery updates its status. Existing prediction bytes are checked afterward.
Without --apply this only prints a proposal and never stops a process.
"""
import argparse
import hashlib
import json
from pathlib import Path
import uuid

import psutil

from backend.db import Database
from backend.settings import ROOT,digest,utcnow,write_json


def prediction_prefix(database,run_id,limit=-1):
    result=hashlib.sha256();count=0
    with database.connect() as connection:
        for row in connection.execute('SELECT prediction_id,question_id,payload FROM predictions WHERE run_id=? ORDER BY rowid LIMIT ?',
                                      (run_id,limit)):
            result.update((json.dumps(list(row),ensure_ascii=False,separators=(',',':'))+'\n').encode('utf-8'))
            count+=1
    return {'count':count,'sha256':result.hexdigest()}


def exact_worker(process,run_id):
    args=process.cmdline()
    return (Path(process.cwd()).resolve()==ROOT.resolve() and Path(process.exe()).resolve().is_relative_to(ROOT.resolve())
            and 'backend.cli' in args and 'run-job' in args and '--run-id' in args
            and args[args.index('--run-id')+1]==run_id)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id',required=True)
    parser.add_argument('--pid',required=True,type=int)
    parser.add_argument('--expected-start',required=True,type=float)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    database=Database();run=database.run(args.run_id)
    if not run or run['status']!='running' or run['completed']>=run['total']:
        raise SystemExit('This evaluation no longer has unfinished active inference; no process was stopped')
    with database.connect() as connection:
        identity=connection.execute('SELECT pid,process_started FROM job_processes WHERE run_id=?',(args.run_id,)).fetchone()
    if not identity:
        raise SystemExit('No registered worker identity exists')
    launcher=psutil.Process(identity['pid']);worker=psutil.Process(args.pid)
    if (abs(launcher.create_time()-identity['process_started'])>=1 or abs(worker.create_time()-args.expected_start)>=.001
            or not exact_worker(launcher,args.run_id) or not exact_worker(worker,args.run_id)
            or launcher.pid not in [worker.pid,*[p.pid for p in worker.parents()]]):
        raise SystemExit('Process identity does not match this exact project evaluation')
    before=prediction_prefix(database,args.run_id)
    proposal={'prepared_at':utcnow(),'run_id':args.run_id,'worker_pid':worker.pid,'worker_started':worker.create_time(),
        'launcher_pid':launcher.pid,'launcher_started':launcher.create_time(),'checkpoint':before,
        'configuration_sha256':digest(run['configuration']),'total':run['total'],
        'stop_method':'terminate only the verified inference worker; wait for worker and launcher exit; then recover interrupted status',
        'saved_predictions_policy':'Retain every original prediction byte and original run ID. A new recovery run copies complete successful batches with origin IDs.',
        'apply_requested':args.apply}
    if not args.apply:
        print(json.dumps(proposal,indent=2));return
    # Recheck immediately before the only process mutation.
    current=database.run(args.run_id)
    if current['status']!='running' or current['completed']>=current['total'] or not exact_worker(worker,args.run_id):
        raise SystemExit('The job state changed while preparing; nothing was stopped')
    proposal['stop_requested_at']=utcnow()
    worker.terminate()
    worker.wait(timeout=30)
    if launcher.pid!=worker.pid:
        launcher.wait(timeout=15)
    proposal['process_exit_confirmed_at']=utcnow()
    # No active writer remains when the terminal database status is recorded.
    database.recover_interrupted()
    after=prediction_prefix(database,args.run_id,before['count'])
    if after!=before:
        raise RuntimeError('Saved prediction prefix failed verification; do not launch recovery')
    proposal.update(checkpoint_preserved=True,source_status=database.run(args.run_id)['status'],
                    saved_predictions_after_exit=database.run(args.run_id)['completed'])
    folder=ROOT/'results'/'worker_stops'
    write_json(folder/f'{args.run_id}-{uuid.uuid4()}.json',proposal,exclusive=True)
    print(json.dumps(proposal,indent=2))


if __name__=='__main__':
    main()
