"""Interactive FAQ shortcuts and language routing, separate from research inference."""
from datetime import datetime, timedelta, timezone
import re
import time
import unicodedata

from backend.college import COLLEGE, is_verified, validate_faq
from backend.modeling import ABSTAIN, PrerequisiteError
from backend.settings import config, digest, read_json, read_jsonl


TOPICS = (
    ("ktr-library-rfid", {"en": "Library technology", "hi": "पुस्तकालय की तकनीक", "ta": "நூலகத் தொழில்நுட்பம்"}),
    ("ktr-transport-booking", {"en": "Campus bus booking", "hi": "कैंपस बस की बुकिंग", "ta": "வளாகப் பேருந்து முன்பதிவு"}),
    ("ktr-oori-ac", {"en": "Oori hostel rooms", "hi": "ओरी छात्रावास के कमरे", "ta": "ஓரி விடுதி அறைகள்"}),
    ("ktr-vinayagar-temple", {"en": "Temple on campus", "hi": "परिसर में मंदिर", "ta": "வளாகத்தில் உள்ள கோயில்"}),
    ("ktr-facilities-division", {"en": "Campus maintenance", "hi": "परिसर का रखरखाव", "ta": "வளாகப் பராமரிப்பு"}),
)

# Exact, authored application questions; no keywords, held-out labels or test aliases.
ALIASES = {
    "ktr-library-rfid": ("What technology does the library use?", "पुस्तकालय में कौन सी तकनीक उपयोग होती है?", "நூலகத்தில் என்ன தொழில்நுட்பம் பயன்படுத்தப்படுகிறது?"),
    "ktr-transport-booking": ("How do I book a campus bus?", "कैंपस बस की बुकिंग कैसे करें?", "வளாகப் பேருந்தை எப்படி முன்பதிவு செய்வது?"),
    "ktr-oori-ac": ("Does Oori hostel have AC rooms?", "क्या ओरी छात्रावास में एसी कमरे हैं?", "ஓரி விடுதியில் ஏசி அறைகள் உள்ளனவா?"),
    "ktr-vinayagar-temple": ("Which temple is on campus?", "परिसर में कौन सा मंदिर है?", "வளாகத்தில் எந்தக் கோயில் உள்ளது?"),
    "ktr-facilities-division": ("Who maintains the campus?", "परिसर का रखरखाव कौन करता है?", "வளாகத்தைப் பராமரிப்பது யார்?"),
}


def detect_chat_language(text):
    # English entity names do not override the user's Hindi/Tamil script.
    counts = {"hi": 0, "ta": 0, "en": 0}
    for character in text:
        if not character.isalpha():
            continue
        if "\u0900" <= character <= "\u097f":
            counts["hi"] += 1
        elif "\u0b80" <= character <= "\u0bff":
            counts["ta"] += 1
        elif "LATIN" in unicodedata.name(character, ""):
            counts["en"] += 1
    if counts["hi"] and counts["ta"]:
        return None
    return "hi" if counts["hi"] else "ta" if counts["ta"] else "en" if counts["en"] else None


def question_key(text):
    text = unicodedata.normalize("NFC", text).casefold()
    return " ".join("".join(c for c in text if not unicodedata.category(c).startswith("P")).split())


def unavailable_reply(question, language, reason):
    text = {
        "en": "I can't answer a new question right now. You can still ask the suggested campus questions below, or try again later.",
        "hi": "अभी मैं किसी नए सवाल का जवाब नहीं दे पा रहा हूँ। आप नीचे दिए गए परिसर के सुझाए सवाल पूछ सकते हैं या थोड़ी देर बाद फिर कोशिश कर सकते हैं।",
        "ta": "இப்போது ஒரு புதிய கேள்விக்குப் பதில் அளிக்க முடியவில்லை. கீழே பரிந்துரைக்கப்பட்ட வளாகக் கேள்விகளைக் கேட்கலாம் அல்லது சிறிது நேரம் கழித்து மீண்டும் முயற்சிக்கலாம்.",
    }
    return {"question": question, "language": language, "generated_answer": text[language],
        "raw_generated_answer": None, "answer_method": "availability_notice", "abstained": True,
        "abstention_reason": "model_temporarily_unavailable", "availability_reason": reason,
        "citations": [], "retrieved": [], "evaluation_status": "completed", "research_scored": False}


