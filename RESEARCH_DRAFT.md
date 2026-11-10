# Multilingual QLoRA Adaptation and Grounded Campus Question Answering on a 4 GiB Laptop GPU

## An English, Hindi, and Tamil Pilot Study

**Status:** Working research manuscript; not peer reviewed.  
**Draft date:** 10 November 2026.  
**Author(s) and affiliation(s):** To be confirmed before submission.  
**Code and supporting records:** [multilingual-campus-qa](https://github.com/YatindraRai002/multilingual-campus-qa).  
**Scope:** Actual experiments use Qwen2.5-1.5B-Instruct. The initially proposed 7B experiment was amended for the available hardware and was not executed.

## Abstract

Small language models and retrieval offer a practical route to local multilingual question answering, but benchmark adaptation does not necessarily improve domain-specific grounded responses. We study QLoRA adaptation of Qwen2.5-1.5B-Instruct on a laptop with an NVIDIA RTX 2050 GPU and 4 GiB of dedicated memory. A language-balanced selection of 768 base training examples, augmented with 68 training-only abstention examples, is used for supervised adaptation. We evaluate the original and adapted models on 13,921 held-out questions: English SQuAD v1.1 and separate Hindi and Tamil AI4Bharat IndicQA populations. Token F1 increases from 62.77 to 86.08 in English, 27.56 to 39.22 in Hindi, and 13.20 to 20.59 in Tamil. We then compare original, adapted, retrieval-augmented, and adapted-plus-retrieval configurations on an official-source campus FAQ pilot. In the original 63-question campus test, strict citation enforcement causes both retrieval configurations to abstain on every question. A separately frozen attribution policy is evaluated on 45 fresh questions from six new source documents. Adapted-plus-retrieval F1 is 80.00, 40.00, and 53.33 for English, Hindi, and Tamil, compared with 80.00, 66.67, and 49.63 for original-model retrieval. These results demonstrate lexical benchmark gains and mixed campus transfer. They do not establish human factual accuracy, hallucination reduction, or a consistent advantage from combining QLoRA with retrieval. Independent human source and response reviews remain pending.

**Keywords:** multilingual question answering; small language models; QLoRA; retrieval-augmented generation; English; Hindi; Tamil; campus FAQs; reproducible evaluation.

## 1. Introduction

An institutional question-answering assistant must do more than produce plausible text. It must distinguish campuses, use the relevant published source, preserve policy meaning across languages, and decline requests that its evidence cannot answer. Local execution introduces an additional constraint: model adaptation and inference must share limited GPU and host memory with an ordinary desktop workload.

This study examines two different forms of adaptation. First, supervised QLoRA training adapts a small instruction model to context-grounded multilingual QA. Second, retrieval supplies campus facts at inference time without adding those facts to the model's training set. Keeping these interventions separate allows us to ask whether a benchmark-adapted model also becomes a better consumer of new institutional evidence.

The contribution is an auditable empirical pilot and implementation, rather than a new model architecture or a state-of-the-art claim. We provide a matched benchmark comparison, two explicitly separate campus experiments, a versioned source and retrieval pipeline, and a dashboard that presents backend-computed results and review evidence. We retain an unsuccessful citation-enforcement result instead of replacing it with a successful demonstration.

The research questions are:

1. **RQ1:** Does the selected QLoRA adaptation improve reference-based QA scores within each held-out benchmark population?
2. **RQ2:** Does benchmark adaptation transfer to campus questions when campus FAQs are excluded from training?
3. **RQ3:** Within a fixed campus test, does the adapted model with retrieval outperform the original model with the same retrieved evidence?
4. **RQ4:** What failure modes arise when a small model's generated answers must pass an explicit citation policy?

RQ4 motivates an exploratory follow-up after the original campus failure. Because that follow-up uses new questions and an expanded corpus, it cannot isolate the causal effect of changing the citation policy.

## 2. Background and related work

LoRA freezes pretrained weights and learns low-rank update matrices, reducing the number of trainable parameters during adaptation. We use this established technique rather than introducing a new adapter formulation. [Hu et al., 2021](https://arxiv.org/abs/2106.09685)

QLoRA combines low-rank adaptation with a frozen quantized base model; NF4, double quantization, and paged optimizers are relevant to memory-limited execution. Our implementation follows this general approach at the smaller model scale used here. [Dettmers et al., 2023](https://arxiv.org/abs/2305.14314)

Retrieval-augmented generation combines a language model with external retrieved information. Our system uses a multilingual dense retriever and a versioned FAQ collection; it does not reproduce the original RAG paper's jointly trained architecture. [Lewis et al., 2020](https://arxiv.org/abs/2005.11401)

The Qwen2.5 model family supplies the instruction model used in the experiment. The exact checkpoint is the official 1.5B instruction release, pinned independently of the model-family report. [Qwen et al., 2024](https://arxiv.org/abs/2412.15115), [official model card](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct)

SQuAD provides an established English reading-comprehension population. IndicSQuAD provides a separate translated SQuAD resource for multilingual training. The latter is not the AI4Bharat IndicQA evaluation release used in this study. We keep those source identities and their roles explicit. [Rajpurkar et al., 2016](https://arxiv.org/abs/1606.05250), [Endait et al., 2025](https://aclanthology.org/2025.paclic-1.70/), [AI4Bharat IndicQA release](https://huggingface.co/datasets/ai4bharat/IndicQA)

Multilingual E5 supplies the selected embedding model. Its multilingual design is a starting point, not sufficient evidence of suitability for this corpus; candidate selection is based on the pilot's own retrieval validation queries. [Wang et al., 2024](https://arxiv.org/abs/2402.05672)

## 3. Data and experimental populations

### 3.1 Benchmark sources and splits

AI4Bharat IndicQA is retained as an untouched test-only source for Hindi and Tamil. A reliable parallel English mapping was not established, so English is evaluated separately on the official SQuAD v1.1 development set, reserved as the project's test population. These are not parallel translations, and we do not pool their scores into a controlled cross-language comparison. The project evaluates the specified AI4Bharat component, not every task in the broader, similarly named Indic-QA literature.

Because the selected IndicQA release has no training split, Hindi and Tamil training examples come from the separately documented L3Cube IndicSQuAD extension. Only examples whose preserved question identifiers map to original English SQuAD v1.1 training identifiers are eligible. Published IndicSQuAD development and test files are not used. Training-source documents and canonical question groups are kept together when constructing validation splits, reducing leakage between translated training versions.

**Table 1. Prepared benchmark populations. Prepared counts are distinct from actual training exposure.**

| Language | Prepared train | Validation | Held-out test | Test source | Answerable / unanswerable test |
|---|---:|---:|---:|---|---:|
| English | 78,437 | 8,961 | 10,570 | SQuAD v1.1 official development set | 10,570 / 0 |
| Hindi | 8,954 | 1,044 | 1,547 | AI4Bharat IndicQA official test | 1,052 / 495 |
| Tamil | 8,950 | 1,047 | 1,804 | AI4Bharat IndicQA official test | 1,277 / 527 |
| Total | 96,341 | 11,052 | 13,921 | Separate populations | 12,899 / 1,022 |

Preprocessing preserves Unicode, checks Devanagari and Tamil scripts, retains source identifiers, and detects empty, duplicate, malformed, or mismatched training records. It removes 197 training duplicates and rejects nine quality/overlap records. The complete original evaluation population is retained, including source-quality warnings; test contexts and answers are not repaired or filtered in response to model outputs. The sealed dataset version is `acbff74f81c1a1d1`. Detailed source and licensing provenance is recorded in the [benchmark selection report](docs/BENCHMARK_SELECTION.md) and [acquisition manifest](handoff/benchmark_acquisition.json).

### 3.2 Actual supervised training exposure

After training-only length filtering, a deterministic selection uses 256 base examples and 32 validation examples per language. Additional empty-evidence examples teach abstention using a separate training-only hash-based sampling decision with configured probability 0.1. The realized additions differ by language.

**Table 2. Examples actually selected for the valid training run.**

| Language | Base train | Abstention additions | Total selected train | Validation |
|---|---:|---:|---:|---:|
| English | 256 | 25 | 281 | 32 |
| Hindi | 256 | 17 | 273 | 32 |
| Tamil | 256 | 26 | 282 | 32 |
| Total | 768 | 68 | 836 | 96 |

Selection is balanced before augmentation; the final augmented set is not exactly balanced. The model is not trained on all 96,341 prepared training records. The 1,024-token training limit excludes more long Hindi and Tamil examples than English examples, which may bias the selected training distribution. Test data are not used for augmentation, hyperparameter selection, prompt selection, or checkpoint selection.

An initial augmentation implementation coupled two hashing decisions and produced an invalid selection. That attempt was stopped after 26 optimizer steps, marked protocol-invalid, and excluded. Its history remains preserved. The results below use only the corrected, independently sampled run.

### 3.3 Campus corpus and review provenance

Campus source collection begins only after the full benchmark baseline, training, and matched adapted-model evaluation finish. The target is SRM Institute of Science and Technology, Kattankulathur. The initial corpus contains 39 FAQ records, comprising 13 facts expressed in three languages. The follow-up preserves those records and adds six facts in three languages, producing 57 records from 19 official source pages.

Every FAQ retains an official URL, source document identifier, archived evidence quotation, document version, review timestamp, category, and language. English questions and answers are authored from the source facts; Hindi and Tamil versions are machine translated and explicitly AI reviewed for meaning. All current records are `source_verified` with `reviewer_kind: ai`; none is independently human certified. AI review is not treated as human ground truth. Campus records are never added to the benchmark fine-tuning set.

The pilot emphasizes facility and service identities rather than changing fees, deadlines, current availability, clinical advice, or private student information. Published facts are checked against captured official pages, not independently confirmed through an on-site policy audit. Source URLs and scope are listed in the [campus dataset report](docs/COLLEGE_FAQ_DATASET_REPORT.md).

### 3.4 Campus validation and test separation

Retrieval validation contains 24 questions: two paraphrases for each of four source facts, in three languages. The original campus test contains 54 answerable questions from nine different source facts plus nine clearly out-of-corpus future or personal requests. It therefore has 63 questions, or 21 per language. Validation and test source groups are disjoint, although their facts are available in the retrieval corpus as required for closed-corpus QA.

The follow-up test contains 36 answerable questions from six new source documents plus nine out-of-corpus requests: 45 questions, or 15 per language. Those six documents are disjoint from the entire original FAQ corpus, including validation sources. The original validation queries, embedding choice, and retrieval threshold are retained. References and aliases are fixed before follow-up inference. Every arm within a cohort receives identical questions, each explicitly naming the Kattankulathur campus.

The original and follow-up tests are separate evaluation populations. Their results are never combined or used as a paired before/after estimate.

## 4. Methods and implementation

### 4.1 Model and hardware

The model is `Qwen/Qwen2.5-1.5B-Instruct`, revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`, using its official chat template and tokenizer. The initially proposed 7B checkpoint was replaced before the reported experiment because the laptop has 4 GiB of dedicated GPU memory. Conclusions apply to the amended 1.5B study.

Execution uses an NVIDIA GeForce RTX 2050, an Intel Core i5-11260H CPU, and 23.73 GiB of system RAM under Windows. The environment includes Python 3.11.14, PyTorch 2.7.1 with CUDA 12.6, Transformers 4.57.3, PEFT 0.18.0, bitsandbytes 0.48.2, and ChromaDB 1.3.5. All model execution is local. Shared GPU memory and CPU resources are available to the process; we do not claim that every long-running evaluation remains entirely within dedicated VRAM.

### 4.2 QLoRA configuration

**Table 3. Training configuration and observed completion.**

| Setting | Value |
|---|---|
| Base quantization | NF4, double quantization |
| Compute precision | FP16 |
| LoRA rank / alpha / dropout | 8 / 16 / 0.05 |
| Target projections | q, k, v, o, gate, up, down |
| Learning rate | 1 × 10⁻⁴ |
| Microbatch / gradient accumulation | 1 / 16 |
| Epochs / optimizer steps | 2 / 106 |
| Training sequence limit | 1,024 tokens |
| Optimizer | Paged AdamW, 8 bit |
| Warmup ratio / weight decay | 0.03 / 0.01 |
| Gradient checkpointing | Enabled |
| Random seed | 42 |
| Validation frequency | Every 20 optimizer steps |
| Selected checkpoint | Step 80; validation loss 0.346077 |
| Observed training duration | 58.90 minutes |
| Peak allocated CUDA memory | 2.435 GiB |

Only assistant answer tokens contribute to the causal language-model loss. Checkpoint selection uses the 96 selected validation examples. A memory-saving supervised-logit implementation is checked for loss and gradient equivalence, and explicit grouped-query scaled dot-product attention is checked against reference behavior. These are implementation checks, not independent evidence of model quality. The actual adapter contains 9,232,384 parameters across 392 tensors and passes finite-value, nonzero-update, and checksum validation.

### 4.3 Inference and experimental arms

Generation is deterministic, with sampling disabled, maximum 192 new tokens, repetition penalty 1.0, and seed 42. The inference input capacity is 9,216 tokens; all original benchmark contexts are retained. Benchmark evaluation uses batches of up to four questions with a padded token budget of 4,096, allowing longer prompts to run individually. Input questions, references, base revision, chat prompt, generation settings, and execution configuration are matched between benchmark A and B.

**Table 4. Evidence conditions.**

| Arm | Model weights | Benchmark evidence | Campus evidence |
|---|---|---|---|
| A | Original instruction model | Supplied benchmark context | No campus context |
| B | Same model plus valid LoRA adapter | Same benchmark context | No campus context |
| C | Original instruction model | Not part of the benchmark track | Retrieved official-source FAQ context |
| D | Same model plus valid LoRA adapter | Not part of the benchmark track | Same actual retrieved context as C |

A and B are therefore context-grounded in the benchmark track and closed book in the campus track. Campus C/D comparisons validate the actual per-question context strings, not merely the identity of the vector collection.

### 4.4 Retrieval

Two pinned sentence-embedding candidates are evaluated on the 24 retrieval-validation queries. The selection rule maximizes the lowest language-specific MRR. Multilingual E5-small achieves MRR 1.0 in all three languages before the distance gate; multilingual MiniLM achieves 1.0, 0.8542, and 0.0833 for English, Hindi, and Tamil. E5-small is selected.

Embeddings are computed on CPU, normalized, and stored in ChromaDB. E5 query/passage prefixes are applied. Retrieval searches all three languages, deduplicates by source document, and retains at most four distinct documents. The chunk size is 1,000 characters with overlap 150; each short FAQ in the current collection occupies one chunk. The combined generation context is limited to 5,500 characters. Review freshness is limited to 180 days, with source-version and effective-date checks.

The maximum cosine distance is 0.12740584881953368, the predeclared 95th percentile of positive relevant-hit distances on validation data. No negative-query calibration or test-based threshold tuning is performed. After this gate, fresh-process validation of the persistent index yields Recall@4/MRR of 75%/0.75 for English and 100%/1.0 for Hindi and Tamil. This small validation set does not provide a calibrated probability of correctness.

### 4.5 Citation policies and the exploratory follow-up

The original campus policy, `model-emitted-v1`, requires a valid model-emitted label referring to evidence actually supplied in context. Empty evidence or missing/unknown labels leads to a localized abstention. The prompt requests citations, but compliant source-label generation is not guaranteed.

After the original test exposes a citation failure, a separate policy, `model-or-verbatim-v2`, is frozen before inference on the fresh follow-up test. It retains valid model citations and permits deterministic attribution only when the complete normalized answer equals a complete FAQ answer or evidence quotation from exactly one supplied source document. NFC normalization, case folding, whitespace collapse, and terminal periods/dandas are permitted; internal punctuation, signs, symbols, and Indic combining marks are preserved. Partial, ambiguous, or novel text is rejected. Unknown model labels are not repaired.

Attribution reads no evaluation reference, alias, correctness label, or semantic-similarity score. It preserves the raw generated response and records whether the final citation was emitted by the model or attached through verbatim source attribution. Matching establishes text provenance, not that the copied answer is relevant or true. The follow-up changes the citation policy and corpus/test population while retaining weights, training, prompts, generation, embeddings, and retrieval threshold. Its design and interpretation are documented in the [frozen amendment](docs/CITATION_POLICY_AMENDMENT.md).

## 5. Evaluation and statistical treatment

### 5.1 Lexical QA scores

For answerable questions, exact match compares the normalized prediction against the best reference. Normalization applies NFC, case folding, punctuation removal, and whitespace normalization while preserving Indic combining marks; English articles are removed only for English. Token F1 uses whitespace-token multiset overlap:

$$
P_i = \frac{|T(\hat a_i) \cap T(a_i)|}{|T(\hat a_i)|}, \qquad
R_i = \frac{|T(\hat a_i) \cap T(a_i)|}{|T(a_i)|}, \qquad
F1_i = \frac{2P_iR_i}{P_i+R_i}.
$$

Intersection denotes token multiplicity, and zero overlap gives zero F1. The backend takes the best score across references. An abstention on an answerable question receives zero. For explicitly unanswerable questions, EM and F1 are one if the system abstains and zero otherwise. Valid source labels are removed before lexical comparison, while original text and citations remain recorded. Reported means are multiplied by 100.

This answerability-aware convention matters: an always-abstaining system receives 14.29% on a campus population with three unanswerable questions out of 21, or 20% with three out of 15. Those values are not successful answers to campus facts. Whitespace F1 is sensitive to morphology and wording, especially in Hindi and Tamil, and is not a substitute for semantic factuality review.

### 5.2 Retrieval, abstention, and human factuality

The requested Recall@4 definition is a query hit rate:

$$
\operatorname{Recall@4} = \frac{100}{N_R}\sum_{i=1}^{N_R}
\mathbf{1}[D_i^{(4)} \cap G_i \ne \varnothing], \qquad
\operatorname{MRR@4} = \frac{1}{N_R}\sum_{i=1}^{N_R}\frac{1}{r_i}.
$$

Here, $N_R$ includes all retrieval queries, $G_i$ is the relevant-document set, and the reciprocal rank is zero when no relevant document appears in the first four results. Explicit empty relevance sets contribute zero. Missing relevance labels leave the scope unscored. Therefore, even perfect retrieval of answerable follow-up questions has a maximum all-query Recall@4 of 80%, because only 12 of 15 questions per language have a relevant document. This is not recall calculated only over positive queries.

Abstention accuracy measures the correct answer-versus-abstain decision, independently of whether a non-abstained answer's content is correct. Human factual accuracy, hallucination incidence, and unsupported-claim rate require separate human correctness and claim-support annotations. They remain Pending when the required scope is not reviewed. There are zero human response annotations in the reported study. AI source curation and valid citation syntax never populate those human metrics.

### 5.3 Uncertainty, timing, and completeness

Confidence intervals are 95% percentile bootstrap intervals using 1,000 resamples and seed 42. Lexical intervals resample responses. Questions sharing a source document are correlated, so these intervals may be optimistic; they are not source-clustered intervals or estimates of variation across training seeds. We report no paired significance test or confidence interval for the adaptation difference.

Request, retrieval, and generation durations use monotonic instrumentation. Model and embedding initialization are timed separately. Shared generation-batch durations are counted once for throughput, and benchmark timing intervals resample entire batches. Raw measurements are retained even when desktop contention causes stalls.

Ten evaluation runs complete with 28,274 successful predictions and zero failed predictions: two benchmark runs of 13,921 questions, four original campus runs of 63, and four follow-up runs of 45. This is a count of model responses across repeated populations, not 28,274 unique questions. All scopes use backend definition version `qa-metrics-v3-all-retrieval-queries`. Benchmark metric replay into this version changes no saved model outputs, lexical scores, abstention scores, or timing values.

## 6. Results

### 6.1 Matched benchmark adaptation

**Table 5. Full held-out benchmark results. EM/F1 use a 0–100 scale; differences are percentage points. B intervals describe its F1 mean.**

| Language | Test N | A EM | B EM | A F1 | B F1 | B F1 95% CI | B − A F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| English | 10,570 | 38.79 | 77.52 | 62.77 | 86.08 | 85.49–86.66 | +23.31 |
| Hindi | 1,547 | 16.74 | 28.83 | 27.56 | 39.22 | 36.89–41.45 | +11.66 |
| Tamil | 1,804 | 5.10 | 14.41 | 13.20 | 20.59 | 18.89–22.36 | +7.39 |

The selected adapter improves both lexical metrics within each benchmark population, supporting RQ1 for this run and training budget. The English and Indic populations differ in source, question distribution, and answerability. Their absolute scores and gains cannot establish a controlled language-fairness ranking.

The experiment does not separate changes in answer format from changes in reading comprehension. A model that produces shorter reference-aligned answers can improve EM/F1 without an equivalent improvement in semantic reasoning. An answer-style ablation and independent human review would be needed to distinguish these effects.

### 6.2 Original campus experiment

**Table 6. Original campus test: 63 questions, 21 per language. Each language cell is EM / F1.**

| Arm | English | Hindi | Tamil | Total final abstentions |
|---|---:|---:|---:|---:|
| A: original, closed book | 0.00 / 20.85 | 0.00 / 11.82 | 0.00 / 11.48 | 0 / 63 |
| B: LoRA, closed book | 14.29 / 14.29 | 14.29 / 14.29 | 14.29 / 14.29 | 61 / 63 |
| C: original + retrieval | 14.29 / 14.29 | 14.29 / 14.29 | 14.29 / 14.29 | 63 / 63 |
| D: LoRA + retrieval | 14.29 / 14.29 | 14.29 / 14.29 | 14.29 / 14.29 | 63 / 63 |

The original citation guard rejects every final C/D answer. Arm C has 51 missing/invalid-citation rejections and 12 insufficient-evidence abstentions. Arm D has 50 citation rejections, 12 insufficient-evidence abstentions, and one model abstention. The prompt contains the citation instruction; the failure is not a missing argument in the application. Both RAG arms' 14.29% lexical scores come solely from abstaining on unanswerable questions.

Retrieval itself is not uniformly unsuccessful: C and D have identical Recall@4/MRR of 61.90%/0.619 in English and 85.71%/0.833 in Hindi and Tamil under the all-query denominator. The result identifies a distinction between retrieving a relevant source and returning an answer that satisfies the output contract. Original outputs and metrics are retained unchanged.

### 6.3 Fresh-source citation-policy follow-up

**Table 7. Separate follow-up: 45 fresh questions, 15 per language. Each language cell is EM / F1. These percentages are not paired with Table 6.**

| Arm | English | Hindi | Tamil | Total final abstentions |
|---|---:|---:|---:|---:|
| A: original, closed book | 0.00 / 17.20 | 0.00 / 12.07 | 0.00 / 11.53 | 0 / 45 |
| B: LoRA, closed book | 20.00 / 20.00 | 20.00 / 20.00 | 20.00 / 20.00 | 45 / 45 |
| C: original + retrieval | 80.00 / 80.00 | 66.67 / 66.67 | 46.67 / 49.63 | 14 / 45 |
| D: LoRA + retrieval | 80.00 / 80.00 | 40.00 / 40.00 | 53.33 / 53.33 | 21 / 45 |

Closed-book B abstains on all 45 questions, so its 20% score reflects only the unanswerable fraction. Benchmark adaptation alone therefore does not establish useful closed-book campus transfer for this population. With retrieval, D ties C in English, scores 26.67 F1 points lower in Hindi, and 3.70 points higher in Tamil. The differences are descriptive and based on small, correlated samples.

**Table 8. Follow-up RAG F1 uncertainty from the stored response-bootstrap snapshots.**

| Language | C F1, 95% CI | D F1, 95% CI |
|---|---:|---:|
| English | 80.00, 60.00–100.00 | 80.00, 60.00–100.00 |
| Hindi | 66.67, 46.67–86.67 | 40.00, 13.33–66.67 |
| Tamil | 49.63, 24.44–71.11 | 53.33, 26.67–80.00 |

All 31 non-abstained C responses and all 24 non-abstained D responses receive citations through deterministic verbatim source attribution. No successful model-emitted citation is recorded in this follow-up. Thus the cited answers demonstrate the combined model-and-policy pipeline, not newly learned source-label generation by the model.

C and D again receive identical actual evidence. All-query Recall@4/MRR is 60%/0.600 in English and 80%/0.800 in Hindi and Tamil. The English distance gate excludes some relevant evidence; no threshold is retuned after observing this result.

### 6.4 Resource observations

The valid training run completes in 58.90 minutes with peak allocated CUDA memory of 2.435 GiB. The long adapted benchmark subsequently encounters severe host RAM pressure, Windows shared GPU memory, and a competing model from another project. It completes naturally without interruption or recovery. A single disclosed working-set trim targets only the registered benchmark worker; all measured request durations remain in the results.

**Table 9. Observed benchmark timing under the actual desktop conditions.**

| Arm | Language | Mean request seconds | Median seconds | P95 seconds | Generation tokens/second |
|---|---|---:|---:|---:|---:|
| A | English | 2.404 | 2.132 | 4.638 | 22.027 |
| A | Hindi | 5.265 | 4.546 | 12.509 | 7.926 |
| A | Tamil | 6.845 | 5.813 | 17.793 | 9.619 |
| B | English | 1.690 | 1.460 | 3.166 | 12.713 |
| B | Hindi | 15.277 | 8.294 | 33.902 | 0.931 |
| B | Tamil | 40.423 | 35.124 | 95.554 | 0.753 |

These timings cannot isolate adapter overhead: contention changes during the run, and generated response lengths also differ. All eight later campus runs use the same 75% CUDA allocator budget, 3,220,832,256 bytes, with observed peak reserved memory below the budget. A separate six-case stress probe, including a 9,216-token input and 192 forced output tokens without between-case cache clears, also stays within budget. Allocation measurements do not establish exclusive physical GPU residency or sustained performance on another laptop.

## 7. Discussion

The benchmark and campus results answer different questions. QLoRA improves reference overlap on supplied-context benchmark QA, but campus A/B receive no supplied evidence. Their weak results cannot be interpreted as a failed test of the model's ability to read context it never received. Instead, they show that benchmark adaptation does not provide new campus facts by itself.

Retrieval enables substantially higher lexical scores in the fresh campus population, but adding LoRA to the same retrieval does not produce a consistent benefit. The Hindi result is lower with the adapter, and the Tamil advantage is small relative to the reported uncertainty. The evidence does not support choosing D as universally superior to C.

The citation failure also changes how system behavior should be evaluated. A retriever can return a useful passage, a model can generate a source-derived entity, and a downstream contract can still turn the response into an abstention. Conversely, attaching a valid citation to an exact copied phrase does not prove that the phrase answers the question. Retrieval quality, answer overlap, citation provenance, and human-verified factual support are separate properties.

The follow-up is an exploratory design extension prompted by an original test failure. Its rule and new questions are fixed before follow-up inference, and it retains the unsuccessful original result. Nevertheless, it changes both the evaluation population and corpus, so it provides no controlled estimate of the citation policy's isolated effect. A future policy ablation should use a newly frozen common population and matched raw generations, with independent human review.

## 8. Limitations and validity threats

**Model and training scope.** This is one 1.5B checkpoint, one selected adapter, one training seed, and a small training budget. The study contains neither an executed 7B comparison nor repeated-seed robustness estimates. Length filtering changes which Hindi and Tamil training records are available.

**Dataset comparability and exposure.** English and Indic test populations are not parallel. Preserved-ID and document-group controls reduce known train/validation overlap but cannot rule out semantic duplicates, translation errors, or foundation-model pretraining exposure to public benchmarks. The study is not an evaluation on entirely novel private text.

**Reference independence.** Campus facts, translations, references, and relevance labels are AI curated. Human source certification, native-speaker translation review, and response claim verification remain pending. The number of unsupported answers, hallucination reduction, and human factual accuracy are not established.

**Small, correlated campus samples.** The original campus test covers nine answerable facts and the follow-up six, with paraphrases across three languages. Nominal response counts overstate the number of independent source facts. The response bootstrap does not adjust for source-document dependence, and the future/personal negative queries are relatively easy.

**Metric dependence.** Whitespace overlap can miss semantically correct Indic answers or reward surface copying. EM/F1 includes correct abstentions on unanswerable questions. A verbatim source match certifies provenance only. None of these metrics establishes fairness or semantic factuality.

**Retrieval calibration and freshness.** The distance threshold is selected from positive validation examples without difficult-negative calibration. Review freshness refers to a captured official publication, not proof that every underlying policy is current. Adding sources can change rankings even with the same embedding and threshold.

**Performance measurement.** The Windows laptop is not an isolated performance host. Shared-memory pressure, changing competing workloads, and the disclosed working-set trim limit throughput and latency conclusions. Measured allocated/reserved CUDA memory is distinct from dedicated-memory residency.

**Reproduction scope.** Public source and lightweight evidence do not constitute a preloaded runtime backup. Exact historical campus ingestion requires original source captures retained locally; recapturing live pages may create different source versions. Full prediction logs, model weights, and the vector database are not part of the public repository.

## 9. Ethics, source stewardship, and AI assistance

The intended use is a research assistant for public campus information, not an authority for binding university decisions. The system uses a source allowlist, explicit review provenance, immutable versions, freshness checks, and abstention. Users should consult the cited official publication for consequential decisions. Private portals, credentials, grades, and student-specific records are excluded from the curated and indexed corpus.

Original source attribution and dataset licensing obligations are documented in the repository. The public source handoff does not redistribute raw university page archives or full benchmark downloads. Dataset preparation preserves source and translation provenance rather than silently treating translated training records as native evaluation data.

AI assistance is used for software development, source and translation curation, and manuscript drafting. Those activities do not create human reviewers or human ground-truth annotations. Funding, conflicts of interest, author contributions, and any applicable institutional review statements must be confirmed by the authors before submission; no approval, exemption, or review agreement is asserted here.

## 10. Conclusion and further work

This local experiment demonstrates that QLoRA adaptation of Qwen2.5-1.5B-Instruct can improve lexical QA scores within the selected English, Hindi, and Tamil benchmark populations using a small training budget. It also records a complete citation-enforcement failure in the original campus experiment and mixed adapter effects in a separately frozen fresh-source follow-up. The evidence supports feasibility and measured benchmark gains, while leaving semantic factuality, hallucination reduction, and general campus superiority unresolved.

Further work should prioritize independent source/translation and response reviews, more source facts and difficult negatives, source-clustered uncertainty estimates, repeated training seeds, a controlled policy ablation, and measurements under stable hardware conditions. A larger-model comparison would be a separate experiment requiring suitable hardware and distinct run identifiers.

## References

1. Rajpurkar, P., et al. (2016). [SQuAD: 100,000+ Questions for Machine Comprehension of Text](https://arxiv.org/abs/1606.05250). arXiv:1606.05250.
2. Hu, E. J., et al. (2021). [LoRA: Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685). arXiv:2106.09685.
3. Dettmers, T., et al. (2023). [QLoRA: Efficient Finetuning of Quantized LLMs](https://arxiv.org/abs/2305.14314). arXiv:2305.14314.
4. Lewis, P., et al. (2020). [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401). arXiv:2005.11401.
5. Qwen et al. (2024). [Qwen2.5 Technical Report](https://arxiv.org/abs/2412.15115). arXiv:2412.15115.
6. Wang, L., et al. (2024). [Multilingual E5 Text Embeddings: A Technical Report](https://arxiv.org/abs/2402.05672). arXiv:2402.05672.
7. AI4Bharat. [IndicQA dataset release](https://huggingface.co/datasets/ai4bharat/IndicQA). Experimental revision: `d7e91454f5c8a85b82e2549453521a2b7a185c44`.
8. Endait, S., et al. (2025). [IndicSQuAD: A Comprehensive Multilingual Question Answering Dataset for Indic Languages](https://aclanthology.org/2025.paclic-1.70/). PACLIC. [Author dataset release](https://huggingface.co/datasets/l3cube-pune/indic-squad).

## Appendix A. Experimental provenance and supporting evidence

The [final handover report](docs/FINAL_RESEARCH_REPORT.md) provides the operational record. The public [read-only model audit](handoff/final-model-validation.json) contains the source/language metric dictionaries, intervals, abstentions, citation origins, and run metadata used in this draft. The [frozen follow-up protocol](handoff/citation-policy-followup/sealed_protocol.json) records the post-primary amendment before follow-up inference. The [metric definitions](docs/METRIC_DEFINITIONS.md) specify denominators and pending-review behavior. This manuscript introduces no new inference run or revised score.

**Table A1. Immutable populations and indexes.**

| Artifact | Version |
|---|---|
| Prepared benchmark | `acbff74f81c1a1d1` |
| Original campus corpus / test / index | `652d19bfd9f0b4cc` / `a75705ed443380de` / `d7d31923b9ecac7f` |
| Follow-up campus corpus / test / index | `b07405a784a7045c` / `29ed6c44573105ff` / `6e044fab88609b53` |
| Training-source IndicSQuAD revision | `f5973900b6c0e3caf6a1698b49a3309bad3ae849` |
| Selected E5 revision | `614241f622f53c4eeff9890bdc4f31cfecc418b3` |

**Table A2. Actual evaluation run identifiers.**

| Track | Arm | Run UUID | Successful predictions |
|---|---|---|---:|
| Benchmark | A | `013018a0-f42d-418d-8de8-922d7ca8e728` | 13,921 |
| Benchmark | B | `fc7c6a02-bb45-4aed-8ecb-35b2611ddb07` | 13,921 |
| Original campus | A | `7397049e-5b46-4f77-9362-6a4d82a50252` | 63 |
| Original campus | B | `82540012-8fa2-4827-8b33-8f199248da88` | 63 |
| Original campus | C | `168585c5-3777-4bac-aa51-8aab3151a3c5` | 63 |
| Original campus | D | `d9f859af-917e-4cf9-b6ab-574b8933ca99` | 63 |
| Follow-up campus | A | `7f661f59-cb10-4fc7-a2da-69e4a3a213c5` | 45 |
| Follow-up campus | B | `8448fdf6-04aa-40d8-ba1f-30695f2977e7` | 45 |
| Follow-up campus | C | `5b593ab6-cca9-4cb2-b727-58ca6c12834f` | 45 |
| Follow-up campus | D | `54ab8518-0d9a-4a4d-9fbc-8270e3ff2ad3` | 45 |

Valid training UUID: `7e800833-02fb-4f7f-88e0-883f7fd4dfa3`. Adapter directory: `models/qwen2.5-1.5b/lora_adapter/7e800833-02fb-4f7f-88e0-883f7fd4dfa3/` in the original working project. Adapter tree digest: `3e2e65278413ed82c219d9b0c60c88cea0c1bfc22243f6af9772d13df1b2798d`. The weights are retained locally, not distributed in the public repository. The follow-up protocol file SHA-256 is `57829556ce330d64253b3d3dcabdad2820234fbc3585d9c84af945b582a4cecd`.

Implementation verification recorded 103 passing Python tests and three passing Edge browser tests, including a real cited-chat request through the local GPU. These checks validate software behavior rather than certify research conclusions. Historical validation records are available in [`handoff/validation-local-profile.json`](handoff/validation-local-profile.json); installation and new-run commands are in [README.md](README.md) and [the reproduction guide](docs/REPRODUCIBILITY.md). Archived run artifacts and their original timestamps remain authoritative for the reported experiments.
