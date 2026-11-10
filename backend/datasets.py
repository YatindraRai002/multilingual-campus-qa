from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import httpx

from backend.settings import ROOT, config, digest, read_json, read_jsonl, utcnow, write_json, write_jsonl

BENCHMARK = ROOT / "data" / "benchmark"
LANGUAGES = {"en": "English", "hi": "Hindi", "ta": "Tamil"}
ALIASES = {"english": "en", "eng_latn": "en", "eng": "en", "hindi": "hi", "hin_deva": "hi",
           "hin": "hi", "tamil": "ta", "tam_taml": "ta", "tam": "ta"}
PROCESSING_VERSION = "unicode-nfc-source-groups-v6-approved-indicsquad-script-audit"


def language_code(value: str) -> str:
    key = str(value).strip().lower().replace("-", "_")
    code = ALIASES.get(key, key)
    if code not in LANGUAGES:
        raise ValueError(f"Unsupported language: {value}")
    return code


def identify_language(text: str) -> str | None:
    # Conservative script routing; mixed/no-script text requires explicit language selection.
    counts = Counter()
    for c in text:
        if c.isalpha():
            if "\u0900" <= c <= "\u097f":
                counts["hi"] += 1
            elif "\u0b80" <= c <= "\u0bff":
                counts["ta"] += 1
            elif "LATIN" in unicodedata.name(c, ""):
                counts["en"] += 1
    if not counts:
        return None
    code, count = counts.most_common(1)[0]
    return code if count / sum(counts.values()) >= 0.6 else None


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", str(text))).strip()


def canonical(text: str) -> str:
    return normalize(text).casefold()


