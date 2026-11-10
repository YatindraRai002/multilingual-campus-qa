# Final research report and project handover

Generated from audited stored records: 2026-11-08T23:28:35.764055+00:00.

The implementation, local GPU QLoRA training, full paired benchmark evaluation, two four-arm campus experiments, dashboard and live multilingual chat are complete. **10 model runs produced 28,274 successful predictions, with zero failed predictions.** Independent human source/reference certification and response factuality annotations remain pending. The brief explicitly permits those metrics to remain unscored when human labels are unavailable.

## Scope and benchmark

The user explicitly authorized **Qwen/Qwen2.5-1.5B-Instruct** for the laptop RTX 2050 (4 GiB), replacing the original 7B design. The original 7B profile is archived and was not run. The separate approved L3Cube IndicSQuAD training extension supplies Hindi/Tamil training data; AI4Bharat IndicQA stays test-only. English SQuAD v1.1 is a separate established extractive QA population because a reliable parallel English mapping was not established. Cross-language scores are not a controlled translation comparison.

Prepared dataset: `acbff74f81c1a1d1`. Full original test populations and contexts were retained.

| Language | Prepared train | Validation | Test | Test source | Answerable / unanswerable |
|---|---:|---:|---:|---|---:|
| English | 78,437 | 8,961 | 10,570 | SQuAD v1.1 official dev | 10,570 / 0 |
| Hindi | 8,954 | 1,044 | 1,547 | AI4Bharat IndicQA official test | 1,052 / 495 |
| Tamil | 8,950 | 1,047 | 1,804 | AI4Bharat IndicQA official test | 1,277 / 527 |

Totals: 96,341 train / 11,052 validation / 13,921 test. Preprocessing removed 197 training duplicates and rejected 9 quality/overlap records. Original test quality warnings are preserved. [Selection rationale](BENCHMARK_SELECTION.md), [dataset audit](BENCHMARK_DATASET_REPORT.md) and [training-source extension](SUPPLEMENTAL_TRAINING_REPORT.md) give revisions, licenses and grouping rules.

## Actual local training

Training `7e800833-02fb-4f7f-88e0-883f7fd4dfa3` completed **106 optimizer steps / two epochs** in **58.90 minutes**. Validation selected checkpoint 80, loss **0.346077**. Peak allocated CUDA memory: **2.435 GiB**.

| Language | Selected base training examples | Training-only abstention additions | Validation examples |
|---|---:|---:|---:|
| en | 256 | 25 | 32 |
| hi | 256 | 17 | 32 |
| ta | 256 | 26 | 32 |

Actual selected training set: 836 examples including 68 abstention additions; validation: 96. Selection is language balanced before augmentation; augmentation creates slightly different final language counts. The complete prepared corpus was not used for training. Overlength examples were filtered on train/validation only.

Configuration: NF4 double quantization, FP16, rank 8, alpha 16, dropout 0.05; q/k/v/o and gate/up/down projections; learning rate 1e-4, batch 1, gradient accumulation 16, sequence length 1,024, two epochs, warmup 0.03, weight decay 0.01, paged AdamW 8-bit, gradient checkpointing and seed 42. Official Qwen chat formatting and assistant-only loss are used. No campus FAQ was used for fine-tuning.

Adapter: `models/qwen2.5-1.5b/lora_adapter/7e800833-02fb-4f7f-88e0-883f7fd4dfa3/`

Adapter tree SHA-256: `3e2e65278413ed82c219d9b0c60c88cea0c1bfc22243f6af9772d13df1b2798d`. The real adapter passed finite-tensor, nonzero-update and checksum validation. The earlier 26-step protocol-invalid augmentation attempt is preserved and excluded.

## Full matched benchmark results

A = original model; B = same base plus the valid adapter. Both use the same complete questions, contexts, references, prompt, deterministic generation (maximum 192 new tokens), 9,216-token input capacity and batching. The original long B worker completed naturally, uninterrupted, as requested.

