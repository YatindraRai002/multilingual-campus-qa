import time

import pytest

from backend.evaluation.inference_runner import infer_record
from backend.hardware import readiness
from backend.modeling import PrerequisiteError, cited_sources, messages
from backend.retrieval import chunks


def test_small_gpu_is_rejected_for_original_7b_without_model_loading(monkeypatch):
    from backend import hardware as hardware_module
    monkeypatch.setattr(hardware_module,'config',lambda name:{'model_id':'Qwen/Qwen2.5-7B-Instruct',
        'min_training_vram_gib':12,'min_inference_vram_gib':6,'recommended_training_vram_gib':16})
    hardware = {"gpu":{"name":"RTX 2050","free_vram_gib":3.5},
                "dependencies":dict.fromkeys(["torch","transformers","peft","bitsandbytes","accelerate"],"installed")}
    assert not readiness(hardware,training=True)["ready"]
    assert not readiness(hardware)["ready"]


def test_approved_local_profile_has_a_distinct_smaller_memory_gate():
    from backend.settings import config
    if config('model_config')['model_id'] != 'Qwen/Qwen2.5-1.5B-Instruct':
        pytest.skip('The active profile is the original larger-GPU study')
    hardware = {'gpu':{'name':'RTX 2050','free_vram_gib':3.5},
                'dependencies':dict.fromkeys(['torch','transformers','peft','bitsandbytes','accelerate'],'installed')}
    assert readiness(hardware,training=True)['ready']


def test_chat_prompt_preserves_target_script_and_evidence_boundaries():
    prompt = messages("நூலகம் எங்கே?","சான்று","ta",citations=True)
    assert prompt[0]["role"] == "system"
    assert "Tamil" in prompt[0]["content"]
    assert "untrusted" in prompt[0]["content"]
    assert "<evidence>" in prompt[1]["content"]
    assert "சான்று" in prompt[1]["content"]


def test_unknown_citation_never_becomes_a_url():
    hit = {"source_url":"https://www.srmist.edu.in/","source_title":"Official fixture","source_document_id":"fixture"}
    citations,unknown = cited_sources("A claim [S1] and [S9]",[hit])
    assert len(citations) == 1
    assert citations[0]["url"] == hit["source_url"]
    assert unknown == ["9"]


def test_chunk_overlap_preserves_document_coverage():
    text = "abcdefghijklmnopqrstuvwxyz"
    assert list(chunks(text,10,3)) == ["abcdefghij","hijklmnopq","opqrstuvwx","vwxyz"]
    with pytest.raises(ValueError):
        list(chunks(text,5,5))


class FixtureEngine:
    def generate(self,*args,**kwargs):
        time.sleep(.01)
        return {"generated_answer":"A fixture [S9]","raw_generated_answer":"A fixture [S9]","abstained":False,
                "input_tokens":5,"output_tokens":3,"generation_seconds":.01}


class FixtureRetriever:
    def __init__(self,empty=False):
        self.hits = [] if empty else [{"source_document_id":"fixture","source_url":"https://www.srmist.edu.in/","source_title":"fixture"}]
    def query(self,*args,**kwargs):
        return self.hits,.001
    def context(self,hits):
        return ("fixture evidence" if hits else ""),hits


def test_invalid_citation_triggers_measured_abstention(prediction):
    row = {**prediction,"benchmark_id":"fixture"}
    result = infer_record(FixtureEngine(),row,track="campus",experiment="C",retriever=FixtureRetriever())
    assert result["abstained"]
    assert result["abstention_reason"] == "invalid_or_missing_source_citation"
    assert result["citations"] == []
    assert result["total_seconds"] >= .01


def test_missing_evidence_abstains_without_generating(prediction):
    class NeverCalled:
        def generate(self,*args,**kwargs):
            raise AssertionError("Must abstain before generation")
    result = infer_record(NeverCalled(),{**prediction,"benchmark_id":"fixture"},track="campus",experiment="D",retriever=FixtureRetriever(True))
    assert result["abstained"]
    assert result["output_tokens"] == 0
    assert result["generation_seconds"] == 0


def test_language_budget_uses_only_eligible_examples_and_records_real_balance():
    from backend.training import balanced_indices
    from collections import Counter
    rows = [{'benchmark_id':f'{language}-{i}','language':language} for language,count in [('en',7),('hi',5),('ta',3)] for i in range(count)]
    eligible = list(range(len(rows)-1))
    selected = balanced_indices(rows,eligible,4,['en','hi','ta'],42)
    assert Counter(rows[i]['language'] for i in selected) == {'en':2,'hi':2,'ta':2}
    assert set(selected).issubset(eligible)
    assert selected == balanced_indices(rows,eligible,4,['en','hi','ta'],42)


def test_language_budget_cannot_hide_a_missing_language():
    from backend.training import balanced_indices
    with pytest.raises(PrerequisiteError,match='Every required language'):
        balanced_indices([{'benchmark_id':'en-1','language':'en'}],[0],4,['en','hi','ta'],42)
