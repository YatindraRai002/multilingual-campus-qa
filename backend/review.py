"""Human-only reference evidence. Nothing here is supplied to model generation."""
import re

from backend.college import COLLEGE,is_verified,official_url
from backend.modeling import PrerequisiteError
from backend.settings import digest,read_json,read_jsonl


def reference_evidence(database,prediction):
    run=database.run(prediction['run_id'])
    supplied=set(prediction.get('context_document_ids',[]))
    if prediction.get('source_document_id'):
        supplied.add(prediction['source_document_id'])
    result={'supplied_context':prediction.get('context',''),
            'supplied_document_ids':sorted(supplied),
            'reference_document_ids':prediction.get('relevant_document_ids',[]),'reference_sources':[],
            'policy':'Human factuality judgments use authoritative reference evidence for all A/B/C/D arms; model access to evidence is recorded separately.'}
    if run['track']!='campus':
        return result
    version=run['dataset_version']
    if not re.fullmatch(r'[a-f0-9]{16}',version):
        raise PrerequisiteError('The sealed campus test version is unavailable for reference review')
    test=read_json(COLLEGE/'test_versions'/version/'manifest.json')
    corpus_version=(test or {}).get('corpus_version','')
    if not re.fullmatch(r'[a-f0-9]{16}',corpus_version):
        raise PrerequisiteError('The original reference corpus is missing')
    folder=COLLEGE/'versions'/corpus_version
    manifest=read_json(folder/'manifest.json')
    records=read_jsonl(folder/'faq.jsonl')
    if not manifest or digest(records)!=manifest['records_sha256']:
        raise PrerequisiteError('The original reference corpus checksum does not match')
    wanted=set(result['reference_document_ids'])|supplied
    candidates=[r for r in records if r['source_document_id'] in wanted and is_verified(r)]
    candidates.sort(key=lambda r:r['language']!=prediction['language'])
    seen=set()
    for row in candidates:
        identifier=row['source_document_id']
        if identifier in seen:
            continue
        if not re.fullmatch(r'[a-zA-Z0-9_-]{1,200}',identifier) or not official_url(row['source_url']):
            raise PrerequisiteError('An invalid official reference source was recorded')
        source=read_json(COLLEGE/'documents'/identifier/'metadata.json')
        if not source or source['source_url']!=row['source_url'] or source['document_version']!=row['document_version']:
            raise PrerequisiteError('The original official reference snapshot is missing or differs')
        result['reference_sources'].append({key:row.get(key) for key in ('source_document_id','source_url','source_title',
            'document_version','evidence_quote','canonical_question','answer','language','verified_by','verified_at',
            'reviewer_kind','human_review_status','translation_status')})
        seen.add(identifier)
    return result
