# Corpus source checks and human review

Campus source verification and human response evaluation are separate processes.

`source_verified` means an official university snapshot exists, its URL/version and exact evidence quotation match, and an explicitly named AI reviewer has checked the FAQ's meaning and campus scope. Machine translations receive `machine_translation_ai_reviewed` only after that check. These records retain `reviewer_kind: ai`, the review method/notes and `human_review_status: pending`. They are never labeled human-verified.

`human_verified` requires an explicitly human reviewer, an attributed review date and reviewed translation status. Pending records and unreviewed machine translations are excluded from indexing. `accepted_verification_statuses` in the sealed retrieval configuration can restrict an index to human-verified records only.

The initial campus study is an **AI-curated, official-source-backed pilot** unless actual human corpus review is recorded. Its validation/test reference questions disclose their reviewer kind and retain pending human review for AI curation. Source document relevance comes from the cited official evidence; it is not a model-generated judgment of another model's answer. Pilot lexical and retrieval scores are conditional on those reference annotations and should not be presented as independently human-certified results.

Factual answer accuracy, hallucination incidence and unsupported-claim rate still require actual human response annotations. AI corpus review never creates those annotations, never marks a response correct, and never fills missing human metrics with zeros. Human scores remain pending according to the existing metric policy.
