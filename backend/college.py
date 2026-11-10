from __future__ import annotations

import hashlib
import re
from collections import Counter
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.datasets import current_manifest, identify_language, normalize
from backend.db import Database
from backend.modeling import PrerequisiteError
from backend.settings import ROOT, config, digest, read_json, read_jsonl, utcnow, write_json, write_jsonl

COLLEGE = ROOT / "data" / "college_faq"
VERIFIED_STATUSES = ('human_verified','source_verified')


def is_verified(record):
    return record.get('verification_status') in VERIFIED_STATUSES


def require_benchmark_complete(database: Database | None = None):
    database = database or Database()
    manifest = current_manifest()
    if not manifest:
        raise PrerequisiteError("Complete benchmark preparation and the A/B evaluation workflow before collecting campus data.")
    selected = config('model_config')
    runs = [r for r in database.runs(limit=10000) if r["track"] == "benchmark" and r["status"] == "completed" and
            r["dataset_version"] == manifest["version"] and r["configuration"].get("limit_per_language") is None and
            r['configuration'].get('model_id')==selected['model_id'] and r['configuration'].get('model_revision')==selected['revision']]
    baseline = [r for r in runs if r["experiment"] == "A"]
    adapted = [r for r in runs if r["experiment"] == "B"]
    for a in baseline:
        for b in adapted:
            if a["evaluation_fingerprint"] == b["evaluation_fingerprint"] and a["configuration"]["generation"] == b["configuration"]["generation"] and a["configuration"]["model_revision"] == b["configuration"]["model_revision"]:
                return
    raise PrerequisiteError("Campus acquisition is gated until a complete paired benchmark A/B evaluation exists. No campus policy data have been fabricated.")


def official_url(url: str) -> bool:
    parsed = urlparse(url)
    return (parsed.scheme == "https" and parsed.hostname in config("sources")["allowed_hosts"]
            and not parsed.username and not parsed.password and parsed.port in {None,443})


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip = 0
        self.parts = []
    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self.skip += 1
    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"}:
            self.skip = max(0,self.skip-1)
    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def collect_sources():
    require_benchmark_complete()
    registry = config("sources")
    results = []
    with httpx.Client(timeout=60, follow_redirects=False) as client:
        for source in registry["sources"]:
            url = source["url"]
            # Every redirect is revalidated before fetching to prevent requests to private hosts.
            for _ in range(5):
                if not official_url(url):
                    raise ValueError(f"Only the configured official HTTPS university hosts are allowed: {url}")
                response = client.get(url, headers={"User-Agent": "CampusQAResearch/0.1 (public university research)"})
                if response.is_redirect:
                    url = str(response.url.join(response.headers["location"]))
                else:
                    break
            response.raise_for_status()
            if "text/html" not in response.headers.get("content-type", ""):
                raise ValueError("Use a reviewed text extraction for non-HTML sources; do not silently parse PDFs as HTML.")
            parser = TextExtractor()
            parser.feed(response.text)
            content = normalize(" ".join(parser.parts))
            document_hash = hashlib.sha256(response.content).hexdigest()
            document_id = f"{source['id']}-{document_hash[:16]}"
            folder = COLLEGE / "documents" / document_id
            if not folder.exists():
                folder.mkdir(parents=True)
                (folder/"original.html").write_bytes(response.content)
                (folder/"text.txt").write_text(content,encoding="utf-8")
                write_json(folder/"metadata.json", {"source_document_id": document_id, "source_url": url,
                           "source_title": source["title"], "captured_at": utcnow(), "document_version": document_hash,
                           "category": source["category"], "status": "captured_pending_faq_review"},exclusive=True)
            results.append(read_json(folder/"metadata.json"))
    return results


