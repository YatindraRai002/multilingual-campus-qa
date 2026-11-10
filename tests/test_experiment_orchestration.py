"""Exercise all four runner paths in a temporary store with an explicitly synthetic engine."""
from backend.settings import digest


def test_all_four_campus_configurations_persist_and_compare(tmp_path,monkeypatch,database):
    from backend import experiments,reporting,retrieval
    from backend.evaluation import inference_runner
    monkeypatch.setattr(experiments,'ROOT',tmp_path)
    monkeypatch.setattr(reporting,'ROOT',tmp_path)
    (tmp_path/'docs').mkdir()
    monkeypatch.setattr(experiments,'Database',lambda:database)
    monkeypatch.setattr(experiments,'apply_inference_memory_policy',lambda policy:{'isolated_fixture':True})
    model = {'model_id':'Qwen/Qwen2.5-7B-Instruct','revision':'unit-fixture-no-weights','prompt_version':'fixture-v1',
             'generation':{'max_new_tokens':8,'do_sample':False},'max_input_tokens':128,'seed':42}
    monkeypatch.setattr(experiments,'config',lambda name:model)
    monkeypatch.setattr(inference_runner,'config',lambda name:model)
    row = {'benchmark_id':'synthetic-only','language':'en','context':'','question':'Where is the synthetic test library?',
           'reference_answer':'campus','reference_answers':['campus'],'answerable':True,
           'source_dataset':'unit-fixture-never-research','relevant_document_ids':['fixture-doc']}
    manifest = {'version':'unit-fixture-v1'}
    monkeypatch.setattr(experiments,'evaluation_rows',lambda *args:(manifest,[row]))

    class Engine:
        loading_seconds = .001
        def __init__(self,*args):
            pass
        def generate(self,*args,**kwargs):
            return {'generated_answer':'campus [S1]' if kwargs.get('citations') else 'campus',
                    'raw_generated_answer':'synthetic fixture','abstained':False,'input_tokens':10,
                    'output_tokens':3,'generation_seconds':.001}
        def close(self):
            assert not experiments.gpu_available(), 'GPU cleanup must finish before releasing the lock'
            assert database.run(run_id)['status']=='running', 'Terminal status must not precede model cleanup'
    monkeypatch.setattr(experiments,'QwenEngine',Engine)
    adapter = {'adapter_revision':'unit-fixture-adapter','adapter_path':str(tmp_path/'unit-adapter')}
    monkeypatch.setattr(experiments,'adapter_manifest',lambda *args:adapter)

    class Retriever:
        def __init__(self,*args,**kwargs):
            pass
        def query(self,*args,**kwargs):
            return [{'source_document_id':'fixture-doc','source_url':'https://www.srmist.edu.in/',
                     'source_title':'Isolated unit source','answer':'campus'}],.0001
        def context(self,hits):
            return '[S1] The synthetic test library is on campus.',hits
    monkeypatch.setattr(retrieval,'Retriever',Retriever)

    fingerprint = digest([{key:row[key] for key in ['benchmark_id','question','reference_answer','context','language']}])
    ids = []
    for letter in 'ABCD':
        stored = {'model_id':model['model_id'],'model_revision':model['revision'],'prompt_version':model['prompt_version'],
                  'generation':model['generation'],'max_input_tokens':128,'seed':42,'test_ids':[row['benchmark_id']],
                  'adapter':adapter if letter in 'BD' else None,'limit_per_language':None,
                  'ingestion':{'configuration':{'top_k':4}} if letter in 'CD' else None,
                  'evidence_as_of':'2026-11-07T00:00:00+00:00',
                  'context_condition':'retrieved_verified_campus_evidence' if letter in 'CD' else 'closed_book_no_campus_evidence'}
        run_id = database.create_run(track='campus',experiment=letter,dataset_version=manifest['version'],
                       evaluation_fingerprint=fingerprint,configuration=stored,total=1)
        experiments.result_folder(database.run(run_id)).mkdir(parents=True)
        result = experiments.execute_run(run_id)
        assert experiments.gpu_available()
        assert result['status'] == 'completed'
        assert database.predictions(run_id)[0]['generated_answer']
        assert database.metrics(run_id)['populations']['unit-fixture-never-research']['languages']['en']['exact_match']['value'] == 100
        ids.append(run_id)
    assert len(set(ids)) == 4
    assert experiments.compare_runs(database,ids)['matched_population']
    assert (tmp_path/'docs'/'EXPERIMENT_STATUS.md').is_file()
