# Interim benchmark comparison

> Historical export as of 2026-11-08 10:02 UTC, superseded by the completed [final research report](FINAL_RESEARCH_REPORT.md). Full benchmark B later completed naturally; Tamil is now scored. The text below describes the earlier snapshot, whose immutable export is preserved.

Exported: 2026-11-08T10:02:29.133498+00:00.

**The full experiment is still incomplete.** This read-only export scores only language populations whose full question sets have successful paired A/B outputs. Incomplete populations remain pending. No model is run, no experiment metrics are overwritten, and these test results are not used for selection.

Baseline A: `013018a0-f42d-418d-8de8-922d7ca8e728`. Trained B: `fc7c6a02-bb45-4aed-8ecb-35b2611ddb07`. Dataset: `acbff74f81c1a1d1`. Model: Qwen2.5-1.5B-Instruct (user-approved local amendment).

English SQuAD and Hindi/Tamil IndicQA are separate populations. EM and F1 measure reference overlap; human factuality metrics require actual human response annotations. Brackets show 95% bootstrap intervals; responses sharing a source document can be correlated.

| Population | Language | Paired count | A EM | B EM | A F1 | B F1 |
|---|---|---:|---:|---:|---:|---:|
| SQuAD-v1.1 | en | 10,570 | 38.79% [37.83, 39.74] | 77.52% [76.75, 78.33] | 62.77% [62.04, 63.46] | 86.08% [85.49, 86.66] |
| ai4bharat/IndicQA | hi | 1,547 | 16.74% [14.80, 18.75] | 28.83% [26.63, 31.09] | 27.56% [25.68, 29.56] | 39.22% [36.89, 41.45] |
| Pending | ta | 312/1,804 saved | Pending | Pending | Pending | Pending |

Timing observations were collected on a shared Windows desktop with changing RAM and GPU contention. They do not isolate adapter overhead. Actual batch-completion latency and batch-deduplicated throughput remain in the JSON export.

Both sides here use the same v3 scoring code in memory. The active worker remains uninterrupted on its loaded v2 definitions; registered A/B metrics will both be replayed only after its full completion.
