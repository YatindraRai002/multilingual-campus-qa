# RAG implementation report

Generated from persisted validation and index records: 2026-11-08T23:08:26.502247+00:00.

Selected embedding: **intfloat/multilingual-e5-small**, revision `614241f622f53c4eeff9890bdc4f31cfecc418b3`, on CPU. Both pinned candidates were actually evaluated before selection. The rule maximizes the worst-language MRR on primary validation queries, with document-level deduplication. These choices were carried over unchanged when the follow-up added source documents.

| Candidate | English MRR | Hindi MRR | Tamil MRR | Worst-language MRR |
|---|---:|---:|---:|---:|
| intfloat/multilingual-e5-small | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 | 1.0000 | 0.8542 | 0.0833 | 0.0833 |

These are rankings before the distance gate, with eight positive validation queries per language. The gate is the predeclared 95th percentile of positive relevant-hit distances, pooled across languages. It has no negative-query calibration and is not a calibrated probability of factual correctness.

Selected maximum cosine distance: **0.127405849**. A separate fresh-process check reopened the real persistent index, verified its content checksum and applied this gate:

| Validation language | Recall@4 after gate | MRR after gate |
|---|---:|---:|
| en | 75.00% | 0.7500 |
| hi | 100.00% | 1.0000 |
| ta | 100.00% | 1.0000 |

## Actual ChromaDB index

Collection: `campus_faq_6e044fab88609b53`. Index version: `6e044fab88609b53`. Corpus: `b07405a784a7045c`. Actual FAQ records: **57**; chunks: **57**. The short pilot answers each fit one chunk. Persistent storage is `data/chroma/`.

Chunk budget: 1000 characters with 150 overlap. Combining marks remain attached at chunk boundaries. Embeddings are normalized; multilingual E5 uses its query/passage prefixes. Ranking searches all three languages, then deduplicates by official source document. This cross-language condition matches candidate validation.

Retrieval uses top 4 distinct source documents, a 180-day review-freshness filter, effective-date checks and an aggregate 5500-character context budget. Only configured source-verified or human-verified records are eligible. All current records are explicitly AI source-reviewed and pending human review; the configuration can require human verification for a later index.

## Generation and citations

Campus A/B receive no retrieved context. C/D use this same frozen collection and retrieval settings. Context construction returns the exact subset of hits actually supplied to the model. Citations are resolved only against those source labels. The original model-emitted-v1 policy abstains for missing citations. The current model-or-verbatim-v2 policy additionally attaches a citation when the entire normalized response equals a complete FAQ answer or evidence quote from exactly one supplied source document. Case, repeated whitespace and terminal periods/dandas are ignored; internal punctuation, signs and Indic marks remain. No aliases, substrings, similarity scores or evaluation references enter that decision. Empty evidence, invalid labels, ambiguous matches and unsupported text still cause abstention. Raw model text and citation origin remain recorded. This is provenance formatting, not semantic claim certification.

Each run records its model/adapter revision, test and index versions, actual retrieved sources, context, raw/final answer and monotonic retrieval/generation/total durations. Model and embedder initialization occur outside normal request timers. C/D comparison checks the actual per-question context strings, not just the collection name.

## Metric scope and limitations

Definitions `qa-metrics-v3-all-retrieval-queries` use every retrieval query in Recall@K and MRR. Explicit empty relevance lists contribute zero; missing labels leave the scope pending. With 36 answerable and 9 unanswerable questions, the maximum all-query Recall@4 is 80.00% and maximum MRR is 0.8000, even with perfect positive retrieval.

The index can be rebuilt into a new version after reviewed updates/deletions. Chat refuses a stale index after the active corpus changes. Historical experiment indexes and records remain available. Stable chunk IDs prevent duplicate upserts. Freshness is based on attributed review time, which is not proof of an updated university publication date.

The local 3 GB CUDA allocator policy applies identically to all four campus workers. A real trained-adapter stress check passed six varying/repeated shapes, including 9,216-token inputs with 192 forced output tokens, without clearing the cache between cases. This is allocator-capacity evidence, not a promise of dedicated-memory residency or isolation from other desktop applications.

Actual model results are reported separately in [EVALUATION_REPORT.md](EVALUATION_REPORT.md). Human source/reference certification and human response factuality metrics remain pending. The small pilot, correlated question variants and simple negatives do not establish a production-ready campus policy authority.
