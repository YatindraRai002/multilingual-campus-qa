# Evaluation report

Updated from persisted records: 2026-11-08T23:11:53.350503+00:00.

The active study uses the user-approved Qwen2.5-1.5B model on the local GPU. Original 7B settings are archived; 1.5B outcomes are not 7B outcomes.

English SQuAD and Hindi/Tamil IndicQA are separate evaluation populations. Benchmark and campus tracks are reported separately. No cross-source aggregate accuracy is computed.

Human factuality metrics remain **Pending** until all eligible responses in their scope have actual human annotations. EM and F1 measure reference overlap and must not be relabeled semantic accuracy.

## Benchmark track

### Experiment B — fc7c6a02-bb45-4aed-8ecb-35b2611ddb07

Status: **completed**. Persisted predictions: 13,921/13,921. Dataset: `acbff74f81c1a1d1`. Model: `Qwen/Qwen2.5-1.5B-Instruct`.

Values in brackets are 95% bootstrap confidence intervals, when available.

| Source population | Language | Completed | EM | F1 | Human accuracy | Hallucination incidence |
|---|---|---:|---:|---:|---:|---:|
| SQuAD-v1.1 | en | 10,570 | 77.52% [76.75, 78.33] | 86.08% [85.49, 86.66] | Pending | Pending |
| ai4bharat/IndicQA | hi | 1,547 | 28.83% [26.63, 31.09] | 39.22% [36.89, 41.45] | Pending | Pending |
| ai4bharat/IndicQA | ta | 1,804 | 14.41% [12.91, 16.08] | 20.59% [18.89, 22.36] | Pending | Pending |

Full definitions, denominators, retrieval and latency measurements: `/api/experiments/fc7c6a02-bb45-4aed-8ecb-35b2611ddb07/metrics`. Immutable configuration and predictions: `/api/experiments/fc7c6a02-bb45-4aed-8ecb-35b2611ddb07/export?format=json`.

### Experiment A — 013018a0-f42d-418d-8de8-922d7ca8e728

Status: **completed**. Persisted predictions: 13,921/13,921. Dataset: `acbff74f81c1a1d1`. Model: `Qwen/Qwen2.5-1.5B-Instruct`.

Values in brackets are 95% bootstrap confidence intervals, when available.

| Source population | Language | Completed | EM | F1 | Human accuracy | Hallucination incidence |
|---|---|---:|---:|---:|---:|---:|
| SQuAD-v1.1 | en | 10,570 | 38.79% [37.83, 39.74] | 62.77% [62.04, 63.46] | Pending | Pending |
| ai4bharat/IndicQA | hi | 1,547 | 16.74% [14.80, 18.75] | 27.56% [25.68, 29.56] | Pending | Pending |
| ai4bharat/IndicQA | ta | 1,804 | 5.10% [4.10, 6.15] | 13.20% [11.85, 14.56] | Pending | Pending |

Full definitions, denominators, retrieval and latency measurements: `/api/experiments/013018a0-f42d-418d-8de8-922d7ca8e728/metrics`. Immutable configuration and predictions: `/api/experiments/013018a0-f42d-418d-8de8-922d7ca8e728/export?format=json`.

## Campus track

### Experiment D — 54ab8518-0d9a-4a4d-9fbc-8270e3ff2ad3

Status: **completed**. Persisted predictions: 45/45. Dataset: `29ed6c44573105ff`. Model: `Qwen/Qwen2.5-1.5B-Instruct`.

Reference review provenance: `{"human_reference_review_complete": false, "response_factuality_metrics": "pending until actual human response annotations exist", "reviewer_kinds": {"ai": 45}}`. AI-curated references support pilot overlap/retrieval results; independent human certification and human response factuality scores require actual human review.

Values in brackets are 95% bootstrap confidence intervals, when available.

