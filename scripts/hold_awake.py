"""Temporarily prevent Windows sleep while the local study is being executed."""
import argparse
import ctypes
import os
import time
from backend.settings import read_json
from backend.study import study_path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('study_id')
parser.add_argument('--include-campus-preparation',action='store_true',
    help='Also cover the source-review and capacity-check interval before campus jobs resume.')
arguments=parser.parse_args()
folder=study_path(arguments.study_id)
statuses={'queued','running'}
if arguments.include_campus_preparation:
    statuses.add('waiting_for_verified_campus_data')
if os.name!='nt':
    raise SystemExit('No Windows power hold needed on this platform')
continuous=0x80000000
system_required=0x00000001
active=bool(ctypes.windll.kernel32.SetThreadExecutionState(continuous|system_required))
print(f'Temporary system-sleep hold for active study: {active}',flush=True)
try:
    while (read_json(folder/'state.json',{}).get('status') in statuses):
        time.sleep(30)
finally:
    ctypes.windll.kernel32.SetThreadExecutionState(continuous)
    print('Temporary system-sleep hold released.',flush=True)
