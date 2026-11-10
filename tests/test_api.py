import pytest
from fastapi.testclient import TestClient

from backend import main


@pytest.fixture
def client(monkeypatch,database):
    monkeypatch.setattr(main,"Database",lambda:database)
    monkeypatch.setattr(main,'apply_inference_memory_policy',lambda policy:{'isolated_fixture':True})
    with TestClient(main.app) as client:
        yield client


def test_dashboard_and_required_read_endpoints(client):
    assert client.get('/').status_code == 200
    assert 'CampusQA' in client.get('/').text
    for path in ['/api/health','/api/system','/api/datasets/summary','/api/datasets/languages','/api/models',
                 '/api/experiments','/api/college-faq/summary','/api/languages/metrics','/api/training','/api/docs']:
        assert client.get(path).status_code == 200,path
    assert client.get('/api/experiments').json()['runs'] == []
    assert client.get('/api/experiments/not-a-run').status_code == 404


def test_evaluation_validates_track_and_keeps_blocked_jobs_out_of_results(client,monkeypatch):
    def blocked(*args,**kwargs):
        from backend.modeling import PrerequisiteError
        raise PrerequisiteError('4 GiB fixture GPU is too small; not a research run')
    monkeypatch.setattr(main,'submit_evaluation',blocked)
    response = client.post('/api/evaluation/run',json={'track':'benchmark','experiment':'A'})
    assert response.status_code == 409
    assert response.json()['status'] == 'prerequisites_missing'
    assert client.get('/api/experiments').json()['count'] == 0
    assert client.post('/api/evaluation/run',json={'track':'invalid','experiment':'A'}).status_code == 422


def test_host_check_and_report_path_validation(client):
    assert client.get('/api/health',headers={'host':'untrusted.example'}).status_code == 400
    assert client.get('/api/docs/unknown.md').status_code == 404
    assert client.get('/api/datasets/records?split=test').status_code == 422


@pytest.mark.parametrize('status,expected_status',[('completed',200),('failed',422)])
def test_chat_releases_model_before_gpu_lock_on_success_and_error(client,monkeypatch,tmp_path,status,expected_status):
    from filelock import FileLock,Timeout
    path=tmp_path/'isolated-chat-gpu.lock'
    monkeypatch.setattr(main,'gpu_lock',lambda:FileLock(path))
    closed=[]
    class Engine:
        loading_seconds=0.0
        def __init__(self,*args): pass
        def close(self):
            with pytest.raises(Timeout):
                FileLock(path).acquire(timeout=0)
            closed.append(True)
    monkeypatch.setattr(main,'QwenEngine',Engine)
    monkeypatch.setattr(main,'infer_record',lambda *args,**kwargs:{'evaluation_status':status,
        'generated_answer':'Isolated fixture only','error':'Isolated forced inference error'})
    response=client.post('/api/chat',json={'question':'Where is the fixture?','language':'en','experiment':'A'})
    assert response.status_code==expected_status
    assert closed==[True]
    with FileLock(path).acquire(timeout=0):
        pass


def test_annotation_is_real_evidence_and_recomputes_metrics(client,database,prediction,monkeypatch,tmp_path):
    from backend import reporting
    (tmp_path/'docs').mkdir()
    monkeypatch.setattr(reporting,'ROOT',tmp_path)
    run = database.create_run(track='benchmark',experiment='A',dataset_version='test-fixture',evaluation_fingerprint='fixture',configuration={},total=1)
    database.transition(run,'running')
    prediction_id = database.add_prediction(run,prediction)
    body = {'reviewer':'unit reviewer','correct':True,'claims':[{'text':'A test fact','supported':True,'evidence_document_ids':['unknown']}],
            'claim_inventory_complete':True,'notes':'isolated unit fixture'}
    assert client.post(f'/api/predictions/{prediction_id}/annotations',json=body).status_code == 422
    body['claims'][0]['evidence_document_ids'] = ['fixture-doc']
    assert client.post(f'/api/predictions/{prediction_id}/annotations',json=body).status_code == 200
    calculated = client.get(f'/api/experiments/{run}/metrics').json()
    assert calculated['populations']['unit-fixture-not-research']['languages']['en']['accuracy']['value'] == 100
    assert client.get(f'/api/experiments/{run}/export?format=json').json()['run']['run_id'] == run
    assert client.get(f'/api/experiments/{run}/export?format=csv').status_code == 200


def test_closed_book_facts_can_use_official_reference_evidence(client,database,prediction,monkeypatch,tmp_path):
    from backend import reporting
    monkeypatch.setattr(reporting,'ROOT',tmp_path)
    run=database.create_run(track='campus',experiment='A',dataset_version='unit-fixture',
        evaluation_fingerprint='unit-fixture',configuration={},total=1)
    database.transition(run,'running')
    row={**prediction,'context':'','source_document_id':None,'context_document_ids':[],
         'relevant_document_ids':['official-reference-fixture']}
    identifier=database.add_prediction(run,row)
    body={'reviewer':'unit reviewer','correct':True,'claims':[{'text':'A fixture fact','supported':True,
        'evidence_document_ids':['official-reference-fixture']}],'claim_inventory_complete':True}
    response=client.post(f'/api/predictions/{identifier}/annotations',json=body)
    assert response.status_code==200
    group=database.metrics(run)['populations']['unit-fixture-not-research']['languages']['en']
    assert group['accuracy']['value']==100 and group['hallucination_incidence']['value']==0


def test_answerable_abstention_rejects_correct_annotation_and_exposes_evidence_ids(client,database,prediction):
    run=database.create_run(track='benchmark',experiment='A',dataset_version='unit-fixture',
        evaluation_fingerprint='unit-fixture',configuration={},total=1)
    database.transition(run,'running')
    identifier=database.add_prediction(run,{**prediction,'abstained':True,'generated_answer':'[ABSTAIN]'})
    response=client.post(f'/api/predictions/{identifier}/annotations',json={'reviewer':'unit reviewer',
        'correct':True,'claims':[],'claim_inventory_complete':True})
    assert response.status_code==422
    evidence=client.get(f'/api/predictions/{identifier}/evidence')
    assert evidence.status_code==200
    assert evidence.json()['supplied_document_ids']==['fixture-doc']
    assert evidence.json()['supplied_context']==prediction['context']
