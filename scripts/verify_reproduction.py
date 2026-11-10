"""Rebuild the actual acquired benchmark in a clean workspace and compare sealed checksums."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
expected = json.loads((root/'data/benchmark/manifest.json').read_text(encoding='utf-8'))
acquisition = json.loads((root/'data/benchmark/acquisition.json').read_text(encoding='utf-8'))
with tempfile.TemporaryDirectory(prefix='reproduce-',dir=root/'.cache') as directory:
    target = Path(directory).resolve()
    assert target.is_relative_to(root.resolve()) and target.parent == (root/'.cache').resolve()
    shutil.copytree(root/'config',target/'config')
    (target/'docs').mkdir()
    for artifact in acquisition['artifacts']:
        output = target/artifact['path']
        output.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(root/artifact['path'],output)
    shutil.copy2(root/'data/benchmark/acquisition.json',target/'data/benchmark/acquisition.json')
    supplement = root/'data/benchmark/supplemental_training.jsonl'
    if supplement.exists():
        shutil.copy2(supplement,target/'data/benchmark/supplemental_training.jsonl')
    process = subprocess.run([sys.executable,'-m','backend.cli','prepare'],cwd=root,
            env={**os.environ,'CAMPUSQA_ROOT':str(target)},capture_output=True,text=True)
    if process.returncode:
        raise RuntimeError(process.stderr)
    actual = json.loads(process.stdout)
    assert actual['version'] == expected['version'],(actual['version'],expected['version'])
    assert actual['split_checksums'] == expected['split_checksums'],'Rebuilt split checksums differ'
print(json.dumps({'status':'passed','dataset_version':expected['version'],'split_checksums':expected['split_checksums'],
                  'fresh_workspace_reconstruction':True},indent=2))