| Source population | Language | Completed | EM | F1 | Human accuracy | Hallucination incidence |
|---|---|---:|---:|---:|---:|---:|
| SRM-KTR-source-reviewed-campus | en | 15 | 80.00% [60.00, 100.00] | 80.00% [60.00, 100.00] | Pending | Pending |
| SRM-KTR-source-reviewed-campus | hi | 15 | 40.00% [13.33, 66.67] | 40.00% [13.33, 66.67] | Pending | Pending |
| SRM-KTR-source-reviewed-campus | ta | 15 | 53.33% [26.67, 80.00] | 53.33% [26.67, 80.00] | Pending | Pending |

Full definitions, denominators, retrieval and latency measurements: `/api/experiments/54ab8518-0d9a-4a4d-9fbc-8270e3ff2ad3/metrics`. Immutable configuration and predictions: `/api/experiments/54ab8518-0d9a-4a4d-9fbc-8270e3ff2ad3/export?format=json`.

### Experiment C — 5b593ab6-cca9-4cb2-b727-58ca6c12834f

Status: **completed**. Persisted predictions: 45/45. Dataset: `29ed6c44573105ff`. Model: `Qwen/Qwen2.5-1.5B-Instruct`.

Reference review provenance: `{"human_reference_review_complete": false, "response_factuality_metrics": "pending until actual human response annotations exist", "reviewer_kinds": {"ai": 45}}`. AI-curated references support pilot overlap/retrieval results; independent human certification and human response factuality scores require actual human review.

Values in brackets are 95% bootstrap confidence intervals, when available.

| Source population | Language | Completed | EM | F1 | Human accuracy | Hallucination incidence |
|---|---|---:|---:|---:|---:|---:|
| SRM-KTR-source-reviewed-campus | en | 15 | 80.00% [60.00, 100.00] | 80.00% [60.00, 100.00] | Pending | Pending |
| SRM-KTR-source-reviewed-campus | hi | 15 | 66.67% [46.67, 86.67] | 66.67% [46.67, 86.67] | Pending | Pending |
| SRM-KTR-source-reviewed-campus | ta | 15 | 46.67% [20.00, 66.67] | 49.63% [24.44, 71.11] | Pending | Pending |

Full definitions, denominators, retrieval and latency measurements: `/api/experiments/5b593ab6-cca9-4cb2-b727-58ca6c12834f/metrics`. Immutable configuration and predictions: `/api/experiments/5b593ab6-cca9-4cb2-b727-58ca6c12834f/export?format=json`.

### Experiment B — 8448fdf6-04aa-40d8-ba1f-30695f2977e7

Status: **completed**. Persisted predictions: 45/45. Dataset: `29ed6c44573105ff`. Model: `Qwen/Qwen2.5-1.5B-Instruct`.

Reference review provenance: `{"human_reference_review_complete": false, "response_factuality_metrics": "pending until actual human response annotations exist", "reviewer_kinds": {"ai": 45}}`. AI-curated references support pilot overlap/retrieval results; independent human certification and human response factuality scores require actual human review.

Values in brackets are 95% bootstrap confidence intervals, when available.

| Source population | Language | Completed | EM | F1 | Human accuracy | Hallucination incidence |
|---|---|---:|---:|---:|---:|---:|
| SRM-KTR-source-reviewed-campus | en | 15 | 20.00% [0.00, 40.17] | 20.00% [0.00, 40.17] | Pending | Pending |
| SRM-KTR-source-reviewed-campus | hi | 15 | 20.00% [0.00, 40.17] | 20.00% [0.00, 40.17] | Pending | Pending |
| SRM-KTR-source-reviewed-campus | ta | 15 | 20.00% [0.00, 40.17] | 20.00% [0.00, 40.17] | Pending | Pending |

Full definitions, denominators, retrieval and latency measurements: `/api/experiments/8448fdf6-04aa-40d8-ba1f-30695f2977e7/metrics`. Immutable configuration and predictions: `/api/experiments/8448fdf6-04aa-40d8-ba1f-30695f2977e7/export?format=json`.

### Experiment A — 7f661f59-cb10-4fc7-a2da-69e4a3a213c5

Status: **completed**. Persisted predictions: 45/45. Dataset: `29ed6c44573105ff`. Model: `Qwen/Qwen2.5-1.5B-Instruct`.

