"""Isolated application checks; no fixture is inserted into the research store."""
import pytest
from fastapi.testclient import TestClient
from filelock import FileLock

from backend import campus_chat, main
from backend.modeling import ABSTAIN, PrerequisiteError
from backend.settings import digest, write_json, write_jsonl


@pytest.fixture
def source_rows(monkeypatch):
    rows = []
    for identifier, _ in campus_chat.TOPICS:
        for language, question, answer in (
            ("en", f"What is the {identifier} fixture?", "This is an English fixture answer."),
            ("hi", f"{identifier} की परीक्षण जानकारी क्या है?", "यह हिन्दी में परीक्षण का उत्तर है।"),
            ("ta", f"{identifier} சோதனைத் தகவல் என்ன?", "இது தமிழில் ஒரு சோதனைப் பதில்."),
        ):
            rows.append({"faq_id": identifier, "language": language, "canonical_question": question,
                "answer": answer, "source_document_id": "fixture-" + identifier,
                "source_url": "https://www.srmist.edu.in/", "source_title": "Isolated fixture source",
                "verification_status": "source_verified", "reviewer_kind": "ai", "human_review_status": "pending"})
    monkeypatch.setattr(campus_chat, "load_chat_faqs", lambda: rows)
    return rows


@pytest.fixture
def client(monkeypatch, database, source_rows):
    monkeypatch.setattr(main, "Database", lambda: database)
    def no_gpu(*args, **kwargs):
        raise AssertionError("A known FAQ must not allocate a model or use the GPU.")
    monkeypatch.setattr(main, "QwenEngine", no_gpu)
    with TestClient(main.app) as value:
        yield value


@pytest.mark.parametrize("language", ["en", "hi", "ta"])
@pytest.mark.parametrize("topic", [identifier for identifier, _ in campus_chat.TOPICS])
def test_all_five_topics_answer_in_the_input_language_without_gpu(client, database, source_rows, language, topic):
    row = next(r for r in source_rows if r["faq_id"] == topic and r["language"] == language)
    response = client.post("/api/chat", json={"question": row["canonical_question"], "answer_mode": "faq_first"})
    assert response.status_code == 200
    answer = response.json()
    assert answer["language"] == language and answer["generated_answer"] == row["answer"] + " [S1]"
    assert answer["answer_method"] == "source_faq" and answer["research_scored"] is False
    assert answer["model_inference_performed"] is False and answer["raw_generated_answer"] is None
    assert answer["citations"][0]["document_id"] == row["source_document_id"]
    assert database.runs() == []


def test_suggestions_are_five_topics_with_three_real_localizations(client):
    response = client.get("/api/chat/suggestions")
    assert response.status_code == 200
    topics = response.json()["questions"]
    assert len(topics) == 5
    assert all(set(t["questions"]) == {"en", "hi", "ta"} for t in topics)
    assert all(set(t["labels"]) == {"en", "hi", "ta"} for t in topics)


@pytest.mark.parametrize("text,language", [
    ("What is the campus bus?", "en"), ("SRMIST library में कौन सी तकनीक है?", "hi"),
    ("SRMIST library என்ன தொழில்நுட்பம்?", "ta"), ("12345", None), ("नमस्ते வணக்கம்", None),
])
def test_chat_language_respects_indic_script_and_asks_for_ambiguous_text(text, language):
    assert campus_chat.detect_chat_language(text) == language


def test_unknown_question_does_not_match_topic_keywords(source_rows):
    assert campus_chat.faq_reply("What will the library fee be in 2040?", "en") is None
    assert campus_chat.faq_reply("Does the library use blockchain?", "en") is None


def test_exact_question_can_use_an_explicit_answer_language(client, source_rows):
    row = next(r for r in source_rows if r["language"] == "en")
    answer = client.post("/api/chat", json={"question": row["canonical_question"],
        "language": "ta", "answer_mode": "faq_first"}).json()
    assert answer["language"] == "ta" and campus_chat.detect_chat_language(answer["generated_answer"]) == "ta"


