def retrieval_scores(rows, k):
    # [] is an explicitly labelled query with no relevant document, not missing gold.
    # Missing labels stay unscored; the caller retains all queries in its denominator.
    eligible = [r for r in rows if r.get("retrieval_enabled") and isinstance(r.get("relevant_document_ids"),list)]
    recalls, reciprocal = [], []
    for row in eligible:
        relevant = set(row["relevant_document_ids"])
        retrieved = [h["source_document_id"] for h in row.get("retrieved", [])][:k]
        ranks = [i for i, doc in enumerate(retrieved, start=1) if doc in relevant]
        recalls.append(float(bool(ranks)))
        reciprocal.append(1 / min(ranks) if ranks else 0.0)
    return recalls, reciprocal
