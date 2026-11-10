# Metric definitions

| Metric | Definition and denominator |
|---|---|
| Answer accuracy | Human-validated correct answerable responses / all answerable responses × 100 |
| Exact match | Best normalized reference exact match across references; explicit unanswerable decisions scored separately |
| Token F1 | Best reference precision/recall harmonic mean on whitespace tokens; Unicode marks preserved |
| Hallucination incidence | Non-abstained responses with at least one human-verified unsupported claim / all non-abstained responses × 100 |
| Unsupported claim rate | Human-verified unsupported factual claims / all evaluated factual claims × 100 |
| Recall@K | Queries with a relevant document in top K / all retrieval queries × 100; explicitly empty relevance lists count as misses |
| MRR | Mean reciprocal rank of the first relevant document in top K, over all retrieval queries; misses and explicitly empty relevance lists contribute zero |
| Language performance gap | Highest minus lowest human-validated language accuracy, within one source dataset |
| Abstention accuracy | Correct answer/abstain decisions / completed responses with answerability ground truth × 100 |
| Mean/median/P95 latency | Statistics over measured completed-request monotonic timing; linear-interpolated P95 |
| Throughput | Sum of actually generated tokens / actual measured generation seconds; excludes retrieval/loading |

Every metric snapshot includes definitions, denominators, coverage and confidence intervals where the sample permits them. Human factuality metrics require complete annotations in the reported source/language scope; partial reviews leave them pending. An abstention is not a correct answer to an answerable question. Error records remain persisted and counted but are excluded from completed-response scores; the run is marked failed if any records failed.

For campus factuality review, human judges may inspect the sealed official reference corpus in every A/B/C/D arm. Closed-book A/B responses can therefore be factually supported even though the model did not receive those documents. The review interface distinguishes supplied model context from reference evidence and loads the original experiment's corpus version. Source support is not inferred from the mere presence or absence of RAG. Citation validity and faithfulness to the supplied context are distinct from factual correctness against authoritative reference sources. Answerable abstentions cannot be annotated or counted as correct answers.

English articles are removed only for English exact-match normalization. Unicode punctuation is removed while Devanagari/Tamil combining marks remain. Validated RAG source labels such as `[S1]` are removed from the content used for EM/F1, while original generated text and citations remain persisted for review. Whitespace tokenization is a limited Tamil/Hindi lexical measure and does not replace human semantic judgment. No cross-dataset aggregate accuracy is computed.

Confidence intervals use seeded bootstrap resampling (1,000 draws, seed 42). Claim-rate bootstrap samples whole responses to keep claims within their response. For batched inference, latency-mean intervals resample entire generation batches, preserving response weighting when batches have different sizes. Throughput intervals resample batch token/duration pairs, counting each actual shared duration once. One independent batch cannot establish an interval even if it contains four responses. Unbatched timing intervals resample responses. Source-document correlation remains a limitation of the lexical/human response bootstrap. Model loading is separately reported and not disguised as ordinary request latency.

The corrected timing uncertainty method was recorded as `qa-metrics-v2-batch-confidence`. Version `qa-metrics-v3-all-retrieval-queries` retains that timing method and makes retrieval denominators follow the requested all-query formula. An explicitly empty relevant-document list is a labelled negative and contributes zero; an absent/unknown label leaves the metric pending while retaining the full query denominator. Thus maximum all-query recall can be below 100% when some questions have no relevant document. Source-reviewed relevance labels disclose AI/human provenance; AI curation is not human certification.

`recompute-metrics <run-id>` replays saved outputs without inference and appends a versioned metric snapshot; original snapshots and predictions remain intact. Comparisons reject mixed metric-definition versions. The original benchmark B worker completed naturally, uninterrupted. Both benchmark runs were then replayed into v3 before campus evaluation; lexical, abstention and timing dictionaries, including intervals, were asserted exactly unchanged. The v3 denominator correction was made before any campus retrieval outcomes existed. All ten completed runs now use the same v3 definition.

Actual comparisons require the same population fingerprint, base revision, prompt, input limit, generation settings and random seed. RAG C/D must also use matching index versions and actual evidence contexts. These checks passed for both completed campus cohorts and the paired benchmark. Campus and benchmark runs cannot be compared as one population; the original and follow-up campus tests also stay separate. Lexical adaptation results are available in the final report. Human factuality and human-accuracy language-gap conclusions remain pending independent annotations.
