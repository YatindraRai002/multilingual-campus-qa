PROJECT: Multilingual SLM Fine-Tuning and Grounded Campus FAQ System
YOUR ROLE
Act as a Senior Machine Learning Research Engineer, NLP Engineer, MLOps Engineer and Full-Stack Developer.

You are responsible for implementing a complete, reproducible research project titled:

"Multilingual SLM Fine-Tuning for Local Campus FAQs: Evaluating LoRA-Based Adaptation and Retrieval-Augmented Generation Across English, Hindi and Tamil."

Do not merely create a chatbot or a collection of disconnected scripts.

Build an end-to-end research pipeline that:

Downloads and prepares an established multilingual QA benchmark.

Evaluates an original 7B-class Qwen model.

Fine-tunes Qwen using LoRA.

Evaluates the fine-tuned model against the original model.

Builds a college-specific verified FAQ knowledge base.

Stores college information in ChromaDB.

Integrates multilingual RAG.

Compares different model configurations.

Calculates all research metrics in the backend.

Displays actual experimental results on the frontend.

Make sensible engineering decisions independently. Inspect the existing repository before changing anything. Preserve working functionality and avoid unnecessary rewrites.

PHASE 1 — REPOSITORY AND HARDWARE AUDIT
Before implementation:

Inspect the entire existing repository.

Identify the current frontend and backend frameworks.

Identify existing API routes, database and UI components.

Inspect Python and Node versions.

Check CPU, RAM, GPU, VRAM and available disk space.

Verify CUDA and PyTorch compatibility.

Check whether the environment can load and fine-tune a 7B-class model.

Create:

docs/ENVIRONMENT_REPORT.md

The report must include:

Existing architecture.

Hardware information.

GPU compatibility.

Dependency status.

Estimated model storage.

Estimated training memory.

Recommended training configuration.

Use the existing hardware efficiently.

Prefer QLoRA with 4-bit quantization when necessary.

If the available hardware cannot support training, prepare a compatible Colab/cloud execution configuration. Do not falsely report that training succeeded.

Do not begin an expensive training run before validating the environment.

PHASE 2 — BENCHMARK DATASET SELECTION AND ACQUISITION
This is the first major research milestone.

We must establish the benchmark before developing the college FAQ knowledge base.

Primary benchmark: Indic-QA
Use the published Indic-QA benchmark:

Hugging Face dataset:
ai4bharat/IndicQA

Research paper:
"INDIC QA BENCHMARK: A Multilingual Benchmark to Evaluate Question Answering Capability of LLMs for Indic Languages."

The benchmark covers 11 Indian languages and includes context-grounded extractive and abstractive question-answering tasks.

Target languages:

English

Hindi

Tamil

Important language handling
Indic-QA covers Hindi and Tamil among its Indic languages. Do not assume that it contains a directly comparable English split.

Investigate its dataset configurations, splits, original source datasets and record identifiers.

For English:

Use original English source datasets when a reliable mapping to the Indic-QA examples exists.

Otherwise select a suitable established English QA benchmark, such as SQuAD, and document the differences.

Do not falsely claim that unmatched English records are parallel translations of Hindi and Tamil records.

Dataset inspection
Before downloading everything:

Inspect the official dataset card.

Read the benchmark paper.

Check licensing and research usage conditions.

Inspect available language configurations.

Inspect train, validation and test splits.

Inspect record schemas.

Identify source datasets.

Identify native versus translated records.

Inspect answer and context quality.

Estimate storage requirements.

Create:

docs/BENCHMARK_SELECTION.md

docs/BENCHMARK_DATASET_REPORT.md

Include a reasoned explanation for selecting the benchmark and document all limitations.

Do not replace Indic-QA with an arbitrary web FAQ dataset.

If its official repository has changed, investigate the original paper and maintained official dataset location before selecting an alternative.

Benchmark dataset structure
Normalize the records into a common schema:

benchmark_id

source_dataset

language

context

question

reference_answer

answer_type

original_source_id

translation_status

split

license

provenance

Preserve original benchmark records separately.

Never overwrite the original downloaded dataset.

PHASE 3 — BENCHMARK PREPROCESSING
Create a reproducible preprocessing pipeline.

