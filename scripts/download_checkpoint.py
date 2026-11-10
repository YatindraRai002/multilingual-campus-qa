"""Download the approved public checkpoint with verified HTTP ranges and SHA-256."""
from concurrent.futures import ThreadPoolExecutor,as_completed
import argparse
import hashlib
import json
import os
from pathlib import Path
import time

import httpx

from backend.settings import ROOT,config

selected=config('model_config')
arguments=argparse.ArgumentParser(description=__doc__)
arguments.add_argument('--model',help='Optional public model repository; also supply --revision')
arguments.add_argument('--revision',help='Exact 40-character model commit')
args=arguments.parse_args()
if bool(args.model)!=bool(args.revision):
    arguments.error('--model and --revision must be supplied together')
if args.model:
    import re
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',args.model) or not re.fullmatch(r'[a-f0-9]{40}',args.revision):
        arguments.error('A repository name and exact commit hash are required')
    selected={'model_id':args.model,'revision':args.revision}
with httpx.Client(follow_redirects=True,timeout=60) as client:
    info=client.get(f"https://huggingface.co/api/models/{selected['model_id']}/revision/{selected['revision']}",params={'blobs':True})
    info.raise_for_status()
    info=info.json()
    if info.get('gated') or info.get('private'):
        raise RuntimeError('This downloader only supports public, ungated checkpoints')
    files=[item for item in info['siblings'] if item['rfilename'].endswith('.safetensors')]
    if len(files)!=1:
        raise RuntimeError('Use the standard Hub downloader for a sharded checkpoint')
    checkpoint=files[0]
    total=checkpoint['size']
    expected=checkpoint['lfs']['sha256']
    official=f"https://huggingface.co/{selected['model_id']}/resolve/{selected['revision']}/{checkpoint['rfilename']}?download=true"
    response=client.head(official)
    response.raise_for_status()
    resolved=str(response.url)

cache=ROOT/'.cache'/'huggingface'/'hub'/('models--'+selected['model_id'].replace('/','--'))
destination=cache/'snapshots'/selected['revision']/checkpoint['rfilename']
destination.parent.mkdir(parents=True,exist_ok=True)
if destination.exists():
    with destination.open('rb') as stream:
        actual=hashlib.file_digest(stream,'sha256').hexdigest()
    if actual!=expected:
        raise RuntimeError('An existing checkpoint does not match its official SHA-256; it was not overwritten')
    print(json.dumps({'status':'already_verified','model_id':selected['model_id'],'bytes':total,'sha256':actual}),flush=True)
    raise SystemExit(0)
temporary=destination.with_suffix('.parallel-download')
progress=temporary.with_suffix('.progress.json')
chunk_size=8*1024*1024
completed=set(json.loads(progress.read_text()) if progress.exists() and temporary.exists() else [])
if not temporary.exists():
    with temporary.open('wb') as stream:
        stream.truncate(total)
started=time.perf_counter()
timeout=httpx.Timeout(60,connect=20)
client=httpx.Client(timeout=timeout,limits=httpx.Limits(max_connections=6,max_keepalive_connections=6))
def download(start):
    end=min(total-1,start+chunk_size-1)
    for attempt in range(4):
        try:
            with client.stream('GET',resolved,headers={'Range':f'bytes={start}-{end}'}) as response:
                response.raise_for_status()
                if response.status_code!=206 or not response.headers.get('content-range','').startswith(f'bytes {start}-'):
                    raise RuntimeError('The server did not honor the requested checkpoint byte range')
                written=0
                with temporary.open('r+b',buffering=0) as stream:
                    stream.seek(start)
                    for block in response.iter_bytes(1024*1024):
                        if written+len(block)>end-start+1:
                            raise RuntimeError('Checkpoint byte range is larger than requested')
                        stream.write(block)
                        written+=len(block)
                if written!=end-start+1:
                    raise RuntimeError('Checkpoint byte range is incomplete')
                return start
        except Exception:
            if attempt==3:
                raise
            time.sleep(1+attempt)
try:
    with ThreadPoolExecutor(max_workers=6) as pool:
        pending=[pool.submit(download,start) for start in range(0,total,chunk_size) if start not in completed]
        for future in as_completed(pending):
            completed.add(future.result())
            progress.write_text(json.dumps(sorted(completed)))
            if len(completed)%12==0 or len(completed)==len(range(0,total,chunk_size)):
                print(json.dumps({'completed_chunks':len(completed),'total_chunks':len(range(0,total,chunk_size)),
                                  'elapsed_seconds':round(time.perf_counter()-started,1)}),flush=True)
finally:
    client.close()
with temporary.open('rb') as stream:
    actual=hashlib.file_digest(stream,'sha256').hexdigest()
if actual!=expected:
    raise RuntimeError('Downloaded checkpoint SHA-256 does not match the official Hub LFS hash')
if destination.exists():
    raise RuntimeError('A checkpoint already exists at the destination; it was not overwritten')
temporary.replace(destination)
blob=cache/'blobs'/expected
blob.parent.mkdir(exist_ok=True)
if not blob.exists():
    os.link(destination,blob)
print(json.dumps({'status':'verified','bytes':total,'sha256':actual,'checkpoint':str(destination)},indent=2),flush=True)
