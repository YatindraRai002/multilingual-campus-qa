from __future__ import annotations

from collections import defaultdict
import re

from backend.evaluation.accuracy import answer_scores
from backend.evaluation.hallucination import claim_counts
from backend.evaluation.language_fairness import language_gap
from backend.evaluation.latency import latency_metrics
from backend.evaluation.retrieval import retrieval_scores
from backend.evaluation.statistics import bootstrap_ci, ratio_bootstrap


def metric(values, definition, *, expected=None, unit="percent", scale=100):
    expected = len(values) if expected is None else expected
    valid = bool(values) and len(values) == expected
    return {"value": sum(values)/len(values)*scale if valid else None,
            "numerator": sum(values) if values else 0, "denominator": expected,
            "reviewed_or_scored": len(values), "unit": unit,
            "status": "scored" if valid else "pending", "definition": definition,
            "confidence_interval": bootstrap_ci(values, scale=scale) if valid else None}


def evaluate_group(rows, *, k=4):
    answerable = [r for r in rows if r.get("answerable", True)]
    human_correct = [float(r["annotation"]["correct"] and not r.get("abstained", False))
                     for r in answerable if r.get("annotation")]
    exact, f1 = [], []
    for row in rows:
        # Abstention correctness is represented by the explicit decision, not a translated string match.
        if not row.get("answerable", True):
            em, score = (float(row.get("abstained", False)),) * 2
        else:
            generated = row["generated_answer"] if not row.get("abstained") else ""
            if row.get('retrieval_enabled'):
                generated = re.sub(r'\[S\d+\]','',generated)
            em, score = answer_scores(generated,
                                      row.get("reference_answers", [row["reference_answer"]]), row["language"])
        exact.append(em)
        f1.append(score)
    hallucination = claim_counts(rows)
    recall, reciprocal = retrieval_scores(rows, k)
    retrieval_queries=sum(bool(row.get('retrieval_enabled')) for row in rows)
    result = {
        "count": len(rows), "human_reviewed": sum(r.get("annotation") is not None for r in rows),
        "accuracy": metric(human_correct, "Human-validated correct answerable responses / all answerable responses × 100.", expected=len(answerable)),
        "exact_match": metric(exact, "Best normalized reference exact match; English articles removed only for English."),
        "f1": metric(f1, "Best whitespace-token reference F1 × 100; Indic combining marks preserved."),
        "hallucination_incidence": metric(hallucination["incidents"], "Responses with >=1 human-verified unsupported claim / all non-abstained responses × 100.", expected=hallucination["non_abstained"]),
        "unsupported_claim_rate": {"value": 100*hallucination["unsupported"]/hallucination["total_claims"] if hallucination["complete"] and hallucination["total_claims"] else None,
                                   "numerator": hallucination["unsupported"], "denominator": hallucination["total_claims"],
                                   "status": "scored" if hallucination["complete"] and hallucination["total_claims"] else "pending",
                                   "unit": "percent", "definition": "Human-verified unsupported factual claims / all evaluated factual claims × 100.",
                                   "confidence_interval": ratio_bootstrap(hallucination["claim_pairs"]) if hallucination["complete"] else None},
        "recall_at_k": metric(recall, f"Queries retrieving a relevant document in top {k} / all retrieval queries × 100. Explicitly empty relevance lists contribute zero; missing labels leave the scope pending.",expected=retrieval_queries),
        "mrr": metric(reciprocal, f"Mean reciprocal rank of the first relevant document in top {k}, over all retrieval queries; empty relevance lists contribute zero.",expected=retrieval_queries, unit="ratio", scale=1),
        "abstention_accuracy": metric([float(r.get("abstained", False) == (not r.get("answerable", True))) for r in rows],
                                      "Correct answer/abstain decisions / responses with answerability ground truth × 100."),
        "latency": latency_metrics(rows),
    }
    return result


def evaluate_predictions(rows: list[dict], *, k=4):
    grouped = defaultdict(lambda: defaultdict(list))
    completed = [r for r in rows if r.get("evaluation_status") == "completed"]
    for row in completed:
        grouped[row["source_dataset"]][row["language"]].append(row)
    populations = {}
    for source, languages in grouped.items():
        language_metrics = {language: evaluate_group(records, k=k) for language, records in languages.items()}
        populations[source] = {"languages": language_metrics, "language_performance_gap": language_gap(language_metrics)}
    return {"status": "scored" if completed else "not_performed", "completed_predictions": len(completed),
            "excluded_failed_predictions": len(rows)-len(completed), "populations": populations,
            "definitions_version": "qa-metrics-v3-all-retrieval-queries", "human_metrics_policy": "pending until every eligible response in the scope is reviewed",
            "comparison_note": "English SQuAD and Hindi/Tamil IndicQA are separate populations."}


def recompute_run(database,run_id,*,reason='definitions_replay'):
    """Append a metric snapshot from saved outputs without running model inference."""
    run=database.run(run_id)
    if not run:
        raise ValueError('Experiment not found')
    rows=database.predictions(run_id,limit=1_000_000)
    if not rows:
        raise ValueError('No predictions exist to score')
    k=(run['configuration'].get('ingestion') or {}).get('configuration',{}).get('top_k',4)
    calculated=evaluate_predictions(rows,k=k)
    calculated.update(run_id=run_id,dataset_version=run['dataset_version'],track=run['track'],
                      experiment=run['experiment'],snapshot_reason=reason)
    database.store_metrics(run_id,calculated)
    from backend.reporting import write_run_report
    write_run_report(database,run_id)
    return database.metrics(run_id)
