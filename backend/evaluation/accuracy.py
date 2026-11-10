from __future__ import annotations

import re
import unicodedata
from collections import Counter


def normalize_answer(text: str, language: str) -> str:
    text = unicodedata.normalize("NFC", text).casefold()
    # Preserve Devanagari/Tamil combining marks. ASCII-only \w filtering corrupts them.
    text = "".join(c for c in text if not unicodedata.category(c).startswith("P"))
    if language == "en":
        text = re.sub(r"\b(a|an|the)\b", " ", text)
    return " ".join(text.split())


def answer_scores(prediction: str, references: list[str], language: str):
    predicted = normalize_answer(prediction, language)
    exact, best_f1 = 0.0, 0.0
    for reference in references or [""]:
        normalized = normalize_answer(reference, language)
        exact = max(exact, float(predicted == normalized))
        left, right = predicted.split(), normalized.split()
        if not left or not right:
            score = float(left == right)
        else:
            overlap = sum((Counter(left) & Counter(right)).values())
            precision, recall = overlap / len(left), overlap / len(right)
            score = 2 * precision * recall / (precision + recall) if overlap else 0.0
        best_f1 = max(best_f1, score)
    return exact, best_f1
