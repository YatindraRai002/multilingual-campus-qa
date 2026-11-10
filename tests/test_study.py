import os
from types import SimpleNamespace

import pytest


def test_coordinator_launch_records_real_process_identity_without_a_research_score(tmp_path,monkeypatch):
    from backend import study,datasets
    monkeypatch.setattr(study,'ROOT',tmp_path)
    monkeypatch.setattr(study,'config',lambda name:{'fixture':name})
    monkeypatch.setattr(datasets,'current_manifest',lambda:{'version':'dataset-fixture'})
    monkeypatch.setattr(study.subprocess,'Popen',lambda *args,**kwargs:SimpleNamespace(pid=os.getpid()))
    state=study.launch_study(phase='benchmark')
    assert state['status']=='running' and state['stage']=='starting'
    assert state['run_ids']=={}
    assert (study.study_path(state['study_id'])/'plan.json').exists()
    with pytest.raises(Exception,match='already running'):
        study.launch_study(phase='benchmark',resume=state['study_id'])


def test_coordinator_will_not_reuse_an_evaluation_of_another_adapter_or_index():
    from backend.study import compatible_run
    model={'model_id':'test','revision':'r','generation':{},'prompt_version':'p','max_input_tokens':128,'seed':42}
    run={'status':'completed','track':'campus','experiment':'D','dataset_version':'v',
         'configuration':{'model_id':'test','model_revision':'r','generation':{},'prompt_version':'p',
                          'max_input_tokens':128,'seed':42,'limit_per_language':None,
                          'adapter':{'adapter_revision':'a1'},'ingestion':{'version':'i1'}}}
    assert compatible_run(run,'campus','D','v',model,adapter_revision='a1',ingestion_version='i1')
    assert not compatible_run(run,'campus','D','v',model,adapter_revision='a2',ingestion_version='i1')
    assert not compatible_run(run,'campus','D','v',model,adapter_revision='a1',ingestion_version='i2')
    run['status']='interrupted'
    assert not compatible_run(run,'campus','D','v',model,adapter_revision='a1',ingestion_version='i1')
    assert compatible_run(run,'campus','D','v',model,adapter_revision='a1',ingestion_version='i1',statuses=('interrupted',))