class FAQ(BaseModel):
    model_config = ConfigDict(extra="forbid")
    faq_id: str = Field(min_length=1,max_length=200)
    canonical_question: str = Field(min_length=3,max_length=4000)
    language: str = Field(pattern="^(en|hi|ta)$")
    answer: str = Field(min_length=1,max_length=30000)
    category: str = Field(min_length=1,max_length=100)
    source_url: str
    source_title: str = Field(min_length=1,max_length=500)
    source_document_id: str = Field(pattern="^[a-zA-Z0-9_-]{1,200}$")
    verification_status: str = Field(pattern="^(human_verified|source_verified|unverified_translation|pending)$")
    verified_at: datetime | None = None
    verified_by: str | None = None
    document_version: str = Field(min_length=1)
    effective_date: date | None = None
    translation_status: str = Field(pattern="^(native|human_translation|machine_translation_reviewed|machine_translation_ai_reviewed|machine_translation_unreviewed)$")
    reviewer_kind: str | None = Field(default=None,pattern='^(human|ai)$')
    review_method: str | None = Field(default=None,pattern='^(human_review|official_snapshot_ai_review)$')
    human_review_status: str | None = Field(default=None,pattern='^(pending|reviewed)$')
    review_notes: str = Field(default='',max_length=4000)
    evidence_quote: str = Field(min_length=1)
    campus: str = "Kattankulathur"

    @field_validator("source_url")
    @classmethod
    def check_url(cls, value):
        if not official_url(value):
            raise ValueError("FAQ citations must use a registered official university HTTPS host.")
        return value


def validate_faq(record: dict):
    faq = FAQ.model_validate(record)
    if faq.campus != "Kattankulathur":
        raise ValueError("This experiment targets the Kattankulathur campus only.")
    if faq.verification_status in VERIFIED_STATUSES:
        if not faq.verified_by or not faq.verified_at or faq.verified_at.tzinfo is None:
            raise ValueError("Verification requires a named reviewer and timezone-aware timestamp.")
        if faq.verified_at > datetime.now(timezone.utc):
            raise ValueError("Verification cannot be dated in the future.")
        if faq.translation_status == "machine_translation_unreviewed":
            raise ValueError("Unreviewed translations cannot be verified.")
        if faq.verification_status=='human_verified':
            if faq.reviewer_kind!='human' or faq.review_method not in {None,'human_review'}:
                raise ValueError('Human verification requires an explicitly human reviewer')
            if faq.translation_status=='machine_translation_ai_reviewed' or faq.human_review_status=='pending':
                raise ValueError('AI-only translation review cannot be recorded as human verification')
            faq.human_review_status='reviewed'
        else:
            if faq.reviewer_kind!='ai' or faq.review_method!='official_snapshot_ai_review' or not faq.review_notes.strip():
                raise ValueError('Source verification requires explicit AI review provenance and review notes')
            if faq.human_review_status!='pending':
                raise ValueError('AI source review must retain pending human-review status')
            if faq.translation_status not in {'native','machine_translation_ai_reviewed'}:
                raise ValueError('AI source review must explicitly identify its machine-reviewed translation status')
    if identify_language(faq.canonical_question) != faq.language:
        raise ValueError("Question script does not match the declared language; manual review required.")
    if identify_language(faq.answer) != faq.language:
        raise ValueError("Answer script does not match the declared language; manual review required.")
    folder = COLLEGE / "documents" / faq.source_document_id
    source = read_json(folder/"metadata.json")
    if not source or not (folder/"text.txt").exists():
        raise ValueError("The original official source snapshot must exist before importing FAQs.")
    if source["source_url"] != faq.source_url or source["document_version"] != faq.document_version:
        raise ValueError("FAQ source version does not match its captured source.")
    if normalize(faq.evidence_quote) not in normalize((folder/"text.txt").read_text(encoding="utf-8")):
        raise ValueError("The reviewed evidence quote is absent from the official source snapshot.")
    return faq.model_dump(mode="json")


def seal_corpus(records: list[dict]):
    ids = [(r["faq_id"],r["language"]) for r in records]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate FAQ ID/language pairs")
    version = digest(sorted(records,key=lambda r:(r["faq_id"],r["language"])))[:16]
    folder = COLLEGE / "versions" / version
    manifest = {"version": version, "created_at": utcnow(), "count": len(records),
                "languages": dict(Counter(r["language"] for r in records)),
                "verification": dict(Counter(r["verification_status"] for r in records)),
                "eligible_verified_count":sum(is_verified(r) for r in records),
                "human_verified_count":sum(r['verification_status']=='human_verified' for r in records),
                "reviewer_kinds":dict(Counter(r.get('reviewer_kind') or 'unreviewed' for r in records)),
                "records_sha256": digest(records), "campus": "Kattankulathur"}
    if not (folder/"manifest.json").exists():
        write_jsonl(folder/"faq.jsonl",records,exclusive=True)
        write_json(folder/"manifest.json",manifest,exclusive=True)
    else:
        manifest = read_json(folder/"manifest.json")
    write_json(COLLEGE/"manifest.json",manifest)
    return manifest


