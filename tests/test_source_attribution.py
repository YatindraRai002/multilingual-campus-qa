import pytest

from backend.evaluation.inference_runner import infer_record
from backend.source_attribution import normalized_verbatim, verbatim_source_label


def hit(answer, document="source-one"):
    return {"answer": answer, "evidence_quote": "Official excerpt", "source_document_id": document,
            "source_url": "https://www.srmist.edu.in/library/", "source_title": "Test source"}


@pytest.mark.parametrize("answer,generated", [
    ("Astrophilia.", "ASTROPHILIA"),
    ("विनायगर मंदिर।", "विनायगर मंदिर"),
    ("விநாயகர் கோயில்.", "விநாயகர்   கோயில்"),
])
def test_exact_source_attribution_preserves_unicode(answer, generated):
    assert verbatim_source_label(generated, [hit(answer)]) == "S1"


def test_attribution_rejects_added_claims_partial_spans_and_ambiguity():
    assert verbatim_source_label("Known answer plus a new claim", [hit("Known answer")]) is None
    assert verbatim_source_label("Known", [hit("Known answer")]) is None
    assert verbatim_source_label("Known answer", [hit("Known answer"), hit("Known answer", "source-two")]) is None
    assert verbatim_source_label("!!!", [hit("!!!")]) is None
    assert normalized_verbatim("கோயில்") != normalized_verbatim("கயல")
    assert verbatim_source_label("C", [hit("C++")]) is None
    assert verbatim_source_label("2", [hit("-2")]) is None


class Engine:
    def __init__(self, answer):
        self.answer = answer

    def generate(self, *args, **kwargs):
        return {"generated_answer": self.answer, "raw_generated_answer": self.answer,
                "abstained": False, "input_tokens": 8, "output_tokens": 3, "generation_seconds": .01}


class Retrieval:
    def __init__(self, policy):
        self.settings = {"citation_policy": policy}

    def query(self, question):
        return [hit("Known answer.")], .001

    def context(self, hits):
        return "[S1] Known answer.", hits


def prediction(answer, policy):
    row = {"benchmark_id": "isolated-attribution-fixture", "language": "en", "context": "",
           "question": "Which answer is supplied?", "reference_answer": "Known answer.",
           "source_dataset": "isolated-test-fixture"}
    return infer_record(Engine(answer), row, track="campus", experiment="D", retriever=Retrieval(policy))


def test_legacy_policy_retains_the_original_guard():
    result = prediction("Known answer.", "model-emitted-v1")
    assert result["abstained"] and result["abstention_reason"] == "invalid_or_missing_source_citation"


def test_v2_attributes_only_supplied_text_and_keeps_raw_output():
    result = prediction("Known answer.", "model-or-verbatim-v2")
    assert not result["abstained"]
    assert result["raw_generated_answer"] == "Known answer."
    assert result["generated_answer"] == "Known answer. [S1]"
    assert result["citation_origin"] == "verbatim_source_attribution"
    assert result["citations"][0]["document_id"] == "source-one"


def test_v2_does_not_repair_unknown_source_labels_or_new_content():
    for answer in ("Known answer [S9]", "A different unsupported answer"):
        result = prediction(answer, "model-or-verbatim-v2")
        assert result["abstained"] and not result["citations"]


def test_valid_model_citations_are_preserved():
    result = prediction("Known answer. [S1]", "model-or-verbatim-v2")
    assert not result["abstained"]
    assert result["citation_origin"] == "model_emitted"
