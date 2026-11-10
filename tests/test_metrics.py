import copy

import pytest

from backend.evaluation.accuracy import answer_scores, normalize_answer
from backend.evaluation.evaluation_runner import evaluate_group, evaluate_predictions
from backend.evaluation.statistics import bootstrap_ci, percentile


@pytest.mark.parametrize("language,text",[("hi","पुस्तकालय"),("ta","தமிழ்")])
def test_indic_combining_marks_are_preserved(language,text):
    assert normalize_answer(text,language) == text
    assert answer_scores(text,[text],language) == (1,1)


def test_articles_are_only_removed_for_english():
    assert answer_scores("The library.",["library"],"en") == (1,1)
    assert normalize_answer("a library","ta") == "a library"
    assert answer_scores("open library",["library"],"en")[1] == pytest.approx(2/3)


def test_known_formulas_and_denominators(prediction):
    a,b,c = [copy.deepcopy(prediction) for _ in range(3)]
    a["annotation"] = {"correct":True,"claims":[{"supported":True},{"supported":True}]}
    b.update(generated_answer="dormitory",total_seconds=2.2,annotation={"correct":False,"claims":[{"supported":False}]})
    c.update(answerable=False,reference_answer="",reference_answers=[],abstained=True,output_tokens=0,generation_seconds=0,
             total_seconds=3.2,annotation={"correct":False,"claims":[]})
    metrics = evaluate_group([a,b,c])
    assert metrics["accuracy"]["value"] == 50
    assert metrics["accuracy"]["denominator"] == 2
    assert metrics["exact_match"]["value"] == pytest.approx(200/3)
    assert metrics["hallucination_incidence"]["value"] == 50
    assert metrics["hallucination_incidence"]["denominator"] == 2
    assert metrics["unsupported_claim_rate"]["value"] == pytest.approx(100/3)
    assert metrics["unsupported_claim_rate"]["denominator"] == 3
    assert metrics["abstention_accuracy"]["value"] == 100
    assert metrics["latency"]["total_seconds"]["mean"] == pytest.approx(2.2)
    assert metrics["latency"]["total_seconds"]["p95"] == pytest.approx(3.1)
    assert metrics["latency"]["throughput"]["value"] == 10


def test_missing_reviews_never_become_fake_factuality_scores(prediction):
    metrics = evaluate_group([prediction])
    for name in ["accuracy","hallucination_incidence","unsupported_claim_rate"]:
        assert metrics[name]["value"] is None
        assert metrics[name]["status"] == "pending"
    assert metrics["exact_match"]["value"] == 100


def test_answerable_abstention_cannot_be_correct_even_with_a_contradictory_annotation(prediction):
    row={**prediction,'abstained':True,'generated_answer':'[ABSTAIN]',
         'annotation':{'correct':True,'claims':[]}}
    result=evaluate_group([row])
    assert result['accuracy']['value']==0
    assert result['accuracy']['denominator']==1
    assert result['exact_match']['value']==0


def test_partial_annotation_does_not_change_accuracy_denominator(prediction):
    a = {**prediction,"annotation":{"correct":True,"claims":[]}}
    metrics = evaluate_group([a,prediction])
    assert metrics["accuracy"]["value"] is None
    assert metrics["accuracy"]["denominator"] == 2
    assert metrics["accuracy"]["reviewed_or_scored"] == 1


def test_retrieval_hit_rate_and_mrr_include_misses(prediction):
    first = {**prediction,"retrieval_enabled":True,"relevant_document_ids":["relevant"],
             "retrieved":[{"source_document_id":"wrong"},{"source_document_id":"relevant"}]}
    second = {**first,"retrieved":[]}
    metrics = evaluate_group([first,second],k=4)
    assert metrics["recall_at_k"]["value"] == 50
    assert metrics["mrr"]["value"] == .25


def test_retrieval_denominator_includes_explicitly_unanswerable_queries(prediction):
    positive={**prediction,'retrieval_enabled':True,'relevant_document_ids':['relevant'],
              'retrieved':[{'source_document_id':'relevant'}]}
    negative={**prediction,'retrieval_enabled':True,'relevant_document_ids':[],
              'retrieved':[],'answerable':False,'abstained':True}
    metrics=evaluate_group([positive,negative],k=4)
    assert metrics['recall_at_k']['value']==50
    assert metrics['recall_at_k']['denominator']==2
    assert metrics['recall_at_k']['reviewed_or_scored']==2
    assert metrics['mrr']['value']==.5 and metrics['mrr']['denominator']==2


def test_unknown_relevance_keeps_full_denominator_and_scope_pending(prediction):
    positive={**prediction,'retrieval_enabled':True,'relevant_document_ids':['relevant'],
              'retrieved':[{'source_document_id':'relevant'}]}
    unknown={**prediction,'retrieval_enabled':True,'relevant_document_ids':None,'retrieved':[]}
    metrics=evaluate_group([positive,unknown],k=4)
    for key in ['recall_at_k','mrr']:
        assert metrics[key]['value'] is None and metrics[key]['status']=='pending'
        assert metrics[key]['denominator']==2 and metrics[key]['reviewed_or_scored']==1


def test_populations_are_separate_and_failures_excluded(prediction):
    a = {**prediction,"source_dataset":"SQuAD-v1.1"}
    b = {**prediction,"language":"hi","source_dataset":"ai4bharat/IndicQA"}
    failed = {**prediction,"evaluation_status":"failed"}
    result = evaluate_predictions([a,b,failed])
    assert set(result["populations"]) == {"SQuAD-v1.1","ai4bharat/IndicQA"}
    assert result["excluded_failed_predictions"] == 1
    assert result["populations"]["ai4bharat/IndicQA"]["language_performance_gap"]["value"] is None


def test_fairness_gap_uses_one_source(prediction):
    rows = [{**prediction,"source_dataset":"same-source","language":"hi","annotation":{"correct":True,"claims":[]}},
            {**prediction,"source_dataset":"same-source","language":"ta","annotation":{"correct":False,"claims":[]}}]
    result = evaluate_predictions(rows)
    assert result["populations"]["same-source"]["language_performance_gap"]["value"] == 100


def test_empty_metrics_and_reproducible_confidence_intervals():
    assert evaluate_predictions([])["status"] == "not_performed"
    assert bootstrap_ci([0,1,1],seed=42) == bootstrap_ci([0,1,1],seed=42)
    assert bootstrap_ci([1]) is None
    assert percentile([1,2,3],.95) == pytest.approx(2.9)


def test_valid_rag_citation_labels_do_not_penalize_answer_content(prediction):
    row = {**prediction,'generated_answer':'library [S1]','retrieval_enabled':True}
    result = evaluate_group([row])
    assert result['exact_match']['value'] == 100
    assert result['f1']['value'] == 100
    assert row['generated_answer'] == 'library [S1]'