def import_faq(path: Path):
    require_benchmark_complete()
    records = [validate_faq(r) for r in read_jsonl(path)]
    return seal_corpus(records)


def delete_document(document_id: str):
    require_benchmark_complete()
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,200}",document_id):
        raise ValueError("Invalid document ID")
    current = read_json(COLLEGE/"manifest.json")
    if not current:
        raise ValueError("No corpus exists")
    records = read_jsonl(COLLEGE/"versions"/current["version"]/"faq.jsonl")
    kept = [r for r in records if r["source_document_id"] != document_id]
    if len(kept) == len(records):
        raise ValueError("Document is absent from the current corpus")
    return seal_corpus(kept)


def college_summary():
    return read_json(COLLEGE/"manifest.json", {"count": 0, "languages": {}, "verification": {},
                                               "status": "awaiting_benchmark_workflow",
                                               "message": "Verified campus corpus collection starts after the benchmark A/B workflow."})


def seal_campus_test(path: Path):
    require_benchmark_complete()
    manifest = read_json(COLLEGE/"manifest.json")
    if not manifest:
        raise ValueError("Import the verified FAQ corpus first")
    faqs = read_jsonl(COLLEGE/"versions"/manifest["version"]/"faq.jsonl")
    documents = {r["source_document_id"] for r in faqs if is_verified(r)}
    rows = read_jsonl(path)
    if not rows or len({r.get("question_id") for r in rows}) != len(rows):
        raise ValueError("Campus test questions must be non-empty with unique question IDs")
    for row in rows:
        if row.get("split") != "test" or not row.get("reviewer") or row.get("language") not in {"en","hi","ta"}:
            raise ValueError("A reviewed test split with supported language labels is required")
        if row.get('reviewer_kind') not in {'human','ai'}:
            raise ValueError('Campus reference questions must disclose human or AI review provenance')
        if row['reviewer_kind']=='ai' and row.get('human_review_status')!='pending':
            raise ValueError('AI-curated reference questions must retain pending human review')
        if type(row.get("answerable")) is not bool or not isinstance(row.get("relevant_document_ids"),list):
            raise ValueError("Explicit answerability and relevant document ID annotations are required")
        if row["answerable"] and (not row.get("reference_answer") or not row["relevant_document_ids"]):
            raise ValueError("Answerable campus questions need a ground-truth answer and relevant source IDs")
        if not set(row["relevant_document_ids"]).issubset(documents):
            raise ValueError("Ground-truth relevance refers to an unverified or missing document")
        if identify_language(row.get("question","")) != row["language"]:
            raise ValueError("Campus question script mismatch")
        row.update(benchmark_id=row["question_id"],source_dataset="SRM-KTR-source-reviewed-campus",context="",
                   reference_answers=row.get("reference_answers",[row.get("reference_answer","")]),
                   reference_answer=row.get("reference_answer",""), split="test")
    version = digest({"corpus":manifest["version"],"questions":rows})[:16]
    target = COLLEGE/"test_versions"/version
    if not target.exists():
        write_jsonl(target/"test.jsonl",rows,exclusive=True)
        write_json(target/"manifest.json",{"version":version,"corpus_version":manifest["version"],"count":len(rows),
                    "test_checksum":digest(rows),"created_at":utcnow(),
                    "reference_annotation_policy":{'reviewer_kinds':dict(Counter(r['reviewer_kind'] for r in rows)),
                        'human_reference_review_complete':all(r['reviewer_kind']=='human' for r in rows),
                        'response_factuality_metrics':'pending until actual human response annotations exist'}},exclusive=True)
    write_json(COLLEGE/"test_manifest.json",read_json(target/"manifest.json"))
    return read_json(target/"manifest.json")
