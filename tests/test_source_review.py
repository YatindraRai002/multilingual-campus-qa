from datetime import datetime,timezone

import pytest


@pytest.fixture
def source_row(tmp_path,monkeypatch):
    from backend import college
    from backend.settings import write_json
    monkeypatch.setattr(college,'COLLEGE',tmp_path)
    folder=tmp_path/'documents'/'isolated-source'
    folder.mkdir(parents=True)
    write_json(folder/'metadata.json',{'source_url':'https://www.srmist.edu.in/','document_version':'fixture-version'})
    (folder/'text.txt').write_text('The unit library opens at noon.',encoding='utf-8')
    return {'faq_id':'isolated-fixture','canonical_question':'When does the unit library open?','language':'en',
        'answer':'The unit library opens at noon.','category':'unit-test','source_url':'https://www.srmist.edu.in/',
        'source_title':'Isolated source fixture','source_document_id':'isolated-source','verification_status':'source_verified',
        'verified_at':datetime.now(timezone.utc).isoformat(),'verified_by':'Codex (AI fixture)',
        'document_version':'fixture-version','translation_status':'native','evidence_quote':'The unit library opens at noon.',
        'reviewer_kind':'ai','review_method':'official_snapshot_ai_review','human_review_status':'pending',
        'review_notes':'Unit-only source quotation and meaning review; no research data.'}


def test_ai_source_review_is_explicit_and_does_not_become_human_review(source_row):
    from backend.college import validate_faq
    result=validate_faq(source_row)
    assert result['verification_status']=='source_verified'
    assert result['reviewer_kind']=='ai' and result['human_review_status']=='pending'


@pytest.mark.parametrize('changes,match',[
    ({'reviewer_kind':None},'provenance'),
    ({'human_review_status':'reviewed'},'pending human'),
    ({'translation_status':'machine_translation_unreviewed'},'Unreviewed'),
    ({'verification_status':'human_verified'},'human reviewer'),
])
def test_missing_or_misleading_review_provenance_is_rejected(source_row,changes,match):
    from backend.college import validate_faq
    with pytest.raises(ValueError,match=match):
        validate_faq({**source_row,**changes})


def test_ai_reviewed_translation_keeps_its_identity(source_row):
    from backend.college import validate_faq
    result=validate_faq({**source_row,'language':'hi','canonical_question':'परीक्षण पुस्तकालय कब खुलता है?',
        'answer':'परीक्षण पुस्तकालय दोपहर में खुलता है।','translation_status':'machine_translation_ai_reviewed'})
    assert result['translation_status']=='machine_translation_ai_reviewed'
    assert result['human_review_status']=='pending'


def test_retrieval_includes_declared_verified_sources_and_excludes_unreviewed_records(tmp_path):
    pytest.importorskip('chromadb')
    from backend.retrieval import _client,Retriever
    client=_client(tmp_path/'isolated-review-vectors')
    collection=client.create_collection('isolated_review_policy',embedding_function=None,metadata={'hnsw:space':'cosine'})
    kinds=['source_verified','human_verified','pending']
    now=datetime.now(timezone.utc)
    collection.upsert(ids=kinds,embeddings=[[1.,0.,0.]]*3,documents=['unit fixture']*3,
        metadatas=[{'verification_status':kind,'source_document_id':kind,'verified_at':now.isoformat(),'language':'en'} for kind in kinds])
    class Embedder:
        def encode(self,*args,**kwargs): return [[1.,0.,0.]]
    retriever=Retriever.__new__(Retriever)
    retriever.collection=collection;retriever.embedder=Embedder();retriever.as_of=now
    retriever.settings={'top_k':4,'max_source_age_days':180,'max_cosine_distance':2.}
    hits,_=retriever.query('unit fixture')
    assert {hit['verification_status'] for hit in hits}=={'human_verified','source_verified'}
    retriever.settings['accepted_verification_statuses']=['human_verified']
    hits,_=retriever.query('unit fixture')
    assert [hit['verification_status'] for hit in hits]==['human_verified']
    retriever.settings['accepted_verification_statuses']=['pending']
    with pytest.raises(ValueError,match='Only explicit'):
        retriever.query('unit fixture')
