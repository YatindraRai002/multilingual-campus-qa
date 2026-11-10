"""Conservative provenance formatting; this does not judge factual correctness."""
import unicodedata

MODEL_CITATIONS = "model-emitted-v1"
VERBATIM_CITATIONS = "model-or-verbatim-v2"


def citation_policy(settings):
    selected = settings.get("citation_policy", MODEL_CITATIONS)
    if selected not in {MODEL_CITATIONS, VERBATIM_CITATIONS}:
        raise ValueError("Unsupported citation policy")
    return selected


def normalized_verbatim(text):
    # Internal punctuation, signs, symbols and Indic marks can change meaning.
    # Ignore only case, repeated whitespace and terminal sentence periods/dandas.
    return " ".join(unicodedata.normalize("NFC", text).casefold().split()).rstrip(".।॥").rstrip()


def verbatim_source_label(answer, used):
    """Attribute only a complete normalized answer/quote from one supplied source document.

    No aliases, reference answers, semantic similarity, substrings or test labels are used.
    A match proves text provenance, not that it correctly answers the user's question.
    """
    target = normalized_verbatim(answer)
    if not target or not any(character.isalnum() for character in target):
        return None
    matches = [(index, hit["source_document_id"]) for index, hit in enumerate(used, start=1)
               if any(target == normalized_verbatim(hit.get(field, "")) for field in ("answer", "evidence_quote"))]
    if len({document for _, document in matches}) != 1:
        return None
    return f"S{matches[0][0]}"
