import pytest


def test_human_evidence_uses_original_sealed_corpus_and_detects_changes(tmp_path,monkeypatch,database):
    from backend import review
    from backend.modeling import PrerequisiteError
    from backend.settings import digest,write_json,write_jsonl
    monkeypatch.setattr(review,'COLLEGE',tmp_path)
    test_version,corpus_version='a'*16,'b'*16
    row={'source_document_id':'fixture-doc','source_url':'https://www.srmist.edu.in/',
         'document_version':'unit-version','source_title':'Unit source','language':'ta','answer':'தமிழ்',
         'canonical_question':'இது என்ன?','verification_status':'human_verified','evidence_quote':'unit quote',
         'verified_by':'unit reviewer','verified_at':'2026-01-01T00:00:00+00:00'}
    write_json(tmp_path/'test_versions'/test_version/'manifest.json',{'corpus_version':corpus_version})
    folder=tmp_path/'versions'/corpus_version
    write_jsonl(folder/'faq.jsonl',[row])
    write_json(folder/'manifest.json',{'records_sha256':digest([row])})
    write_json(tmp_path/'documents'/'fixture-doc'/'metadata.json',row)
    # The current corpus may differ; human review must use this experiment's original version.
    write_json(tmp_path/'manifest.json',{'version':'c'*16})
    run=database.create_run(track='campus',experiment='A',dataset_version=test_version,
        evaluation_fingerprint='unit-only',configuration={},total=1)
    prediction={'run_id':run,'language':'ta','context':'','relevant_document_ids':['fixture-doc']}
    evidence=review.reference_evidence(database,prediction)
    assert evidence['supplied_document_ids']==[]
    assert evidence['reference_sources'][0]['answer']=='தமிழ்'
    write_jsonl(folder/'faq.jsonl',[{**row,'answer':'tampered'}])
    with pytest.raises(PrerequisiteError,match='checksum'):
        review.reference_evidence(database,prediction)
