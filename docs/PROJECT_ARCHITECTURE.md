# Project architecture

The originally empty workspace now contains a local FastAPI service, SQLite experiment registry, a buildless JavaScript research dashboard, a Python QLoRA pipeline and versioned ChromaDB retrieval. PyTorch and Transformers are imported lazily for model execution. The frontend only formats backend values and plots stored observations.

## Data flow

Official benchmark downloads → immutable raw files + SHA-256 checksums → Unicode/script/span validation → document-group splits → immutable dataset version → original Qwen predictions → validation-selected LoRA training → identical LoRA evaluation population.

After benchmark A/B completion: official campus source registry → original snapshots → source-reviewed FAQs with disclosed AI/human provenance → embedding validation in all three languages → versioned Chroma collection → four campus configurations → backend metrics → SQLite → dashboard and exports. Human response factuality metrics remain pending until actual human annotations exist.

## Boundaries

`datasets.py` acquires and seals benchmark versions. `supplemental.py` streams the explicitly approved IndicSQuAD training extension, filters it by original SQuAD training-ID mapping, and preserves canonical translation groups. `training.py` has a hard hardware/data/baseline preflight, a deterministic equal-language selection budget, answer-only label masking, training-only empty-evidence abstention augmentation, monitoring and adapter storage. `experiments.py` snapshots every configuration and starts a durable subprocess worker. `evaluation/inference_runner.py` instruments inference with monotonic time. Evaluation modules derive numerical metrics without asking a language model to score itself.

`college.py` validates official hosts, original source snapshots, reviewer metadata and policy versions. `retrieval.py` compares embedding candidates using reviewed validation queries, then stores externally generated vectors in ChromaDB. Retrieval omits stale/unverified/future-effective policies and validates source labels before returning citations.

`source_attribution.py` implements the separately frozen citation extension. Historical indexes retain model-emitted citation enforcement; the follow-up can attribute only a complete verbatim FAQ answer/evidence quote from one supplied source. Raw generated text and attribution origin remain persisted. The rule reads no gold references and does not certify factual correctness. Primary and follow-up campus populations are versioned and compared separately.

## Experiment persistence

SQLite tables cover dataset versions, model revisions, adapters, runs, predictions, retrieval ranks, human annotation revisions, metric snapshots, training runs and training logs. UUID run IDs are unique; predictions cannot be appended to terminal runs. Duplicate prediction IDs per run are rejected. Annotation corrections and recomputed metric snapshots are appended, preserving historical entries. Restart recovery checks worker process identity before marking a job interrupted.

Each run records its exact question/reference fingerprint, immutable dataset version, model and adapter revisions, prompt version, generation settings, seed, hardware, context condition and timestamps. Output files are segregated by run ID. Comparisons reject mismatched populations or settings. C/D comparisons also compare actual evidence contexts.

## Local deployment

FastAPI serves both `/api/*` and the static dashboard. The default server binds to `127.0.0.1:8000`, uses one worker and validates the Host header; the audited laptop uses port 8765 because 8000 is occupied. There is no remote account, public deployment, hosted inference API or paid cloud resource. A file lock serializes GPU use across chat, evaluation and training. Chat/evaluation keep that lock through model cleanup on success and failure, so a following job cannot allocate memory before teardown finishes. Model/retriever loading time is recorded separately from normal measured inference.

The approved 1.5B local experiment uses a durable stage coordinator: full baseline, actual LoRA training, full matched evaluation, and then verified campus data and four campus configurations. Original 7B profiles remain archived. The coordinator persists real job IDs, progress and stage failures; component checks and discarded capacity probes are never reported as research results.