def load_chat_faqs():
    manifest = read_json(COLLEGE / "manifest.json")
    if not manifest:
        return []
    rows = read_jsonl(COLLEGE / "versions" / manifest["version"] / "faq.jsonl")
    if len(rows) != manifest["count"] or digest(rows) != manifest["records_sha256"]:
        raise PrerequisiteError("The campus FAQ snapshot failed its checksum check.")
    settings = config("retrieval")
    accepted = settings.get("accepted_verification_statuses", ["human_verified"])
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=settings["max_source_age_days"])
    eligible = []
    for row in rows:
        if not is_verified(row) or row["verification_status"] not in accepted:
            continue
        if not row.get("verified_at") or datetime.fromisoformat(row["verified_at"]) < cutoff:
            continue
        if row.get("effective_date") and row["effective_date"] > now.date().isoformat():
            continue
        validate_faq(row)
        eligible.append(row)
    return eligible


def suggestions():
    rows = load_chat_faqs()
    by_id = {(r["faq_id"], r["language"]): r for r in rows}
    topics = []
    for identifier, labels in TOPICS:
        if all((identifier, language) in by_id for language in ("en", "hi", "ta")):
            topics.append({"id": identifier, "labels": labels,
                "questions": {language: by_id[(identifier, language)]["canonical_question"]
                              for language in ("en", "hi", "ta")}})
    return {"questions": topics, "languages": ["en", "hi", "ta"],
            "answer_method": "source_faq", "human_review_status": "pending"}


def faq_reply(question, language):
    start = time.perf_counter()
    rows = load_chat_faqs()
    available = {identifier for identifier, _ in TOPICS}
    key = question_key(question)
    matches = {r["faq_id"] for r in rows if r["faq_id"] in available
               and key in {question_key(r["canonical_question"]),
                           *(question_key(q) for q in ALIASES.get(r["faq_id"], ()))}}
    if len(matches) != 1:
        return None
    identifier = next(iter(matches))
    row = next((r for r in rows if r["faq_id"] == identifier and r["language"] == language), None)
    if not row:
        return None
    citation = {"label": "S1", "url": row["source_url"], "title": row["source_title"],
                "document_id": row["source_document_id"]}
    return {"question": question, "language": language, "generated_answer": row["answer"] + " [S1]",
        "raw_generated_answer": None, "answer_method": "source_faq", "faq_id": identifier,
        "citations": [citation], "retrieved": [row], "abstained": False,
        "evaluation_status": "completed", "research_scored": False, "model_inference_performed": False,
        "total_seconds": time.perf_counter() - start,
        "notice": "Answer from the source-reviewed campus FAQ, not a generated model response or research prediction."}


def enforce_reply_language(result, language):
    """Keep application replies in the requested script without changing research outputs."""
    result = {**result, "answer_method": "local_model"}
    if result.get("abstained"):
        result["generated_answer"] = ABSTAIN[language]
        return result
    answer = re.sub(r"\[S\d+\]", "", result["generated_answer"]).strip()
    if detect_chat_language(answer) == language:
        return result
    # A model may copy a differently localized FAQ verbatim. Use its reviewed
    # translation only when the original pipeline established exact provenance.
    if result.get("citation_origin") == "verbatim_source_attribution" and len(result.get("citations", [])) == 1:
        citation = result["citations"][0]
        hit = next((h for h in result.get("retrieved", []) if h["source_document_id"] == citation["document_id"]), None)
        if hit:
            translated = next((r for r in load_chat_faqs() if r["faq_id"] == hit.get("faq_id")
                and r["source_document_id"] == citation["document_id"] and r["language"] == language), None)
            if translated:
                return {**result, "generated_answer": translated["answer"] + f" [{citation['label']}]",
                        "answer_method": "localized_source_faq", "retrieved": [*result.get("retrieved", []), translated]}
    return {**result, "generated_answer": ABSTAIN[language], "abstained": True, "citations": [],
            "abstention_reason": "reply_language_mismatch"}
