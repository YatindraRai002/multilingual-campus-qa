"""The authored demo is application content, never research predictions."""
from copy import deepcopy
import pytest
from fastapi.testclient import TestClient
from backend import demo_chat, main
from backend.campus_chat import detect_chat_language


@pytest.fixture
def client(monkeypatch, database):
    monkeypatch.setattr(main, "Database", lambda: database)
    def no_gpu(*args, **kwargs):
        raise AssertionError("A prepared demo answer must not allocate the GPU model.")
    monkeypatch.setattr(main, "QwenEngine", no_gpu)
    with TestClient(main.app) as value:
        yield value


@pytest.mark.parametrize("language", ["en", "hi", "ta"])
@pytest.mark.parametrize("topic_index", range(5))
def test_detailed_demo_works_in_all_fifteen_cases(client, database, language, topic_index):
    topic = demo_chat.load_demo_topics()[topic_index]
    response = client.post("/api/chat", json={"question": topic["questions"][language], "answer_mode": "faq_first"})
    assert response.status_code == 200
    answer = response.json()
    assert answer["topic_id"] == topic["id"] and answer["language"] == language
    assert answer["answer_method"] == "prepared_demo" and answer["is_demo"] is True
    assert len(answer["answer_sections"]) == 4 and len(answer["generated_answer"]) > 900
    assert detect_chat_language(answer["generated_answer"]) == language
    assert answer["model_inference_performed"] is False and answer["research_scored"] is False
    assert answer["raw_generated_answer"] is None and answer["retrieved"] == []
    assert answer["citations"] and all(r["is_demo_reference"] for r in answer["reference_sources"])
    assert database.runs() == []


@pytest.mark.parametrize("question,identifier", [
    ("tell me about SRM", "demo-srm-overview"),
    ("tell about  hostels", "demo-hostels"),
    ("Please tell about placements!", "demo-placements"),
    ("Can you tell me about admissions?", "demo-admissions"),
    ("वेलकम के बजाय एसआरएम की फीस 2040 में क्या होगी?", None),
    ("SRM के बारे में बताओ", "demo-srm-overview"),
    ("பிளேஸ்மென்ட் பற்றி சொல்லுங்கள்", "demo-placements"),
])
def test_authored_aliases_cover_the_requested_demo_without_keyword_guessing(question, identifier):
    answer = demo_chat.demo_reply(question, detect_chat_language(question))
    assert (answer["topic_id"] if answer else None) == identifier


def test_suggestions_show_five_broad_topics(client):
    data = client.get("/api/chat/suggestions").json()
    assert data["is_demo"] is True and data["answer_method"] == "prepared_demo"
    assert {t["id"] for t in data["questions"]} == {"demo-srm-overview", "demo-hostels", "demo-placements", "demo-admissions", "demo-campus-life"}


def test_demo_references_reject_nonofficial_hosts(monkeypatch):
    from backend.settings import read_json, ROOT
    invalid = deepcopy(read_json(ROOT / "config/demo_answers.json"))
    invalid["topics"][0]["sources"][0]["url"] = "https://srmist.edu.in.attacker.example/page"
    monkeypatch.setattr(demo_chat, "read_json", lambda path: invalid)
    with pytest.raises(ValueError, match="official university"):
        demo_chat.load_demo_topics()