Required operations:

Normalize text.

Preserve Unicode.

Validate Hindi Devanagari.

Validate Tamil script.

Detect empty records.

Detect duplicates.

Identify malformed answers.

Validate context-question-answer relationships.

Normalize language identifiers.

Preserve original source identifiers.

Generate dataset statistics.

Keep the original train, validation and test splits wherever available.

If the benchmark requires a new split, split by source document or canonical question group to avoid leakage.

Critical restriction
The test split must remain untouched.

Do not use test records for:

Fine-tuning.

Hyperparameter tuning.

Prompt optimization.

Checkpoint selection.

Training data augmentation.

Use the training split for LoRA training and validation split for model selection.

Save the processed dataset under:

data/benchmark/

Suggested structure:

data/benchmark/raw/

data/benchmark/processed/

data/benchmark/train/

data/benchmark/validation/

data/benchmark/test/

Generate a manifest containing actual record counts, language distributions, split distributions, duplicate statistics and dataset checksums.

Create:

docs/DATASET_PREPROCESSING_REPORT.md

Do not invent dataset counts.

PHASE 4 — BASE MODEL SELECTION AND LOADING
Use:

Qwen/Qwen2.5-7B-Instruct

This is the selected 7B-class model.

Official model repository:

https://huggingface.co/Qwen/Qwen2.5-7B-Instruct

Verify:

Model license.

Checkpoint availability.

Model revision.

Tokenizer.

Hindi and Tamil script handling.

Memory requirements.

Inference compatibility.

PEFT compatibility.

Do not silently substitute a smaller model.

If the selected model cannot be accessed or trained, stop and report the problem.

Use the model's official chat template for training and inference.

Create:

config/model_config.yaml

PHASE 5 — BASELINE EVALUATION
Before fine-tuning, evaluate the original Qwen2.5-7B-Instruct model.

Use the untouched benchmark evaluation split.

Run evaluation separately for:

English.

Hindi.

Tamil.

Where the benchmark does not offer a comparable English split, explicitly document the separate English evaluation dataset.

Store actual predictions.

For every evaluated record, persist:

Question ID.

Language.

Context.

Question.

Reference answer.

Generated answer.

Model configuration.

Prompt version.

Generation settings.

Input tokens.

Output tokens.

Inference time.

Evaluation status.

Save under:

results/baseline/

This is the baseline against which all later experiments will be compared.

PHASE 6 — LORA FINE-TUNING
Fine-tune the selected Qwen2.5-7B-Instruct model using the benchmark training dataset.

Use:

PyTorch.

Transformers.

PEFT.

TRL where compatible.

bitsandbytes where appropriate.

Accelerate where required.

Implement LoRA/QLoRA.

Configure:

LoRA rank.

LoRA alpha.

Dropout.

Target modules based on the selected architecture.

Learning rate.

Batch size.

Gradient accumulation.

Epochs.

Warmup.

Weight decay.

Precision.

Gradient checkpointing.

Random seed.

Choose hyperparameters based on actual hardware and validation performance.

Do not blindly use generic settings.

Training objective
Teach the model to perform context-grounded multilingual question answering.

The model should:

Understand questions in the target language.

Use the supplied context.

Produce answers in the requested language.

Preserve factual information.

Avoid unsupported claims.

Abstain when context does not contain sufficient information.

Use language-balanced sampling where justified.

Report the actual number of training examples used per language.

Do not artificially claim balanced training if the source dataset is imbalanced.

Training monitoring
Track:

Training loss.

Validation loss.

Epochs.

Learning rate.

Training duration.

GPU memory usage where available.

Checkpoint information.

Save the best validation checkpoint.

Store the LoRA adapter separately from the base model.

Directory:

models/qwen2.5-7b/lora_adapter/

Save training logs under:

results/training/

Create:

docs/LORA_TRAINING_REPORT.md

The test split must not influence checkpoint selection.

PHASE 7 — FINE-TUNED MODEL EVALUATION
Load the trained LoRA adapter with the original base model.

Run evaluation using exactly the same benchmark test records used in baseline evaluation.

Keep:

Same test questions.

Same reference answers.