Reference review provenance: `{"human_reference_review_complete": false, "response_factuality_metrics": "pending until actual human response annotations exist", "reviewer_kinds": {"ai": 45}}`. AI-curated references support pilot overlap/retrieval results; independent human certification and human response factuality scores require actual human review.

Values in brackets are 95% bootstrap confidence intervals, when available.

| Source population | Language | Completed | EM | F1 | Human accuracy | Hallucination incidence |
|---|---|---:|---:|---:|---:|---:|
| SRM-KTR-source-reviewed-campus | en | 15 | 0.00% [0.00, 0.00] | 17.20% [6.79, 28.49] | Pending | Pending |
| SRM-KTR-source-reviewed-campus | hi | 15 | 0.00% [0.00, 0.00] | 12.07% [5.93, 18.62] | Pending | Pending |
| SRM-KTR-source-reviewed-campus | ta | 15 | 0.00% [0.00, 0.00] | 11.53% [3.08, 23.15] | Pending | Pending |

Full definitions, denominators, retrieval and latency measurements: `/api/experiments/7f661f59-cb10-4fc7-a2da-69e4a3a213c5/metrics`. Immutable configuration and predictions: `/api/experiments/7f661f59-cb10-4fc7-a2da-69e4a3a213c5/export?format=json`.

### Experiment D — d9f859af-917e-4cf9-b6ab-574b8933ca99

Status: **completed**. Persisted predictions: 63/63. Dataset: `a75705ed443380de`. Model: `Qwen/Qwen2.5-1.5B-Instruct`.

Reference review provenance: `{"human_reference_review_complete": false, "response_factuality_metrics": "pending until actual human response annotations exist", "reviewer_kinds": {"ai": 63}}`. AI-curated references support pilot overlap/retrieval results; independent human certification and human response factuality scores require actual human review.

Values in brackets are 95% bootstrap confidence intervals, when available.

| Source population | Language | Completed | EM | F1 | Human accuracy | Hallucination incidence |
|---|---|---:|---:|---:|---:|---:|
| SRM-KTR-source-reviewed-campus | en | 21 | 14.29% [0.00, 33.33] | 14.29% [0.00, 33.33] | Pending | Pending |
| SRM-KTR-source-reviewed-campus | hi | 21 | 14.29% [0.00, 33.33] | 14.29% [0.00, 33.33] | Pending | Pending |
| SRM-KTR-source-reviewed-campus | ta | 21 | 14.29% [0.00, 33.33] | 14.29% [0.00, 33.33] | Pending | Pending |

Full definitions, denominators, retrieval and latency measurements: `/api/experiments/d9f859af-917e-4cf9-b6ab-574b8933ca99/metrics`. Immutable configuration and predictions: `/api/experiments/d9f859af-917e-4cf9-b6ab-574b8933ca99/export?format=json`.

### Experiment C — 168585c5-3777-4bac-aa51-8aab3151a3c5

Status: **completed**. Persisted predictions: 63/63. Dataset: `a75705ed443380de`. Model: `Qwen/Qwen2.5-1.5B-Instruct`.

Reference review provenance: `{"human_reference_review_complete": false, "response_factuality_metrics": "pending until actual human response annotations exist", "reviewer_kinds": {"ai": 63}}`. AI-curated references support pilot overlap/retrieval results; independent human certification and human response factuality scores require actual human review.

Values in brackets are 95% bootstrap confidence intervals, when available.

| Source population | Language | Completed | EM | F1 | Human accuracy | Hallucination incidence |
|---|---|---:|---:|---:|---:|---:|
| SRM-KTR-source-reviewed-campus | en | 21 | 14.29% [0.00, 33.33] | 14.29% [0.00, 33.33] | Pending | Pending |
| SRM-KTR-source-reviewed-campus | hi | 21 | 14.29% [0.00, 33.33] | 14.29% [0.00, 33.33] | Pending | Pending |
| SRM-KTR-source-reviewed-campus | ta | 21 | 14.29% [0.00, 33.33] | 14.29% [0.00, 33.33] | Pending | Pending |