def test_unmatched_wrong_language_model_output_abstains_in_requested_language(client, monkeypatch, tmp_path):
    class Engine:
        loading_seconds = 0.0
        def __init__(self, *args): pass
        def close(self): pass
    monkeypatch.setattr(main, "QwenEngine", Engine)
    monkeypatch.setattr(main, "gpu_lock", lambda: FileLock(tmp_path / "fixture-gpu.lock"))
    monkeypatch.setattr(main, "apply_inference_memory_policy", lambda policy: {"fixture": True})
    monkeypatch.setattr(main, "infer_record", lambda *a, **kw: {"evaluation_status": "completed",
        "generated_answer": "Wrong English fixture text.", "raw_generated_answer": "Wrong English fixture text.",
        "abstained": False, "citations": [], "retrieved": []})
    response = client.post("/api/chat", json={"question": "परीक्षण का कोई नया सवाल है?", "answer_mode": "faq_first", "experiment": "A"})
    assert response.status_code == 200
    assert response.json()["generated_answer"] == ABSTAIN["hi"]
    assert response.json()["abstention_reason"] == "reply_language_mismatch"


def test_localizes_only_a_source_attributed_answer_and_keeps_raw_text(source_rows):
    hit = next(r for r in source_rows if r["language"] == "en")
    original = {"generated_answer": hit["answer"] + " [S1]", "raw_generated_answer": hit["answer"],
        "citation_origin": "verbatim_source_attribution", "abstained": False,
        "citations": [{"label": "S1", "document_id": hit["source_document_id"]}], "retrieved": [hit]}
    translated = campus_chat.enforce_reply_language(original, "ta")
    assert translated["answer_method"] == "localized_source_faq"
    assert translated["raw_generated_answer"] == original["raw_generated_answer"]
    assert campus_chat.detect_chat_language(translated["generated_answer"]) == "ta"


def test_changed_snapshot_is_rejected_before_serving_any_faq(monkeypatch, tmp_path):
    monkeypatch.setattr(campus_chat, "COLLEGE", tmp_path)
    write_json(tmp_path / "manifest.json", {"version": "fixture", "count": 1, "records_sha256": "wrong"})
    write_jsonl(tmp_path / "versions/fixture/faq.jsonl", [{"fixture": True}])
    with pytest.raises(PrerequisiteError, match="checksum"):
        campus_chat.load_chat_faqs()


def test_expired_faq_cannot_be_served(monkeypatch, tmp_path):
    monkeypatch.setattr(campus_chat, "COLLEGE", tmp_path)
    monkeypatch.setattr(campus_chat, "config", lambda name: {"accepted_verification_statuses": ["source_verified"], "max_source_age_days": 1})
    rows = [{"verification_status": "source_verified", "verified_at": "2000-01-01T00:00:00+00:00"}]
    write_json(tmp_path / "manifest.json", {"version": "fixture", "count": 1, "records_sha256": digest(rows)})
    write_jsonl(tmp_path / "versions/fixture/faq.jsonl", rows)
    assert campus_chat.load_chat_faqs() == []


@pytest.mark.parametrize("language,question", [("en", "An unknown fixture question?"),
    ("hi", "किसी नए विषय का परीक्षण सवाल?"), ("ta", "புதிய சோதனைத் தலைப்பு பற்றிய கேள்வி?")])
def test_unavailable_model_returns_a_localized_notice_without_research_records(client, monkeypatch, tmp_path, language, question, database):
    def unavailable(*args, **kwargs):
        raise PrerequisiteError("Insufficient free GPU memory in this isolated fixture.")
    monkeypatch.setattr(main, "QwenEngine", unavailable)
    monkeypatch.setattr(main, "gpu_lock", lambda: FileLock(tmp_path / "fixture-unavailable.lock"))
    monkeypatch.setattr(main, "apply_inference_memory_policy", lambda policy: {"fixture": True})
    response = client.post("/api/chat", json={"question": question, "answer_mode": "faq_first", "experiment": "A"})
    assert response.status_code == 200
    answer = response.json()
    assert answer["language"] == language and campus_chat.detect_chat_language(answer["generated_answer"]) == language
    assert answer["answer_method"] == "availability_notice" and answer["research_scored"] is False
    assert answer["citations"] == [] and database.runs() == []