| Language / population | A EM | B EM | A F1 | B F1 (95% CI) | F1 change, points |
|---|---:|---:|---:|---:|---:|
| en | 38.79 | 77.52 | 62.77 | 86.08 (85.49–86.66) | +23.31 |
| hi | 16.74 | 28.83 | 27.56 | 39.22 (36.89–41.45) | +11.66 |
| ta | 5.10 | 14.41 | 13.20 | 20.59 (18.89–22.36) | +7.39 |

These are reference lexical scores calculated by the backend, including answerability handling, rather than human factual accuracy. The intervals resample responses, not source documents; correlated questions and possible base-model pretraining exposure limit interpretation. No paired significance claim is made.

## Original campus experiment: 63 questions

Test `a75705ed443380de`, corpus `652d19bfd9f0b4cc`, index `d7d31923b9ecac7f`; 21 questions per language, including 3 unanswerable.

A/B receive no campus context; C/D use the same actual retrieved context. C = original + RAG; D = LoRA + RAG.

| Arm | English EM / F1 | Hindi EM / F1 | Tamil EM / F1 | Final abstentions |
|---|---:|---:|---:|---:|
| A | 0.00 / 20.85 | 0.00 / 11.82 | 0.00 / 11.48 | 0 / 63 |
| B | 14.29 / 14.29 | 14.29 / 14.29 | 14.29 / 14.29 | 61 / 63 |
| C | 14.29 / 14.29 | 14.29 / 14.29 | 14.29 / 14.29 | 63 / 63 |
| D | 14.29 / 14.29 | 14.29 / 14.29 | 14.29 / 14.29 | 63 / 63 |

**Negative result preserved:** both C and D abstained on all 63 questions. The model often omitted the required source label. The original guard rejected 51 C and 50 D responses for missing/invalid citations; 12 per arm lacked sufficient retrieval, and D also had one model abstention. Their 14.29% EM/F1 comes solely from the unanswerable cases. These original outputs and metrics were not rewritten.

| RAG retrieval, all-query denominator | English Recall@4 / MRR | Hindi Recall@4 / MRR | Tamil Recall@4 / MRR |
|---|---:|---:|---:|
| Same C/D evidence | 61.90% / 0.619 | 85.71% / 0.833 | 85.71% / 0.833 |

## Citation-policy follow-up: 45 fresh questions

Test `29ed6c44573105ff`, corpus `b07405a784a7045c`, index `6e044fab88609b53`; 15 questions per language, including 3 unanswerable. Six new test source pages are disjoint from the entire original FAQ corpus and validation source pages.

A/B receive no campus context; C/D use the same actual retrieved context. C = original + RAG; D = LoRA + RAG.

| Arm | English EM / F1 | Hindi EM / F1 | Tamil EM / F1 | Final abstentions |
|---|---:|---:|---:|---:|
| A | 0.00 / 17.20 | 0.00 / 12.07 | 0.00 / 11.53 | 0 / 45 |
| B | 20.00 / 20.00 | 20.00 / 20.00 | 20.00 / 20.00 | 45 / 45 |
| C | 80.00 / 80.00 | 66.67 / 66.67 | 46.67 / 49.63 | 14 / 45 |
| D | 80.00 / 80.00 | 40.00 / 40.00 | 53.33 / 53.33 | 21 / 45 |

The frozen extension permits citation attribution only when the entire answer exactly matches a complete answer or evidence quote from exactly one supplied source, after limited case/whitespace/terminal-period normalization. It never uses gold references, aliases or substring/similarity matching. Internal punctuation and Indic marks are preserved; unknown labels and ambiguous/unmatched answers still abstain. Raw model text and citation origin remain recorded. Exact provenance does not certify semantic correctness.

Within this fresh population, D ties C in English, scores lower in Hindi and higher in Tamil. The small sample does not establish a general advantage for LoRA + RAG. Original/follow-up percentages are not a paired causal estimate of the citation change: both the questions and corpus differ. See [the frozen amendment](CITATION_POLICY_AMENDMENT.md).

| RAG retrieval, all-query denominator | English Recall@4 / MRR | Hindi Recall@4 / MRR | Tamil Recall@4 / MRR |
|---|---:|---:|---:|
| Same C/D evidence | 60.00% / 0.600 | 80.00% / 0.800 | 80.00% / 0.800 |

## Retrieval and source review

