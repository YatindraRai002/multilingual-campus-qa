"""Cache public retrieval candidates without choosing one or accessing campus data."""
import json
from pathlib import PurePosixPath
import subprocess
import sys

import httpx

from backend.settings import ROOT,config,utcnow,write_json


def main():
    from huggingface_hub import hf_hub_download
    settings=config('retrieval')
    result=[]
    with httpx.Client(timeout=60,follow_redirects=True) as client:
        for name in settings['candidate_models']:
            revision=settings['candidate_revisions'][name]
            response=client.get(f'https://huggingface.co/api/models/{name}/revision/{revision}',params={'blobs':'true'})
            response.raise_for_status()
            metadata=response.json()
            if metadata.get('private') or metadata.get('gated') or metadata['sha']!=revision:
                raise RuntimeError('Only the configured public, pinned embedding models may be cached')
            subprocess.run([sys.executable,str(ROOT/'scripts'/'download_checkpoint.py'),
                '--model',name,'--revision',revision],cwd=ROOT,check=True)
            files=[]
            for entry in metadata['siblings']:
                path=PurePosixPath(entry['rfilename'])
                if path.parts[0] in {'onnx','openvino'} or path.suffix not in {'.json','.txt','.model','.md'}:
                    continue
                # The standard Hub downloader records the pinned revision and cache metadata.
                hf_hub_download(repo_id=name,filename=path.as_posix(),revision=revision)
                files.append(path.as_posix())
            result.append({'model_id':name,'revision':revision,'license':metadata.get('cardData',{}).get('license'),
                'cached_at':utcnow(),'configuration_files':files,'status':'cached_not_evaluated'})
            print(json.dumps(result[-1]),flush=True)
    write_json(ROOT/'results'/'embedding_cache.json',result)


if __name__=='__main__':
    main()
