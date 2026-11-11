"""Prepared multilingual demonstration content, separate from model/research inference."""
import re
import time
from urllib.parse import urlparse

from backend.campus_chat import question_key
from backend.settings import ROOT, read_json

LANGUAGES = ("en", "hi", "ta")


def load_demo_topics():
    payload = read_json(ROOT / "config/demo_answers.json")
    if not payload or payload.get("purpose") != "prepared_interactive_demo" or payload.get("not_research_data") is not True:
        raise ValueError("The interactive demo content is missing or incorrectly labelled.")
    topics = payload.get("topics", [])
    if len(topics) != 5 or len({t["id"] for t in topics}) != 5:
        raise ValueError("The demo requires five distinct topics.")
    for topic in topics:
        for language in LANGUAGES:
            answer = topic["answers"][language]
            if not topic["questions"][language] or not topic["labels"][language] or not answer["title"] or not answer["intro"]:
                raise ValueError("Each demo topic requires all three localizations.")
            if len(answer["sections"]) < 4 or any(not s["heading"] or len(s["text"]) < 30 for s in answer["sections"]):
                raise ValueError("Demo answers require detailed named sections.")
        if not topic.get("sources"):
            raise ValueError("Demo topics require official reference links.")
        for source in topic["sources"]:
            parsed = urlparse(source["url"])
            host = parsed.hostname or ""
            if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port not in (None, 443) or not (host == "srmist.edu.in" or host.endswith(".srmist.edu.in")):
                raise ValueError("Demo references must be official university HTTPS URLs.")
    return topics


def demo_suggestions():
    return {"questions": [{"id": t["id"], "labels": t["labels"], "questions": t["questions"]}
                          for t in load_demo_topics()],
            "languages": list(LANGUAGES), "answer_method": "prepared_demo", "is_demo": True}


def demo_key(question):
    value = question_key(question)
    value = re.sub(r"^(?:can|could|would) you (?:please )?", "", value)
    return re.sub(r"^(?:please|kindly|कृपया|தயவுசெய்து)\s+|\s+(?:please|कृपया|தயவுசெய்து)$", "", value).strip()


def demo_reply(question, language):
    started = time.perf_counter()
    if language not in LANGUAGES:
        return None
    key = demo_key(question)
    matches = []
    for topic in load_demo_topics():
        candidates = [*topic["questions"].values(), *(q for values in topic["aliases"].values() for q in values)]
        if key in {demo_key(q) for q in candidates}:
            matches.append(topic)
    if len(matches) != 1:
        return None
    topic = matches[0]
    answer = topic["answers"][language]
    notices = {"en": "Prepared demo overview · Check official sources for current details",
               "hi": "तैयार किया गया डेमो उत्तर · वर्तमान जानकारी के लिए आधिकारिक स्रोत देखें",
               "ta": "தயாரிக்கப்பட்ட டெமோ விளக்கம் · தற்போதைய விவரங்களுக்கு அதிகாரப்பூர்வ பக்கங்களைப் பாருங்கள்"}
    references = [{"source_document_id": "demo-reference-" + s["id"], "source_url": s["url"],
                   "source_title": s["title"], "is_demo_reference": True, "language": language}
                  for s in topic["sources"]]
    citations = [{"label": f"S{i}", "url": r["source_url"], "title": r["source_title"],
                  "document_id": r["source_document_id"]} for i, r in enumerate(references, start=1)]
    plain = "\n\n".join([answer["title"], answer["intro"],
                            *(s["heading"] + "\n" + s["text"] for s in answer["sections"])])
    return {"question": question, "language": language, "generated_answer": plain,
            "answer_title": answer["title"], "answer_intro": answer["intro"], "answer_sections": answer["sections"],
            "raw_generated_answer": None, "answer_method": "prepared_demo", "topic_id": topic["id"],
            "is_demo": True, "demo_notice": notices[language], "model_inference_performed": False,
            "research_scored": False, "citations": citations, "reference_sources": references,
            "retrieved": [], "abstained": False, "evaluation_status": "completed",
            "total_seconds": time.perf_counter() - started,
            "notice": "Prepared multilingual demo content; not a model prediction or sealed research result."}
