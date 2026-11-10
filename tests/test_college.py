from datetime import datetime, timezone

import pytest

from backend.college import official_url, require_benchmark_complete
from backend.modeling import PrerequisiteError
from backend.experiments import compare_runs


@pytest.mark.parametrize('url',["http://www.srmist.edu.in/","https://www.srmist.edu.in.attacker.example/",
                               "https://127.0.0.1/","https://name:pass@www.srmist.edu.in/"])
def test_source_allowlist_blocks_non_official_endpoints(url):
    assert not official_url(url)


def test_official_url_and_phase_gate(database):
    assert official_url('https://www.srmist.edu.in/')
    with pytest.raises(PrerequisiteError):
        require_benchmark_complete(database)


def test_unmatched_evaluation_populations_are_not_comparable(database):
    ids = [database.create_run(track='benchmark',experiment=letter,dataset_version='same-version',
            evaluation_fingerprint=fingerprint,configuration={},total=1)
           for letter,fingerprint in [('A','test-set-1'),('B','test-set-2')]]
    with pytest.raises(ValueError,match='evaluation_fingerprint'):
        compare_runs(database,ids)


def test_faq_review_requires_source_snapshot_and_quote(tmp_path,monkeypatch):
    from backend import college
    from backend.settings import write_json
    monkeypatch.setattr(college,'COLLEGE',tmp_path)
    folder = tmp_path/'documents'/'real-fixture-snapshot'
    folder.mkdir(parents=True)
    write_json(folder/'metadata.json',{'source_url':'https://www.srmist.edu.in/','document_version':'fixture-v1'})
    (folder/'text.txt').write_text('This is an isolated test source. The test library opens at noon.',encoding='utf-8')
    row = {'faq_id':'fixture-only','canonical_question':'When does the test library open?','language':'en',
           'answer':'The test library opens at noon.','category':'unit-test','source_url':'https://www.srmist.edu.in/',
           'source_title':'Isolated fixture','source_document_id':'real-fixture-snapshot','verification_status':'human_verified',
           'verified_at':datetime.now(timezone.utc).isoformat(),'verified_by':'unit reviewer','document_version':'fixture-v1',
           'translation_status':'native','evidence_quote':'The test library opens at noon.','campus':'Kattankulathur'}
    row['reviewer_kind']='human'
    assert college.validate_faq(row)['faq_id'] == 'fixture-only'
    with pytest.raises(ValueError,match='absent'):
        college.validate_faq({**row,'evidence_quote':'A made-up policy that is not in the source.'})
    with pytest.raises(ValueError,match='Unreviewed'):
        college.validate_faq({**row,'translation_status':'machine_translation_unreviewed'})


def test_changing_corpus_invalidates_live_retrieval_before_embedding_load(tmp_path,monkeypatch):
    from backend import retrieval
    from backend.settings import write_json
    monkeypatch.setattr(retrieval,'COLLEGE',tmp_path)
    write_json(tmp_path/'ingestion_manifest.json',{'corpus_version':'old'})
    write_json(tmp_path/'manifest.json',{'version':'new'})
    with pytest.raises(PrerequisiteError,match='Re-ingest'):
        retrieval.Retriever()
