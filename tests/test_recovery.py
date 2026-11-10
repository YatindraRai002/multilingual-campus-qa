from copy import deepcopy
import os

import pytest

from backend.settings import digest


@pytest.fixture
def recovery_source(database,prediction):
    rows=[{'benchmark_id':key,'question':f'Where is fixture {key}?','context':prediction['context'],
           'reference_answer':'library','language':'en','source_dataset':'isolated-recovery-fixture'} for key in 'abcd']
    model={'model_id':'isolated-no-weights','revision':'unit-revision','prompt_version':'fixture-v1',
           'generation':{'max_new_tokens':8,'do_sample':False},'max_input_tokens':128,'seed':42}
    configuration={'model_id':model['model_id'],'model_revision':model['revision'],'prompt_version':model['prompt_version'],
        'generation':model['generation'],'max_input_tokens':128,'seed':42,'adapter':None,'ingestion':None,
        'limit_per_language':None,'context_condition':'supplied_benchmark_context','test_ids':list('abcd'),
        'inference_execution':{'maximum_batch_size':1,'batch_token_budget':128},
        'evidence_as_of':'2026-11-07T00:00:00+00:00'}
    fingerprint=digest([{key:r[key] for key in ['benchmark_id','question','reference_answer','context','language']} for r in rows])
    source=database.create_run(track='benchmark',experiment='A',dataset_version='isolated-version',
        evaluation_fingerprint=fingerprint,configuration=configuration,total=4)
    database.transition(source,'running')
    for row in rows[:2]:
        database.add_prediction(source,{**prediction,'question_id':row['benchmark_id'],'question':row['question'],
            'reference_answer':'library','reference_answers':['library'],'generated_answer':'library',
            'source_dataset':'isolated-recovery-fixture'})
    return source,configuration,fingerprint,model,rows


def selection(database,source,configuration,fingerprint):
    from backend.recovery import recovery_selection
    return recovery_selection(database,source,configuration=configuration,fingerprint=fingerprint,
        dataset_version='isolated-version',track='benchmark',experiment='A')


def test_active_workers_and_changed_generation_cannot_be_recovered(database,recovery_source):
    source,configuration,fingerprint,_,_=recovery_source
    with pytest.raises(Exception,match='active runs cannot be copied'):
        selection(database,source,configuration,fingerprint)
    database.transition(source,'interrupted')
    changed=deepcopy(configuration);changed['generation']['max_new_tokens']=9
    with pytest.raises(Exception,match='frozen configuration: generation'):
        selection(database,source,changed,fingerprint)
    database.register_worker(source,os.getpid())
    with pytest.raises(Exception,match='original worker must exit'):
        selection(database,source,configuration,fingerprint)


def test_partial_generation_batch_is_retained_in_history_but_recomputed(database,recovery_source,prediction):
    source,configuration,fingerprint,_,_=recovery_source
    # Existing a/b are complete single requests; c is only half of a two-request batch.
    database.add_prediction(source,{**prediction,'question_id':'c','generation_batch_id':'partial-fixture',
                                   'batch_size':2,'generation_batch_seconds':1.0})
    database.transition(source,'interrupted')
    descriptor,rows=selection(database,source,configuration,fingerprint)
    assert [row['question_id'] for row in rows]==['a','b']
    assert descriptor['reused_count']==2 and descriptor['pending_count']==2
    assert descriptor['excluded_incomplete_or_failed_question_ids']==['c']
    assert database.run(source)['completed']==3


def test_recovery_preserves_source_and_generates_only_pending_questions(tmp_path,monkeypatch,database,recovery_source):
    from backend import experiments,reporting
    from backend.evaluation import inference_runner
    from backend.recovery import restore_observations
    source,configuration,fingerprint,model,rows=recovery_source
    database.transition(source,'interrupted')
    originals=database.predictions(source,limit=100)
    database.annotate(originals[0]['prediction_id'],'isolated reviewer',{'correct':True,'claims':[],
        'claim_inventory_complete':True})
    descriptor,_=selection(database,source,configuration,fingerprint)
    configuration=deepcopy(configuration)
    configuration.update(recovery=descriptor,runtime_memory_policy={'version':'bounded-cuda-cache-v1',
        'device':0,'per_process_memory_fraction':.75})
    recovered=database.create_run(track='benchmark',experiment='A',dataset_version='isolated-version',
        evaluation_fingerprint=fingerprint,configuration=configuration,total=4)
    # A tampered snapshot is rejected before copying even one observation.
    bad=database.run(recovered);bad['configuration']['recovery']['observations_sha256']='tampered'
    with pytest.raises(Exception,match='differ from the sealed recovery manifest'):
        restore_observations(database,bad,lambda row:pytest.fail('No tampered observation may be copied'))
    assert database.run(recovered)['completed']==0
    monkeypatch.setattr(experiments,'ROOT',tmp_path)
    monkeypatch.setattr(reporting,'ROOT',tmp_path)
    monkeypatch.setattr(experiments,'Database',lambda:database)
    monkeypatch.setattr(experiments,'config',lambda name:model)
    monkeypatch.setattr(inference_runner,'config',lambda name:model)
    monkeypatch.setattr(experiments,'evaluation_rows',lambda *args:({'version':'isolated-version'},rows))
    monkeypatch.setattr(experiments,'apply_inference_memory_policy',lambda policy:{'isolated_fixture':True})
    generated=[]
    class Engine:
        loading_seconds=0.0
        def __init__(self,*args): pass
        def generate(self,question,*args,**kwargs):
            generated.append(question)
            return {'generated_answer':'library','abstained':False,'input_tokens':4,'output_tokens':1,
                    'generation_seconds':.001}
        def close(self):
            assert not experiments.gpu_available()
            assert database.run(recovered)['status']=='running'
    monkeypatch.setattr(experiments,'QwenEngine',Engine)
    experiments.result_folder(database.run(recovered)).mkdir(parents=True)
    result=experiments.execute_run(recovered)
    assert result['status']=='completed' and result['completed']==result['total']==4
    assert generated==[rows[2]['question'],rows[3]['question']]
    assert database.run(source)['status']=='interrupted' and database.run(source)['completed']==2
    saved=database.predictions(recovered,limit=100)
    assert all(row['annotation'] is None for row in saved)
    inherited=[row for row in saved if row.get('recovery_origin')]
    assert len(inherited)==2
    assert {row['recovery_origin']['source_prediction_id'] for row in inherited}=={r['prediction_id'] for r in originals}
    assert not {row['prediction_id'] for row in saved}&{r['prediction_id'] for r in originals}
    assert experiments.gpu_available()
    report=(tmp_path/'docs'/'EVALUATION_REPORT.md').read_text(encoding='utf-8')
    assert '2 saved observations reused' in report and source in report
