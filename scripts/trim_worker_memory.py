"""One-off Windows working-set trim for a verified project worker under severe RAM pressure.

This changes page residency, not virtual memory contents or model settings. It can
cause page faults and is not a substitute for adequate RAM. Never run periodically.
API: https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-emptyworkingset
"""
import argparse
import ctypes
import json
import os
import time
from ctypes import wintypes
from pathlib import Path

import psutil

from backend.db import Database
from backend.settings import ROOT, utcnow, write_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id',required=True)
    parser.add_argument('--pid',required=True,type=int)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    if os.name!='nt':
        raise SystemExit('This diagnostic is Windows-only')
    database=Database()
    run=database.run(args.run_id)
    if not run or run['status']!='running':
        raise SystemExit('Only a currently running registered evaluation can be targeted')
    with database.connect() as connection:
        registered=connection.execute('SELECT pid,process_started FROM job_processes WHERE run_id=?',(args.run_id,)).fetchone()
    if not registered:
        raise SystemExit('No registered worker identity exists')
    launcher=psutil.Process(registered['pid'])
    if abs(launcher.create_time()-registered['process_started'])>=1:
        raise SystemExit('The registered process identity changed')
    worker=psutil.Process(args.pid)
    command=worker.cmdline()
    if (Path(worker.cwd()).resolve()!=ROOT.resolve() or not Path(worker.exe()).resolve().is_relative_to(ROOT.resolve())
            or 'backend.cli' not in command or 'run-job' not in command or '--run-id' not in command
            or command[command.index('--run-id')+1]!=args.run_id
            or launcher.pid not in [worker.pid,*[p.pid for p in worker.parents()]]):
        raise SystemExit('Refusing to target a process outside this exact project evaluation')
    def observation():
        memory=psutil.virtual_memory()
        return {'worker_rss_mib':worker.memory_info().rss/1024**2,'system_ram_percent':memory.percent,
                'available_ram_mib':memory.available/1024**2}
    record={'sampled_at':utcnow(),'run_id':args.run_id,'pid':worker.pid,'process_started':worker.create_time(),
            'action':'none','before':observation(),'note':'Page residency only; no model inputs, outputs, parameters or settings are changed.'}
    if args.apply and record['before']['system_ram_percent']>=97:
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        api=ctypes.WinDLL('psapi',use_last_error=True)
        kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
        kernel.OpenProcess.restype=wintypes.HANDLE
        kernel.CloseHandle.argtypes=[wintypes.HANDLE]
        kernel.CloseHandle.restype=wintypes.BOOL
        api.EmptyWorkingSet.argtypes=[wintypes.HANDLE]
        api.EmptyWorkingSet.restype=wintypes.BOOL
        handle=kernel.OpenProcess(0x1000|0x0100,False,worker.pid) # QUERY_LIMITED_INFORMATION | SET_QUOTA
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        started=time.perf_counter()
        try:
            if not api.EmptyWorkingSet(handle):
                raise ctypes.WinError(ctypes.get_last_error())
            record.update(action='single_EmptyWorkingSet',duration_seconds=time.perf_counter()-started)
        finally:
            kernel.CloseHandle(handle)
    record['after']=observation()
    folder=ROOT/'results'/'studies'
    # The study folder is derived from the existing coordinator plan, never from an arbitrary path argument.
    from backend.study import study_path
    matches=[p for p in folder.glob('*/state.json') if args.run_id in p.read_text(encoding='utf-8')]
    target=(study_path(matches[0].parent.name)/'runtime_health') if len(matches)==1 else ROOT/'results'/'runtime_health'
    import uuid
    path=target/f'working-set-{uuid.uuid4()}.json'
    write_json(path,record,exclusive=True)
    print(json.dumps({**record,'observation_path':str(path)},indent=2))


if __name__=='__main__':
    main()
