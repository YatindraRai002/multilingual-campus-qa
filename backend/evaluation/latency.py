from statistics import mean, median
from collections import defaultdict

from backend.evaluation.statistics import bootstrap_ci, percentile, ratio_bootstrap


def latency_metrics(rows):
    result = {}
    has_batches = any(row.get('generation_batch_id') for row in rows)
    for key in ["total_seconds", "retrieval_seconds", "generation_seconds"]:
        values = [r[key] for r in rows if r.get(key) is not None]
        clusters = defaultdict(list)
        for index,row in enumerate(rows):
            if row.get(key) is not None:
                clusters[row.get('generation_batch_id') or f'individual-{index}'].append(row[key])
        interval = ratio_bootstrap([(sum(v),len(v)) for v in clusters.values()],scale=1,
            resampling_unit='generation_batch') if has_batches else bootstrap_ci(values,scale=1)
        result[key] = {"mean": mean(values) if values else None,
                       "median": median(values) if values else None,
                       "p95": percentile(values, .95), "count": len(values),
                       "measurement_clusters":len(clusters), "mean_ci": interval}
    durations = {}
    token_totals = defaultdict(int)
    for index,row in enumerate(rows):
        key = row.get('generation_batch_id') or f'individual-{index}'
        seconds = row.get('generation_batch_seconds',row.get('generation_seconds',0))
        if key in durations and durations[key]!=seconds:
            raise ValueError('Conflicting durations for the same generation batch')
        durations[key]=seconds
        token_totals[key]+=row.get('output_tokens',0)
    duration = sum(durations.values())
    tokens = sum(r.get("output_tokens", 0) for r in rows)
    result["throughput"] = {"value": tokens / duration if duration else None,
                            "numerator": tokens, "denominator": duration, "unit": "tokens/s",
                            "confidence_interval":ratio_bootstrap([(token_totals[key],seconds) for key,seconds in durations.items()],
                                scale=1,resampling_unit='generation_batch' if has_batches else 'response'),
                            "definition": "Generated tokens / measured generation seconds; batch durations counted once; excludes loading and retrieval."}
    return result
