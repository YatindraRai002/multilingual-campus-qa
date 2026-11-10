"""Bundle sources, reviewed campus records and provenance without runtime or weights."""
import json
import hashlib
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
output = root/'results'/'campusqa-source.zip'
output.parent.mkdir(exist_ok=True)
files = []
for name in ['backend','frontend','config','docs','scripts','notebooks','tests']:
    files += [p for p in (root/name).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc']
for name in ['README.md','RESEARCH_DRAFT.md','pyproject.toml','requirements.txt','requirements-ml.txt','requirements-local-lock.txt','package.json','package-lock.json','playwright.config.js','.gitignore','.gitattributes']:
    if (root/name).is_file():
        files.append(root/name)
# Deliberate allowlist: reviewed excerpts and sealed records, never raw web pages,
# private runtime stores, caches, model weights or the full prediction corpus.
campus = root/'data'/'college_faq'
for name in ['manifest.json','test_manifest.json','ingestion_manifest.json','curation_manifest.json',
             'retrieval_validation_manifest.json','pilot_seal.json','followup_seal.json']:
    if (campus/name).is_file():
        files.append(campus/name)
for folder in ['curation','embedding_evaluation']:
    files.extend((campus/folder).glob('*.json'))
for folder,versions in {
    'versions':['652d19bfd9f0b4cc','b07405a784a7045c'],
    'test_versions':['a75705ed443380de','29ed6c44573105ff'],
    'curation_versions':['068baf91-6d5a-48be-bd23-0cbc54f63bd2','406c2868-079d-4927-8d2b-4b53326eb3bf'],
}.items():
    for version in versions:
        files.extend(p for p in (campus/folder/version).glob('*') if p.is_file() and p.suffix in {'.json','.jsonl'})
for version in ['d7d31923b9ecac7f','6e044fab88609b53']:
    if (campus/'ingestion'/f'{version}.json').is_file():
        files.append(campus/'ingestion'/f'{version}.json')
with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(set(files)):
        archive.write(path,path.relative_to(root).as_posix())
    expected = root/'data'/'benchmark'/'manifest.json'
    if expected.exists():
        archive.write(expected,'handoff/expected_benchmark_manifest.json')
    for name in ['acquisition.json','supplemental_report.json']:
        path = root/'data'/'benchmark'/name
        if path.is_file():
            archive.write(path,'handoff/benchmark_'+name)
    for name in ['final-model-validation.json','validation-local-profile.json','final-api-validation.json',
                 'final-session-cleanup.json','reproduction-check.json',
                 'campus-embedding-selection.json','campus-persistent-retrieval-validation.json']:
        path = root/'results'/name
        if path.is_file():
            archive.write(path,'handoff/'+name)
    for folder in ['citation-policy-followup','retrieval_validation']:
        for path in sorted((root/'results'/folder).glob('*.json')):
            archive.write(path,'handoff/'+folder+'/'+path.name)
    interface_audit = root/'handoff'/'chat-interface-validation.json'
    if interface_audit.is_file():
        archive.write(interface_audit,'handoff/chat-interface-validation.json')
with zipfile.ZipFile(output) as archive:
    names = archive.namelist()
    assert len(names) == len(set(names))
    assert archive.testzip() is None
    assert not any(part in {'.cache','.venv','node_modules','documents','chroma','models'}
                   for name in names for part in Path(name).parts)
    assert not any(name.endswith(('.safetensors','.sqlite3','.env')) or name.endswith('/predictions.jsonl') for name in names)
manifest = {'archive':str(output),'bytes':output.stat().st_size,'source_only':True,
            'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'files':len(names),
            'campus_curation_included':True,'raw_source_archives_included':False,
            'benchmark_records_included':False,'pinned_acquisition_manifests_included':True,
            'model_weights_or_adapter_included':False,'runtime_database_or_chroma_included':False}
(root/'results'/'source-bundle-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps(manifest,indent=2))
