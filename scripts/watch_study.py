"""Print compact, read-only progress for a real study; never creates or restarts jobs."""
import argparse
import json
import time

import psutil

from backend.db import Database
from backend.settings import read_json,utcnow
from backend.study import study_path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('study_id')
    parser.add_argument('--interval',type=float,default=50)
    parser.add_argument('--once',action='store_true')
    args=parser.parse_args()
    if not 1 <= args.interval <= 60:
        parser.error('Use an interval from 1 to 60 seconds')
    path=study_path(args.study_id)/'state.json'
    while True:
        state=read_json(path)
        if not state:
            raise SystemExit('Study state does not exist')
        row={'time':utcnow(),'stage':state.get('stage'),'status':state.get('status')}
        database=Database()
        if state.get('active_run_id'):
            run=database.run(state['active_run_id'])
            row.update(run_id=run['run_id'],completed=run['completed'],total=run['total'],job_status=run['status'])
            if run.get('error'):
                row['error']=run['error']
        if state.get('stage')=='training':
            latest=next(iter(database.training()),None)
            if latest:
                row.update(training_id=latest['training_id'],training_status=latest['status'])
                row.update(selected_training_counts=latest['payload'].get('used_training_counts'),
                           augmentation_by_language=latest['payload'].get('training_abstention_augmentation_by_language'),
                           total_optimizer_steps=latest['payload'].get('total_optimizer_steps'))
                row['latest_log']=latest['logs'][-1] if latest['logs'] else None
        if state.get('error'):
            row['error']=state['error']
        if state.get('status')=='running':
            try:
                row['coordinator_alive']=abs(psutil.Process(state['pid']).create_time()-state['process_started'])<1
            except (psutil.Error,KeyError):
                row['coordinator_alive']=False
        print(json.dumps(row,ensure_ascii=True),flush=True)
        if args.once or state.get('status') not in {'running','queued'} or not row.get('coordinator_alive',True):
            break
        time.sleep(args.interval)


if __name__=='__main__':
    main()