Full definitions, denominators, retrieval and latency measurements: `/api/experiments/168585c5-3777-4bac-aa51-8aab3151a3c5/metrics`. Immutable configuration and predictions: `/api/experiments/168585c5-3777-4bac-aa51-8aab3151a3c5/export?format=json`.

### Experiment B — 82540012-8fa2-4827-8b33-8f199248da88

Status: **completed**. Persisted predictions: 63/63. Dataset: `a75705ed443380de`. Model: `Qwen/Qwen2.5-1.5B-Instruct`.

Reference review provenance: `{"human_reference_review_complete": false, "response_factuality_metrics": "pending until actual human response annotations exist", "reviewer_kinds": {"ai": 63}}`. AI-curated references support pilot overlap/retrieval results; independent human certification and human response factuality scores require actual human review.

Values in brackets are 95% bootstrap confidence intervals, when available.

| Source population | Language | Completed | EM | F1 | Human accuracy | Hallucination incidence |
|---|---|---:|---:|---:|---:|---:|
| SRM-KTR-source-reviewed-campus | en | 21 | 14.29% [0.00, 33.33] | 14.29% [0.00, 33.33] | Pending | Pending |
| SRM-KTR-source-reviewed-campus | hi | 21 | 14.29% [0.00, 33.33] | 14.29% [0.00, 33.33] | Pending | Pending |
| SRM-KTR-source-reviewed-campus | ta | 21 | 14.29% [0.00, 33.33] | 14.29% [0.00, 33.33] | Pending | Pending |

Full definitions, denominators, retrieval and latency measurements: `/api/experiments/82540012-8fa2-4827-8b33-8f199248da88/metrics`. Immutable configuration and predictions: `/api/experiments/82540012-8fa2-4827-8b33-8f199248da88/export?format=json`.

### Experiment A — 7397049e-5b46-4f77-9362-6a4d82a50252

Status: **completed**. Persisted predictions: 63/63. Dataset: `a75705ed443380de`. Model: `Qwen/Qwen2.5-1.5B-Instruct`.

Reference review provenance: `{"human_reference_review_complete": false, "response_factuality_metrics": "pending until actual human response annotations exist", "reviewer_kinds": {"ai": 63}}`. AI-curated references support pilot overlap/retrieval results; independent human certification and human response factuality scores require actual human review.

Values in brackets are 95% bootstrap confidence intervals, when available.

| Source population | Language | Completed | EM | F1 | Human accuracy | Hallucination incidence |
|---|---|---:|---:|---:|---:|---:|
| SRM-KTR-source-reviewed-campus | en | 21 | 0.00% [0.00, 0.00] | 20.85% [12.71, 29.30] | Pending | Pending |
| SRM-KTR-source-reviewed-campus | hi | 21 | 0.00% [0.00, 0.00] | 11.82% [7.23, 16.78] | Pending | Pending |
| SRM-KTR-source-reviewed-campus | ta | 21 | 0.00% [0.00, 0.00] | 11.48% [4.56, 19.15] | Pending | Pending |

Full definitions, denominators, retrieval and latency measurements: `/api/experiments/7397049e-5b46-4f77-9362-6a4d82a50252/metrics`. Immutable configuration and predictions: `/api/experiments/7397049e-5b46-4f77-9362-6a4d82a50252/export?format=json`.

## Measurement conditions

Benchmark requests use length-grouped batches of up to four. Each request's latency is its actual batch-completion window; it is not divided by batch size. Throughput counts each shared generation duration once. Model loading is measured separately. Campus requests run singly.

Original test contexts are retained, with a 9,216-token input capacity. Prompts, deterministic generation settings, checkpoint revision, precision, input capacity and batching policy are frozen for paired A/B evaluation.

Failed predictions remain in the run history and exclusion count. A partial or failed run does not establish the completed benchmark required for campus acquisition. Human metrics and one-sample confidence intervals are never imputed.

Detailed metric definitions and limitations: [METRIC_DEFINITIONS.md](METRIC_DEFINITIONS.md).