Current Chroma collection: `campus_faq_6e044fab88609b53`, persisted at `data/chroma/`, with **57 chunks / 57 FAQs (19 per language), from 19 official source pages**. All are explicitly AI source-reviewed; human-verified count is zero. Hindi/Tamil translation provenance remains `machine_translation_ai_reviewed`, human review pending. Original public HTML/text snapshots and SHA metadata are retained locally; personal portal information is excluded.

Embedding candidates were evaluated on 24 validation questions before primary campus inference. E5-small scored 100% Recall@4 / 1.0 MRR in each language before the distance gate; multilingual MiniLM's Tamil Recall@4 was 25% / MRR 0.0833. The declared worst-language MRR rule selected E5-small.

Pinned `intfloat/multilingual-e5-small`, revision `614241f622f53c4eeff9890bdc4f31cfecc418b3`; CPU embeddings, normalized cosine, query/passage prefixes, cross-language search, distinct-source deduplication, top K 4, distance cutoff 0.12740584881953368, maximum context 5,500 characters, chunk size 1,000/overlap 150, source-age limit 180 days. The threshold is the original validation-positive 95th percentile; no negative calibration or test-based retuning was performed. The same settings and original validation queries were retained in the follow-up.

Fresh-process persisted-index validation after the cutoff:

| Language | Validation queries | Recall@4 | MRR |
|---|---:|---:|---:|
| en | 8 | 75.00% | 0.750 |
| hi | 8 | 100.00% | 1.000 |
| ta | 8 | 100.00% | 1.000 |

Empty relevance lists count zero in all-query retrieval metrics. Thus the follow-up's 12 answerable / 15 total questions per language impose a maximum Recall@4 of 80%, even with perfect answerable retrieval. Future/personal negative questions are relatively easy; harder negative validation is still required.

## Timing and memory

Model loading is timed separately. Backend results contain measured retrieval, generation and end-to-end mean, median, P95, throughput and confidence intervals. Benchmark batches count their shared duration only once for throughput, and timing intervals resample whole batches. No timing values were replaced after the run.

| Benchmark arm | Language | Mean / median / P95 request seconds | Generated tokens / second |
|---|---|---:|---:|
| A | en | 2.404 / 2.132 / 4.638 | 22.027 |
| A | hi | 5.265 / 4.546 / 12.509 | 7.926 |
| A | ta | 6.845 / 5.813 / 17.793 | 9.619 |
| B | en | 1.690 / 1.460 / 3.166 | 12.713 |
| B | hi | 15.277 / 8.294 / 33.902 | 0.931 |
| B | ta | 40.423 / 35.124 / 95.554 | 0.753 |

The long B run encountered Windows shared GPU memory, severe host RAM pressure and a competing Ollama model. The user kept it uninterrupted and paused the other project themselves; no other project's process was stopped. One disclosed worker working-set trim is documented in the responsible-AI report. Resource contention changed during execution, so raw A/B timings cannot isolate adapter overhead.

All eight campus runs used the same 75% CUDA allocator budget (3,220,832,256 bytes), with actual peak reserved memory below that budget. A separate six-case, repeated-shape adapter capacity check, including a 9,216-token input and 192 forced output tokens, passed without clearing cache between cases; peak reserved memory was 3,066,036,224 bytes. Allocator measurements do not establish exclusive GPU use or dedicated-memory residency.

## Traceable run IDs

| Track | Arm | Run UUID | Successful predictions |
|---|---|---|---:|
| benchmark | A | `013018a0-f42d-418d-8de8-922d7ca8e728` | 13921 |
| benchmark | B | `fc7c6a02-bb45-4aed-8ecb-35b2611ddb07` | 13921 |
| primary_campus | A | `7397049e-5b46-4f77-9362-6a4d82a50252` | 63 |
| primary_campus | B | `82540012-8fa2-4827-8b33-8f199248da88` | 63 |
| primary_campus | C | `168585c5-3777-4bac-aa51-8aab3151a3c5` | 63 |
| primary_campus | D | `d9f859af-917e-4cf9-b6ab-574b8933ca99` | 63 |
| followup_campus | A | `7f661f59-cb10-4fc7-a2da-69e4a3a213c5` | 45 |
| followup_campus | B | `8448fdf6-04aa-40d8-ba1f-30695f2977e7` | 45 |
| followup_campus | C | `5b593ab6-cca9-4cb2-b727-58ca6c12834f` | 45 |
| followup_campus | D | `54ab8518-0d9a-4a4d-9fbc-8270e3ff2ad3` | 45 |