def fetch(url: str, destination: Path) -> dict:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        with httpx.Client(follow_redirects=True, timeout=180) as client:
            response = client.get(url)
            response.raise_for_status()
        # Exclusive creation: downloaded source files are never overwritten.
        with destination.open("xb") as stream:
            stream.write(response.content)
    content = destination.read_bytes()
    return {"url": url, "path": destination.relative_to(ROOT).as_posix(), "bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest()}


def acquire() -> dict:
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        response = client.get("https://huggingface.co/api/datasets/ai4bharat/IndicQA")
        response.raise_for_status()
        info = response.json()
    selection = config("benchmark")
    revision = selection.get("indicqa_revision") or info["sha"]
    destination = BENCHMARK / "raw" / "indicqa" / revision
    artifacts = []
    for filename in ["README.md", "IndicQA.py", "data/indicqa.hi.json", "data/indicqa.ta.json"]:
        url = f"https://huggingface.co/datasets/ai4bharat/IndicQA/resolve/{revision}/{filename}"
        artifacts.append(fetch(url, destination / filename))
    if not (destination / "hub_metadata.json").exists():
        write_json(destination / "hub_metadata.json", info,exclusive=True)
    # Official SQuAD downloads; checksums pin the exact acquired bytes.
    for split in ["train", "dev"]:
        artifacts.append(fetch(f"https://rajpurkar.github.io/SQuAD-explorer/dataset/{split}-v1.1.json",
                               BENCHMARK / "raw" / "squad" / f"{split}-v1.1.json"))
        if artifacts[-1]["sha256"] != selection["squad_sha256"][f"{split}-v1.1.json"]:
            raise ValueError("Official SQuAD source bytes changed from the pinned checksums; review before proceeding.")
    from backend.supplemental import acquire_supplemental
    artifacts += acquire_supplemental()
    manifest = {"acquired_at": utcnow(), "indicqa_revision": revision, "artifacts": artifacts,
                "dataset_card": "https://huggingface.co/datasets/ai4bharat/IndicQA",
                "license": {"ai4bharat/IndicQA": "cc-by-4.0", "SQuAD-v1.1": "cc-by-sa-4.0"},
                "paper_resource": "ayushayush591/IndicQA_Benchmark",
                "warning": "AI4Bharat IndicQA is a component, not the complete Singh et al. paper benchmark.",
                "english_parallel": False}
    if selection.get('supplemental_training',{}).get('enabled'):
        manifest['license']['l3cube-pune/indic-squad'] = 'cc-by-4.0; inherited SQuAD cc-by-sa-4.0 obligations retained'
    manifest["version"] = digest({"revision": revision, "artifacts": artifacts})[:16]
    write_json(BENCHMARK / "acquisition.json", manifest)
    return manifest


def from_squad(path: Path, *, source: str, language: str, split: str, revision: str, original_split: str | None = None) -> list[dict]:
    data = read_json(path)
    rows = []
    for article_index, article in enumerate(data["data"]):
        title = article.get("title") or f"article-{article_index}"
        for paragraph_index, paragraph in enumerate(article["paragraphs"]):
            raw_context = paragraph["context"]
            for qa in paragraph["qas"]:
                answers = qa.get("answers", [])
                reference = [normalize(a["text"]) for a in answers if isinstance(a.get("text"), str) and normalize(a["text"])]
                explicitly_unanswerable = qa.get("category") == "NO" or qa.get("is_impossible") is True
                answerable = not explicitly_unanswerable
                warnings = []
                if not raw_context.strip() or not str(qa.get("question", "")).strip():
                    warnings.append("empty_context_or_question")
                if not reference and not explicitly_unanswerable:
                    warnings.append("malformed_or_empty_answer")
                if reference and explicitly_unanswerable:
                    warnings.append("conflicting_answerability_annotation")
                if reference and not any(canonical(a) in canonical(raw_context) for a in reference):
                    warnings.append("answer_not_in_context")
                for answer in answers:
                    start = answer.get("answer_start")
                    if isinstance(start, int) and raw_context[start:start+len(answer["text"])] != answer["text"]:
                        warnings.append("original_answer_offset_mismatch")
                        break
                if language in {"hi", "ta"} and identify_language(qa.get("question", "")) != language:
                    warnings.append("question_script_review_required")
                original_id = str(qa["id"])
                context = normalize(raw_context)
                question = normalize(qa["question"])
                row = {
                    "benchmark_id": f"{source}:{language}:{original_id}", "source_dataset": source,
                    "language": language, "context": context, "question": question,
                    "reference_answer": reference[0] if reference else "", "reference_answers": reference,
                    "answer_type": "extractive", "answerable": answerable,
                    "original_source_id": original_id,
                    "translation_status": "native_english" if language == "en" else "original_indicqa_per_card",
                    "split": split, "original_split": original_split or split,
                    "license": "cc-by-sa-4.0" if source == "SQuAD-v1.1" else "cc-by-4.0",
                    "source_document_id": f"{source}:{language}:{title}",
                    "canonical_document_group":f"{source}:{language}:{title}",
                    "canonical_question_group":'SQuAD:'+original_id if source == 'SQuAD-v1.1' else f"{source}:{language}:{original_id}",
                    "context_fingerprint": digest(canonical(context)),
                    "question_fingerprint": digest(canonical(question)),
                    "validation_warnings": sorted(set(warnings)),
                    "provenance": {"source_file": path.relative_to(ROOT).as_posix(), "revision": revision,
                                   "article_title": title, "paragraph_index": paragraph_index,
                                   "parallel_mapping": "not_established", "source_category": qa.get("category"),
                                   "answerability_rule": "category NO or is_impossible=true means unanswerable"},
                }
                rows.append(row)
    return rows


def group_split(rows: list[dict], *, validation_fraction: float = 0.1, seed: int = 42):
    """Assign all questions from a source document to exactly one split."""
    result = []
    for row in rows:
        score = int(digest([seed, row["source_document_id"]])[:12], 16) / (16**12)
        result.append({**row, "split": "validation" if score < validation_fraction else "train"})
    return result


def ensure_no_leakage(train: list[dict], validation: list[dict], test: list[dict]):
    for label, left, right in [("train/validation", train, validation), ("train/test", train, test),
                               ("validation/test", validation, test)]:
        for key in ["benchmark_id", "source_document_id", "context_fingerprint", "question_fingerprint",
                    "canonical_document_group","canonical_question_group"]:
            intersection = {r.get(key,r['benchmark_id']) for r in left} & {r.get(key,r['benchmark_id']) for r in right}
            if intersection:
                raise ValueError(f"Data leakage {label}: {len(intersection)} shared {key} values")


def current_manifest() -> dict | None:
    return read_json(BENCHMARK / "manifest.json")


def load_split(split: str, *, version: str | None = None) -> list[dict]:
    if split not in {"train", "validation", "test"}:
        raise ValueError("Unknown split")
    if version is None:
        manifest = current_manifest()
        if not manifest:
            raise ValueError("Prepare the benchmark first.")
        version = manifest["version"]
    if not re.fullmatch(r"[a-f0-9]{16}", version):
        raise ValueError("Invalid dataset version")
    path = BENCHMARK / "versions" / version / f"{split}.jsonl"
    manifest = read_json(path.parent / "manifest.json")
    if not manifest or not path.exists():
        raise ValueError("Dataset version or split missing")
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest["split_checksums"][split]:
        raise ValueError(f"Sealed {split} split checksum mismatch")
    return read_jsonl(path)


def prepare() -> dict:
    acquired = read_json(BENCHMARK / "acquisition.json")
    if not acquired:
        raise ValueError("Run acquire before prepare.")
    for artifact in acquired["artifacts"]:
        with (ROOT/artifact['path']).open('rb') as stream:
            actual_checksum = hashlib.file_digest(stream,'sha256').hexdigest()
        if actual_checksum != artifact["sha256"]:
            raise ValueError(f"Raw source checksum mismatch: {artifact['path']}")
    rev = acquired["indicqa_revision"]
    test = []
    for lang in ["hi", "ta"]:
        test += from_squad(BENCHMARK / "raw" / "indicqa" / rev / "data" / f"indicqa.{lang}.json",
                           source="ai4bharat/IndicQA", language=lang, split="test", revision=rev)
    test += from_squad(BENCHMARK / "raw" / "squad" / "dev-v1.1.json", source="SQuAD-v1.1",
                       language="en", split="test", revision="v1.1-dev-as-held-out-evaluation",original_split="validation")
    english_train = from_squad(BENCHMARK / "raw" / "squad" / "train-v1.1.json", source="SQuAD-v1.1",
                               language="en", split="train", revision="v1.1-train")
    extra = read_jsonl(BENCHMARK / "supplemental_training.jsonl")
    from backend.supplemental import prepare_supplemental
    approved,supplemental_report = prepare_supplemental(english_train)
    extra += approved
    # Never recycle held-out records. Split supplementary records by their source document.
    candidate = group_split(english_train + extra)
    held_context = {r["context_fingerprint"] for r in test}
    held_questions = {r["question_fingerprint"] for r in test}
    rejected, deduplicated, valid, seen = [], 0, [], set()
    for row in candidate:
        if row["validation_warnings"] or row["context_fingerprint"] in held_context or row["question_fingerprint"] in held_questions:
            rejected.append({"benchmark_id": row["benchmark_id"], "reason": row["validation_warnings"] or ["held_out_overlap"]})
            continue
        pair = (row["context_fingerprint"], row["question_fingerprint"], row["language"])
        if pair in seen:
            deduplicated += 1
            continue
        seen.add(pair)
        valid.append(row)
    # Duplicate questions across distinct training documents are assigned consistently by removing
    # all conflicting documents from the validation population, then putting their questions in train.
    train_question_docs = defaultdict(set)
    for row in valid:
        train_question_docs[row["question_fingerprint"]].add(row["source_document_id"])
    document_group = {row["source_document_id"]: row["source_document_id"] for row in valid}
    def find(document):
        while document_group[document] != document:
            document_group[document] = document_group[document_group[document]]
            document = document_group[document]
        return document
    # Join shared contexts and questions before final group split.
    for key in ["context_fingerprint", "question_fingerprint","canonical_document_group","canonical_question_group"]:
        first = {}
        for row in valid:
            document = row["source_document_id"]
            previous = first.setdefault(row.get(key,row['benchmark_id']), document)
            a, b = find(document), find(previous)
            document_group[max(a, b)] = min(a, b)
    for row in valid:
        root = find(row["source_document_id"])
        score = int(digest([42, root])[:12], 16)/(16**12)
        row["split"] = "validation" if score < 0.1 else "train"
    train = [r for r in valid if r["split"] == "train"]
    validation = [r for r in valid if r["split"] == "validation"]
    ensure_no_leakage(train, validation, test)
    version = digest({"acquisition": acquired["version"], "processing": PROCESSING_VERSION,
                      "supplement": digest(extra)})[:16]
    folder = BENCHMARK / "versions" / version
    if (folder / "manifest.json").exists():
        existing = read_json(folder / "manifest.json")
        for split in ["train", "validation", "test"]:
            load_split(split, version=version)
        write_json(BENCHMARK / "manifest.json", existing)
        return existing
    manifest = {"version": version, "created_at": utcnow(), "processing_version": PROCESSING_VERSION,
                "acquisition_version": acquired["version"], "indicqa_revision": rev,
                "english_parallel": False, "splits": {}, "split_checksums": {},
                "training_rejected": len(rejected), "training_duplicates_removed": deduplicated,
                "test_records_removed": 0,
                "test_warning_counts": dict(Counter(w for r in test for w in r["validation_warnings"])),
                "test_duplicate_pairs": len(test)-len({(r["context_fingerprint"],r["question_fingerprint"],r["language"]) for r in test}),
                "training_languages_missing": [l for l in LANGUAGES if l not in {r["language"] for r in train}],
                "licenses": acquired["license"],
                "supplemental_training":supplemental_report,
                "split_policy": "IndicQA official test; SQuAD dev held out as test; training documents grouped with seed 42; no parallel English mapping."}
    for name, rows in [("train", train), ("validation", validation), ("test", test)]:
        path = folder / f"{name}.jsonl"
        write_jsonl(path, rows, exclusive=True)
        manifest["splits"][name] = {"total": len(rows), "languages": dict(Counter(r["language"] for r in rows)),
                                    "sources": dict(Counter(r["source_dataset"] for r in rows)),
                                    "answerability": {lang: dict(Counter("answerable" if r["answerable"] else "unanswerable" for r in rows if r["language"] == lang)) for lang in LANGUAGES if any(r["language"] == lang for r in rows)}}
        manifest["split_checksums"][name] = hashlib.sha256(path.read_bytes()).hexdigest()
    write_jsonl(folder / "rejected_training.jsonl", rejected, exclusive=True)
    write_json(folder / "manifest.json", manifest, exclusive=True)
    write_json(BENCHMARK / "manifest.json", manifest)
    if supplemental_report:
        (ROOT/'docs'/'SUPPLEMENTAL_TRAINING_REPORT.md').write_text(
            '# Supplemental training dataset report\n\nThe user explicitly approved adding L3Cube IndicSQuAD as a training-only extension on 7 November 2026. '
            'IndicQA remains the untouched evaluation source. Published IndicSQuAD validation/test files are not used. '
            'Only original training records mapping by preserved IDs to SQuAD v1.1 original training are eligible. '
            'The original full Hindi/Tamil training files are preserved. Selection is capped at 10,000 eligible records per language by a fixed hash of source ID and seed 42, '
            'to bound local preprocessing memory and the planned training workload. This cap does not reduce 7B VRAM requirements. '
            'Matched translated questions and English source documents are grouped before train/validation splitting. '
            'No parallel relationship to IndicQA test questions is asserted.\n\n'
            'The publisher declares CC BY 4.0; original SQuAD attribution/share-alike obligations are also retained. '
            'Translations are publisher-generated and have not been independently human-verified by this project. '
            'Question/context scripts and normalized answer presence are checked. Unknown original IDs, empty translations and mismatches are excluded with actual counts.\n\n'
            '```json\n'+json.dumps({'selection':supplemental_report,'processed_splits':manifest['splits'],'version':version},ensure_ascii=False,indent=2)+'\n```\n\n'
            'Training further selects a reproducible equal-language budget of up to 4,000 usable base examples per language after token-length filtering, '
            'with up to 400 validation examples per language. Source populations are imbalanced; selected and augmented exposure counts will be logged separately during actual training. '
            'No model has been fine-tuned in this preparation phase.\n',encoding='utf-8')
    (ROOT / "docs" / "DATASET_PREPROCESSING_REPORT.md").write_text(
        "# Dataset preprocessing report\n\nGenerated from downloaded records. No synthetic data are included.\n\n"
        + "```json\n" + json.dumps(manifest, ensure_ascii=False, indent=2) + "\n```\n\n"
        + "NFC and whitespace normalization preserve Unicode; original bytes and offsets stay in raw/. "
        + "Question scripts and answer spans are audited. Warnings never remove held-out test records. "
        + "Training quality issues and held-out overlaps are excluded. Connected source documents sharing "
        + "contexts or questions stay in the same split. IndicQA has no training or validation split. "
        + "English SQuAD results must be presented separately from IndicQA results.\n", encoding="utf-8")
    return manifest


def import_training(path: Path, *, source_name: str, license_name: str, source_url: str):
    """Import a separately licensed native/translated QA TRAINING corpus, never replace the test set."""
    if "indicqa" in source_name.lower() or "college" in source_name.lower():
        raise ValueError("IndicQA evaluation records and campus FAQs are forbidden as training inputs.")
    if license_name not in {"cc-by-4.0", "cc-by-sa-4.0", "apache-2.0", "mit", "cc0-1.0"}:
        raise ValueError("Training source license must be reviewed and explicitly supported.")
    if not source_url.startswith("https://"):
        raise ValueError("A public HTTPS provenance URL is required.")
    normalized = []
    for raw in read_jsonl(path):
        if raw.get("split") != "train" or raw.get("original_split") in {"test", "validation", "dev"}:
            raise ValueError("Only original training records may be imported.")
        language = language_code(raw["language"])
        context, question, answer = (normalize(raw[k]) for k in ["context", "question", "reference_answer"])
        if not all([context, question, answer]) or identify_language(question) != language:
            raise ValueError("Imported training row has an empty field or incompatible script.")
        if not raw.get("source_document_id") or not raw.get("original_source_id") or not raw.get("translation_status"):
            raise ValueError("Source document ID, original record ID and translation status are required.")
        normalized.append({
            "benchmark_id": f"{source_name}:{language}:{raw['original_source_id']}", "source_dataset": source_name,
            "language": language, "context": context, "question": question,
            "reference_answer": answer, "reference_answers": raw.get("reference_answers", [answer]),
            "answer_type": raw.get("answer_type", "extractive"), "answerable": True,
            "original_source_id": str(raw["original_source_id"]), "translation_status": raw["translation_status"],
            "split": "train", "original_split": "train", "license": license_name,
            "source_document_id": f"{source_name}:{raw['source_document_id']}",
            "context_fingerprint": digest(canonical(context)), "question_fingerprint": digest(canonical(question)),
            "validation_warnings": [], "provenance": {"url": source_url, "source_file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                                                          "declared_original_training": True}})
    existing = read_jsonl(BENCHMARK / "supplemental_training.jsonl")
    ids = {r["benchmark_id"] for r in existing}
    if len({r["benchmark_id"] for r in normalized}) != len(normalized) or ids & {r["benchmark_id"] for r in normalized}:
        raise ValueError("Duplicate imported source IDs")
    write_jsonl(BENCHMARK / "supplemental_training.jsonl", existing + normalized)
    return {"imported": len(normalized), "languages": dict(Counter(r["language"] for r in normalized)),
            "next": "Run prepare to seal a new dataset version; historical versions remain available."}
