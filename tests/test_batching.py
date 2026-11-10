import pytest

from backend.evaluation.batching import pack_batches
from backend.evaluation.latency import latency_metrics
from backend.modeling import trim_generated_tokens


def test_packing_covers_every_id_without_using_reference_answers():
    rows=[{'benchmark_id':str(i),'language':'en' if i<5 else 'ta','reference_answer':'unused'} for i in range(8)]
    lengths=[100,120,1000,1500,5000,200,220,250]
    batches=list(pack_batches(rows,lengths,maximum_size=4,token_budget=2048))
    assert sorted(row['benchmark_id'] for batch in batches for row in batch)==[str(i) for i in range(8)]
    for batch in batches:
        assert len({row['language'] for row in batch})==1
        assert len(batch)<=4
        if len(batch)>1:
            assert max(lengths[int(row['benchmark_id'])] for row in batch)*len(batch)<=2048


def test_batch_throughput_counts_shared_elapsed_generation_once():
    rows=[{'generation_batch_id':'same-batch','generation_batch_seconds':2.,'generation_seconds':2.,
           'output_tokens':10,'total_seconds':2.2,'retrieval_seconds':0.} for _ in range(4)]
    result=latency_metrics(rows)
    assert result['throughput']['value']==20
    assert result['throughput']['denominator']==2
    assert result['total_seconds']['mean']==2.2


def test_eos_padding_is_excluded_from_generated_token_counts():
    assert trim_generated_tokens([10,11,99,0,0],{99})==[10,11,99]
    assert trim_generated_tokens([10,11],{99})==[10,11]


def test_batch_metadata_records_actual_batch_duration(prediction):
    from backend.evaluation.inference_runner import infer_benchmark_batch
    class Engine:
        def generate_batch(self,rows):
            return [{'generated_answer':'fixture','abstained':False,'input_tokens':3,'output_tokens':1,'generation_seconds':.1} for _ in rows],.1
    rows=[{**prediction,'benchmark_id':str(i)} for i in range(2)]
    outputs=infer_benchmark_batch(Engine(),rows,experiment='A')
    assert outputs[0]['generation_batch_id']==outputs[1]['generation_batch_id']
    assert all(output['batch_size']==2 for output in outputs)
    assert all(output['generation_batch_seconds']==.1 for output in outputs)