All metric definitions: `qa-metrics-v3-all-retrieval-queries`. Historical metric revisions are retained. The v3 benchmark replay changed no lexical, abstention or timing values. The final read-only audit verified paired populations, actual C/D contexts, adapter identity, source citation provenance, memory policy, frozen follow-up code hashes and unchanged primary metric snapshots.

## Application and validation

**103 Python tests and 3 Microsoft Edge browser tests passed.** The browser checks actual stored results, training loss, review forms, mobile navigation and a real browser → API → local GPU → cited-answer flow. Desktop, training, mobile and chat screenshots were inspected. Four additional live API requests tested English/Hindi/Tamil validation questions and an unknown future request: English/Tamil returned citations, the Hindi wording safely abstained, and the unknown request abstained. These interactions were unscored; prediction, annotation and research-run counts stayed unchanged.

The dashboard includes benchmark/source provenance, model and adapter details, real loss curves, asynchronous evaluation, matched comparisons, prediction evidence, human review, exports and versioned reports. All research scores are supplied by the backend. Human accuracy, hallucination incidence, unsupported-claim rate and human-accuracy language gaps remain **Pending**: no human annotations were fabricated.

## Open and reproduce

The verification preview is temporary. Start the project from PowerShell:

```powershell
Set-Location 'D:\shameek RAI'
& '.\.venv\Scripts\python.exe' -m backend.cli serve --port 8765
```

Open http://127.0.0.1:8765 (API docs: `/docs`). The service binds to localhost and uses local models; no hosted inference API or key is required. The README and [reproduction guide](REPRODUCIBILITY.md) contain installation, data acquisition, training, ingestion, new-run and export commands. Preserve immutable source snapshots and versioned data to reproduce historical campus runs; live university pages can change.

```powershell
& '.\.venv\Scripts\python.exe' -m scripts.validate_final_outputs
& '.\.venv\Scripts\python.exe' -m pytest
npm run test:browser
powershell -File '.\scripts\bundle.ps1'
```

`results/campusqa-source.zip` contains source, configuration, reports, reviewed campus JSONL/curation and pinned benchmark/training-source acquisition manifests. Benchmark records are reacquired with `acquire` and `prepare`. It excludes environments, caches, model/adapter weights, SQLite, Chroma, full benchmark records, full prediction logs and raw campus HTML. The working project's trained adapter, local database, vector index and original snapshots remain on D:. This is a source handoff, not a fully provisioned runtime backup.

## Repository structure

```text
backend/       FastAPI, model/training, datasets, Chroma, evaluation, SQLite, study coordinator
frontend/      Responsive HTML/CSS/JavaScript dashboard and chat
config/        Pinned active 1.5B settings; archived 7B profiles
data/          Original and versioned benchmarks, campus snapshots/corpora/tests, Chroma, SQLite
models/        Independent checkpoints and valid LoRA adapter
results/       Predictions, metric revisions, training, comparisons, audits, screenshots, source archive
docs/          Methodology, amendments, limitations, metrics and reproduction
scripts/       Setup, acquisition helpers, verification, reports and source packaging
tests/         Isolated Python tests and real Edge browser checks
notebooks/     Archived external-GPU handoff reference
```

## Remaining research limits

The amended experiment establishes lexical benchmark gains for this 1.5B model and budget. It does not establish 7B performance, independent human factual accuracy, lower hallucination, language fairness or a consistent advantage of LoRA over base RAG. Campus facts and references are AI reviewed, narrow, correlated and small; native-speaker source/translation certification and human claim reviews are still needed. Exact copied text can be irrelevant to a question. Lexical F1 is sensitive to Indic morphology. Confidence intervals do not adjust for source-document correlation. Source freshness is based on archived published pages rather than an on-site policy audit. This is a local research pilot, with no public production deployment.