Same generation settings.

Same evaluation definitions.

Compare:

Original Qwen versus LoRA fine-tuned Qwen.

Report results separately for English, Hindi and Tamil.

Where English uses a separate benchmark, make the distinction visible.

Do not mix different benchmark populations into one supposedly directly comparable score.

Save:

results/lora/

Create:

docs/LORA_EVALUATION_REPORT.md

PHASE 8 — COLLEGE-SPECIFIC GROUND-TRUTH FAQ COLLECTION
Only after establishing the benchmark and completing the benchmark fine-tuning workflow, begin constructing the college knowledge base.

The initial target is:

SRM Institute of Science and Technology — Kattankulathur campus.

Use publicly available and verified official university information.

Sources may include:

Official university website.

Official admission pages.

Academic regulations.

Examination policies.

Hostel information.

Fee schedules.

Scholarship policies.

Library services.

Transportation.

Campus facilities.

Student services.

Create a configurable source registry.

Do not scrape private student portals or personal student information.

Do not invent college policies.

FAQ data structure
Every FAQ should contain:

faq_id

canonical_question

language

answer

category

source_url

source_title

source_document_id

verification_status

verified_at

document_version

effective_date, when applicable

Target languages:

English.

Hindi.

Tamil.

Each language version must preserve the same policy meaning.

Machine translations must be flagged as unverified until reviewed.

Ground-truth policy
The college FAQ dataset is a separate knowledge corpus.

Do not automatically merge it into the benchmark training data.

Do not fine-tune the Qwen model on college FAQs in this experiment.

The purpose is to investigate whether the benchmark-adapted model can use verified college information through retrieval.

Store collected records under:

data/college_faq/

Create:

docs/COLLEGE_FAQ_DATASET_REPORT.md

PHASE 9 — CHROMADB KNOWLEDGE BASE
Build a multilingual retrieval system using ChromaDB.

Use an appropriate multilingual sentence-transformer embedding model.

Evaluate candidate embedding models for English, Hindi and Tamil before choosing one.

Do not assume that a model is suitable merely because it is described as multilingual.

Ingestion pipeline
Load verified college FAQs.

Normalize content.

Validate language.

Chunk longer documents where appropriate.

Generate embeddings.

Store records in ChromaDB.

Preserve metadata.

Maintain document versions.

Support updates and deletions.

Prevent duplicate ingestion.

Store:

FAQ ID.

Document ID.

Language.

Category.

Question.

Answer.

Source URL.

Verification status.

Version.

Create separate collections or a carefully validated multilingual collection according to retrieval experiments.

Implement metadata filtering.

Retrieval workflow
User question
→ Language identification
→ Query embedding
→ ChromaDB retrieval
→ Relevant document ranking
→ Context construction
→ Fine-tuned Qwen inference
→ Grounded answer
→ Source citations

If evidence is insufficient, the model must abstain.

Never invent a citation.

Save the retrieval configuration and ingestion manifest.

PHASE 10 — FOUR EXPERIMENTAL CONFIGURATIONS
Implement four independent experimental configurations.

Experiment A — Original model
Original Qwen2.5-7B-Instruct.

No LoRA.

No RAG.

Experiment B — Fine-tuned model
Qwen2.5-7B-Instruct + LoRA.

No RAG.

Experiment C — Retrieval baseline
Original Qwen2.5-7B-Instruct + ChromaDB RAG.

No LoRA.

Experiment D — Proposed final system
LoRA fine-tuned Qwen2.5-7B-Instruct + ChromaDB RAG.

Evaluate all four using the same college-specific test questions for the campus experiment.

Also evaluate A and B using the benchmark test set.

For the campus experiment, ensure that every configuration receives the same available evidence where applicable, and document the different context conditions.

Keep benchmark evaluation and campus evaluation as separate research tracks.

Do not mix their results.

PHASE 11 — BACKEND METRIC COMPUTATION
This is a critical requirement.

All research metrics must be calculated in the backend from actual model outputs and ground-truth annotations.

The AI model must not generate metric values.

The frontend must never calculate or estimate research metrics.

Implement a dedicated evaluation engine.

Suggested modules:

backend/evaluation/inference_runner.py

