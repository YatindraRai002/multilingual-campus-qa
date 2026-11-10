from backend.evaluation.latency import latency_metrics


def test_shared_batch_times_are_one_independent_measurement():
    rows=[{'generation_batch_id':'one-batch','generation_batch_seconds':2.,'generation_seconds':2.,
           'output_tokens':10,'total_seconds':2.2,'retrieval_seconds':0.} for _ in range(4)]
    result=latency_metrics(rows)
    assert result['total_seconds']['count']==4
    assert result['total_seconds']['measurement_clusters']==1
    assert result['total_seconds']['mean_ci'] is None
    assert result['throughput']['confidence_interval'] is None


def test_unequal_batch_sizes_preserve_response_weighting_and_actual_generation_duration():
    first={'generation_batch_id':'a','generation_batch_seconds':1.,'generation_seconds':1.,
           'output_tokens':10,'total_seconds':1.,'retrieval_seconds':0.}
    second={'generation_batch_id':'b','generation_batch_seconds':3.,'generation_seconds':3.,
            'output_tokens':20,'total_seconds':3.,'retrieval_seconds':0.}
    result=latency_metrics([first,second,second,second])
    assert result['total_seconds']['mean']==2.5
    interval=result['total_seconds']['mean_ci']
    assert interval['lower']==1 and interval['upper']==3
    assert interval['resampling_unit']=='generation_batch'
    assert result['throughput']['value']==17.5  # 70 real tokens / (1+3) measured seconds
    interval=result['throughput']['confidence_interval']
    assert interval['lower']==10 and interval['upper']==20


def test_unbatched_requests_keep_response_resampling():
    result=latency_metrics([{'total_seconds':1.,'generation_seconds':1.,'output_tokens':10},
                            {'total_seconds':3.,'generation_seconds':3.,'output_tokens':30}])
    assert result['total_seconds']['mean_ci']['resampling_unit']=='response'


def test_mixed_metric_definitions_cannot_be_compared(database):
    import pytest
    from backend.experiments import compare_runs
    ids=[]
    for letter,version in [('A','old-fixture'),('B','new-fixture')]:
        run=database.create_run(track='benchmark',experiment=letter,dataset_version='unit-only',
            evaluation_fingerprint='same-unit-only',configuration={},total=1)
        database.store_metrics(run,{'definitions_version':version})
        ids.append(run)
    with pytest.raises(ValueError,match='metric definitions'):
        compare_runs(database,ids)