backend/evaluation/accuracy.py

backend/evaluation/hallucination.py

backend/evaluation/retrieval.py

backend/evaluation/latency.py

backend/evaluation/language_fairness.py

backend/evaluation/statistics.py

backend/evaluation/evaluation_runner.py

Metrics
Calculate:

Answer accuracy.

Exact match.

F1 score where appropriate.

Hallucination incidence.

Unsupported factual claim rate.

Retrieval Recall@K.

Mean Reciprocal Rank.

Language-wise accuracy.

Language performance gap.

Mean latency.

Median latency.

P95 latency.

Throughput.

Abstention accuracy.

Confidence intervals.

Formula requirements
Accuracy:

Correct answerable responses / Total answerable responses × 100.

Hallucination incidence:

Responses with at least one unsupported factual claim / Non-abstained responses × 100.

Unsupported claim rate:

Unsupported factual claims / Total evaluated factual claims × 100.

Retrieval Recall@K:

Queries with a relevant document retrieved in the top K / Total retrieval queries × 100.

Language performance gap:

Highest language accuracy − Lowest language accuracy.

Mean latency:

Sum of measured end-to-end latency / Completed requests.

P95 latency:

95th percentile of measured end-to-end latency.

Throughput:

Generated tokens / Actual generation duration.

Use monotonic timing instrumentation.

Separate model-loading time from normal inference.

Record retrieval, generation and total latency separately.

Hallucination assessment
Use evidence-based claim verification.

Create human-review annotations for factual correctness and source support.

LLM-as-a-judge may be used as an auxiliary method but must not be the only ground truth.

When human annotations are unavailable, mark the metric as pending or unscored.

Do not generate artificial scores.

Calculate confidence intervals using an appropriate statistical method such as bootstrap resampling.

Store metric definitions and denominators with every result.

PHASE 12 — DATABASE AND EXPERIMENT MANAGEMENT
Persist all experiment data.

Use the existing database architecture if suitable.

Create structured records for:

Datasets.

Dataset versions.

Model registry.

Model adapters.

Experiment runs.

Predictions.

Metric results.

Language metrics.

Retrieval results.

Human annotations.

Training logs.

Every experiment must have a unique run ID.

Record:

Dataset version.

Model revision.

Adapter revision.

Prompt version.

Generation parameters.

Hardware.

Random seed.

Evaluation split.

Start timestamp.

End timestamp.

Evaluation status.

Never overwrite historical runs.

Allow experiments to be reproduced from stored configurations.

PHASE 13 — BACKEND API
Implement APIs compatible with the existing architecture.

Suggested endpoints:

GET /api/datasets/summary

GET /api/datasets/languages

GET /api/models

GET /api/experiments

GET /api/experiments/{run_id}

GET /api/experiments/{run_id}/metrics

GET /api/experiments/{run_id}/predictions

GET /api/experiments/compare

GET /api/college-faq/summary

GET /api/languages/metrics

POST /api/evaluation/run

GET /api/evaluation/status/{run_id}

POST /api/chat

Long-running evaluation jobs must execute asynchronously.

Return job IDs and status.

Implement appropriate validation, exception handling and logging.

PHASE 14 — FRONTEND RESEARCH DASHBOARD
Build a professional research dashboard.

Include:

Project overview.

Benchmark dataset overview.

Language-wise benchmark distribution.

Dataset provenance.

Model information.

Fine-tuning progress.

Training and validation loss charts.

LoRA configuration.

Benchmark evaluation results.

College FAQ corpus statistics.

ChromaDB retrieval statistics.

Four-experiment comparison.

Language-wise accuracy.

Hallucination analysis.

Latency analysis.

Retrieval performance.

Individual question inspection.

Supporting source documents.

Evaluation history.

Exportable research reports.

STRICT FRONTEND RULE
The frontend is only a visualization layer.

It must not calculate:

Accuracy.

Hallucination rate.

Language performance gap.

Average latency.

P95 latency.

Retrieval Recall@K.

Throughput.

All numerical metrics must arrive from backend APIs backed by persisted experiment records.

If evaluation has not run, display:

"Evaluation not yet performed."

If a metric has insufficient annotations, display:

"Insufficient validated data."

Never use fabricated placeholder percentages as actual research results.

Every result should identify its experiment ID, evaluation dataset and timestamp.

PHASE 15 — RESPONSIBLE AI AND RESEARCH DOCUMENTATION
Generate the following reports:

docs/PROJECT_ARCHITECTURE.md

docs/BENCHMARK_SELECTION.md

docs/BENCHMARK_DATASET_REPORT.md

docs/DATASET_PREPROCESSING_REPORT.md

docs/LORA_TRAINING_REPORT.md

docs/LORA_EVALUATION_REPORT.md

docs/COLLEGE_FAQ_DATASET_REPORT.md

docs/RAG_IMPLEMENTATION_REPORT.md

docs/EVALUATION_REPORT.md

docs/RESPONSIBLE_AI_REPORT.md

docs/REPRODUCIBILITY.md

Address:

Language fairness.

Tamil and Hindi representation.

Translation quality.

Benchmark limitations.

Dataset licensing.

Data provenance.

Hallucination.

Correct abstention.

Source freshness.

Privacy.

Evaluation bias.

Model limitations.

Never claim that a model is unbiased or hallucination-free.

PHASE 16 — TESTING AND FINAL VALIDATION
Test:

Benchmark acquisition.

Dataset schema.

Language identification.

Data leakage prevention.

Training pipeline.

LoRA checkpoint loading.

Model inference.

Multilingual retrieval.

ChromaDB persistence.

Source citations.

Metric formulas.

Timing instrumentation.

API responses.

Dashboard integration.

Historical experiment persistence.

Create synthetic unit-test examples to validate formulas, but never use test fixtures as research results.

Verify that:

Original model results are actually recorded.

Fine-tuned model results are actually recorded.

The same benchmark test questions are used for baseline and LoRA comparison.

College FAQ retrieval uses verified records.

All four campus experiments can execute.

Backend metrics are calculated from actual records.

Frontend displays only persisted results.

Missing evaluation results are not fabricated.

The entire pipeline can be reproduced.

IMPLEMENTATION ORDER
Execute the project in this order:

Repository and hardware audit.

Indic-QA benchmark inspection and acquisition.

Dataset validation and preprocessing.

Qwen2.5-7B-Instruct baseline evaluation.

LoRA/QLoRA fine-tuning.

Fine-tuned model evaluation.

College-specific official FAQ collection.

ChromaDB ingestion.

RAG implementation.

Four experimental configurations.

Backend metric computation.

Database persistence.

Frontend research dashboard.

Testing and documentation.

Do not skip the benchmark stage.

Do not start with college FAQ scraping.

Do not fine-tune on college FAQs in this initial experimental design.

Do not mix benchmark and college-specific evaluation results.

EXECUTION AND AUTONOMY RULES
You have permission to make reasonable implementation decisions without repeatedly asking me about minor technical details.

However:

Do not silently substitute datasets or models.

Do not invent university information.

Do not bypass dataset licensing.

Do not fabricate benchmark records.

Do not fabricate training progress.

Do not fabricate evaluation metrics.

Do not overwrite existing project functionality.

Do not claim successful training without a real checkpoint.

Do not claim successful evaluation without real predictions and calculated metrics.

After each major phase:

Run relevant tests.

Inspect outputs.

Generate a concise report.

Record errors and unresolved issues.

Continue if validation passes.

If a major blocker occurs, explain it and provide the best feasible alternative.

At completion, provide:

Final repository structure.

Selected benchmark and justification.

Actual dataset statistics.

Selected Qwen model.

Training configuration.

LoRA adapter location.

ChromaDB configuration.

Four experiment run IDs.

Actual calculated metrics.

Frontend dashboard status.

Reproduction commands.

Remaining limitations.

FINAL RESEARCH GOAL

Produce a scientifically defensible multilingual research system demonstrating whether benchmark-based LoRA fine-tuning improves Qwen2.5-7B-Instruct's multilingual QA capabilities, and whether combining that model with a verified ChromaDB-based college FAQ retrieval system improves factual accuracy, reduces unsupported answers and maintains performance across English, Hindi and Tamil.