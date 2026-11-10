# Reproducibility

Run commands from the repository root. Windows uses `.venv\Scripts\python.exe`; Linux/Colab uses `python` from the installed environment. Model and benchmark revisions are pinned, original files are preserved, and each normalized split has a SHA-256 checksum. All serialized dataset paths use forward slashes for portable version fingerprints. JSONL output explicitly uses the original Windows study's UTF-8/CRLF format, preserving its existing byte checksums when reproducing on another platform.

## 1. Install and audit

```powershell
powershell -ExecutionPolicy Bypass -File '.\scripts\setup.ps1' -WithML
& '.\.venv\Scripts\python.exe' -m backend.cli audit --check-torch
& '.\.venv\Scripts\python.exe' -m backend.cli resolve-model
& '.\.venv\Scripts\python.exe' -m backend.cli tokenizer-check
```

The tested setup is Python 3.11, PyTorch 2.7.1 CUDA 12.6, Transformers 4.57.3, PEFT 0.18.0, bitsandbytes 0.48.2, Accelerate 1.12.0, sentence-transformers 5.1.2 and ChromaDB 1.3.5. CUDA wheels require a compatible NVIDIA driver. The setup script does not change system drivers. `requirements-local-lock.txt` records the resolved Windows environment; use the pinned project requirements for cross-platform installation.

## 2. Acquire and preprocess

```powershell
& '.\.venv\Scripts\python.exe' -m backend.cli acquire
& '.\.venv\Scripts\python.exe' -m backend.cli prepare
```

Inspect `data/benchmark/acquisition.json`, `data/benchmark/manifest.json` and `docs/DATASET_PREPROCESSING_REPORT.md`. Immutable processed files are `data/benchmark/versions/<version>/{train,validation,test}.jsonl`. The English official dev population is held out as test. IndicQA official test stays test. Source documents sharing a context or canonical question are connected before train/validation assignment, with seed 42.

## 3. Approved Hindi/Tamil training extension

IndicQA has no training split. The user approved `l3cube-pune/indic-squad` as a distinct supplemental training source. `config/benchmark.yaml` pins its revision, a 10,000-record-per-language preprocessing budget and seed 42. `acquire` downloads the original Hindi/Tamil train files (about 615 MB), and `prepare` streams them with bounded memory. Only IDs mapping to the original English SQuAD v1.1 train split can be selected. Source/canonical question groups prevent translated copies from crossing train/validation. Published supplemental dev/test files are not used. The generated supplemental report records exclusions, mapping, actual counts and provenance. This data decision is explicitly separate from the unchanged IndicQA evaluation population.

No additional training upload is necessary for the approved configuration. The local study selects up to 256 usable base examples per language and up to 32 validation examples per language after token-length filtering, with actual augmentation counts logged separately. To register an alternative separately licensed source in a future study, the optional importer accepts JSONL with these fields:

```json
{
  "original_source_id": "the-real-source-record-id",
  "source_document_id": "the-real-canonical-source-document-id",
  "language": "hi",
  "context": "actual source context in the declared language",
  "question": "actual source question",
  "reference_answer": "actual source answer",
  "answer_type": "extractive",
  "translation_status": "native-or-explicitly-described-translation-status",
  "split": "train",
  "original_split": "train"
}
```

The example is a schema illustration, not a benchmark record. For parallel translated training records, reuse a canonical document ID across languages so their questions stay in the same split. Preserve provenance honestly; a train label alone does not prove no contamination.

```powershell
& '.\.venv\Scripts\python.exe' -m backend.cli import-training 'path\to\real-training.jsonl' --source-name 'TheActualCorpus' --license 'cc-by-4.0' --source-url 'https://the-actual-source.example/dataset'
& '.\.venv\Scripts\python.exe' -m backend.cli prepare
```

This seals a **new dataset version** without altering old versions. The full baseline must be run on that version before training. Observe actual per-language counts; do not describe an imbalanced corpus as balanced. `import-training` requires explicit supported licensing and rejects declared dev/test records. Review underlying content licensing before redistribution.

## 4. Baseline → QLoRA → matched evaluation

The active model is the user-approved Qwen2.5-1.5B-Instruct local profile. The RTX 2050 4 GiB completed actual training and all ten evaluation runs. The long original LoRA benchmark used Windows shared GPU memory and completed naturally, uninterrupted, as requested. New runs snapshot and apply `config/runtime_gpu.yaml` (75% CUDA allocator budget, 3 GiB here); old measurements retain their original memory conditions. A repeated-shape real adapter probe, including 9,216 input tokens and 192 forced output tokens without between-case cache clears, passed under this budget, as did all eight campus runs. CUDA allocator peaks do not establish exclusive dedicated-memory residency. Original 7B profiles remain archived and require a larger GPU. Do not describe the amended local experiment as a 7B run.

Unload other GPU models before starting a long experiment. The project lock coordinates its own jobs and does not reserve the GPU against unrelated services. This study observed a separate Ollama model using about 2.3 GiB concurrently. [Ollama's FAQ](https://docs.ollama.com/faq#how-do-i-keep-a-model-loaded-in-memory-or-make-it-unload-immediately) documents checking loaded models with `ollama ps` and releasing a model with `ollama stop <model-name>`. Use the correct Ollama instance for that model. An allocator budget does not create exclusive hardware access.

The durable coordinator executes the ordered benchmark workflow and records actual IDs:

```powershell
& '.\.venv\Scripts\python.exe' -m backend.cli run-study --phase all
```

Inspect `results/studies/<study-id>/state.json`, the coordinator log, or the dashboard's live study banner. Do not start a second study while a GPU job is active. The coordinator stops at the verified-campus-data prerequisite after the matched benchmark runs; collect and review that data before resuming with `run-study --phase campus --resume '<study-id>'`. Individual commands below remain available for deliberate manual execution.

```powershell
& '.\.venv\Scripts\python.exe' -m backend.cli preflight
& '.\.venv\Scripts\python.exe' -m backend.cli run-evaluation --track benchmark --experiment A
& '.\.venv\Scripts\python.exe' -m backend.cli inspect-run '<returned-run-id>'
```

The baseline runs asynchronously. Wait for `status: completed`, then:

```powershell
& '.\.venv\Scripts\python.exe' -m backend.cli train
& '.\.venv\Scripts\python.exe' -m backend.cli run-evaluation --track benchmark --experiment B
```

`preflight` reports both environment and sequencing blockers. Before baseline completion, its baseline prerequisite is expected. A pilot can be requested with `--limit-per-language 50`; it is explicitly marked and cannot unlock training. Do not select hyperparameters or checkpoints based on test scores. Configure on train/validation only, and register any changed configuration as a new run.

Completed adapters: `models/qwen2.5-1.5b/lora_adapter/<training-id>/`. The `current.json` pointer contains the actual path and revision; there is no adapter until checkpoint files exist. Training logs: `results/training/<training-id>/`. Baseline and LoRA predictions/metrics are stored under separate UUID directories. The base model's original weights remain separate from the adapter.

## 5. Collect and review official campus FAQs

After paired full benchmark A/B completion, `config/sources.yaml` was extended to 21 captured public official pages; 19 supply the current 57-record corpus. The initial homepage entry remains discovery only. Complete original HTML/text/SHA metadata is stored locally in `data/college_faq/documents/`. Recapture creates new source versions and requires fresh review: a live page cannot be assumed byte-identical to its historical snapshot.

```powershell
& '.\.venv\Scripts\python.exe' -m backend.cli collect-sources
& '.\.venv\Scripts\python.exe' -m backend.cli import-faq 'path\to\source-reviewed-faqs.jsonl'
```

Use `backend.college.FAQ.model_json_schema()` to obtain the exact schema. Original source snapshots must exist, source versions must match, and verified records require attributed reviewers, timezone-aware timestamps and a verbatim evidence quote. `source_verified` requires explicit AI source-review provenance, review notes and pending human review; AI-checked translations use `machine_translation_ai_reviewed`. `human_verified` requires an explicitly human reviewer. Unreviewed translations cannot be indexed. See `CORPUS_REVIEW_POLICY.md`. `import-faq` imports a complete corpus snapshot, so retain unchanged records when updating a policy. `delete-document <document-id>` creates a new version without it; re-ingest afterward.

Create separate source-reviewed retrieval **validation** queries and campus **test** questions. Both JSONL formats require `question`, `language`, `reviewer`, `reviewer_kind` (`human` or `ai`), `split` and `relevant_document_ids`. AI curation must retain `human_review_status: pending`; it cannot claim human certification. Campus test additionally requires a unique `question_id`, boolean `answerable` and a source-backed `reference_answer` for answerable cases. Use `split: validation` for embedding selection and `split: test` for campus evaluation. The system rejects exact question overlap and stores review provenance with the test version and runs.

```powershell
& '.\.venv\Scripts\python.exe' -m backend.cli seal-campus-test 'path\to\reviewed-campus-test.jsonl'
& '.\.venv\Scripts\python.exe' -m backend.cli evaluate-embeddings 'path\to\reviewed-retrieval-validation.jsonl' --select
& '.\.venv\Scripts\python.exe' -m backend.cli ingest
```

## 6. Run all campus configurations and annotate

The completed primary study is `0f3dfb3d-298f-47c1-a020-4be01eb4bcec`; its 39-record corpus, 63-question test and strict-citation index remain immutable. The separate completed follow-up is `9ed4cb93-716a-4953-b588-606e6d999d88`: 57 FAQs, 45 new source-disjoint questions and the frozen `model-or-verbatim-v2` rule. Original curation is `data/college_faq/curation_versions/068baf91-6d5a-48be-bd23-0cbc54f63bd2/`; follow-up curation is `data/college_faq/curation_versions/406c2868-079d-4927-8d2b-4b53326eb3bf/`. Both retain the original 24 validation questions. The complete version/run table is in `FINAL_RESEARCH_REPORT.md`.

Current corpus/test/index pointers select `b07405a784a7045c` / `29ed6c44573105ff` / `6e044fab88609b53`. Their JSONL, manifests, pinned embedding revision and retrieval configuration are preserved. `scripts/build_campus_pilot.py` records how the original corpus was extended using `curation/followup_facts.json`, preserving old records. Historical source snapshots are required to validate/reimport those original versions. Curation manifests retain original absolute paths as historical provenance; on another machine, use the corresponding relative version directories when supplying files to the CLI. Do not silently rewrite a sealed manifest to pretend new pages are the old versions.

The following commands create new run IDs on the selected current population. They do not overwrite the completed runs or exactly recreate their desktop resource conditions. To reproduce a historical arm, first restore its recorded dataset/corpus/index, adapter, configuration and citation policy in a separate checkout; confirm comparison fingerprints before interpreting a new result.

```powershell
& '.\.venv\Scripts\python.exe' -m backend.cli run-evaluation --track campus --experiment A
# Wait for each run to finish before starting the next GPU job.
& '.\.venv\Scripts\python.exe' -m backend.cli run-evaluation --track campus --experiment B
& '.\.venv\Scripts\python.exe' -m backend.cli run-evaluation --track campus --experiment C
& '.\.venv\Scripts\python.exe' -m backend.cli run-evaluation --track campus --experiment D
```

Use the dashboard's Human review page to record factual correctness and every factual claim's support. Inspect the displayed document IDs, supplied context and official reference sources before saving. Human judges can use the sealed official reference evidence in every campus arm, including closed-book A/B; the model's evidence condition remains recorded separately. Supported claims must reference those actual document IDs. Answerable abstentions cannot be marked correct. Missing annotations leave human metrics pending. All calculations occur in the backend and new metric snapshots preserve prior results.

## 7. Inspect, compare and export

```powershell
& '.\.venv\Scripts\python.exe' -m backend.cli serve --port 8765
& '.\.venv\Scripts\python.exe' -m pytest
npm ci --ignore-scripts
npm run test:browser
```

Browser tests use the existing Microsoft Edge installation and the running localhost service. On Linux use an installed Playwright browser/channel and adjust the test configuration deliberately. No browser download is necessary on this audited Windows machine.

Port 8000 was already occupied on the audited laptop. Start this application with `--port 8765` and use `http://127.0.0.1:8765`. Browser tests default to this same port. Set `CAMPUSQA_BASE_URL` to override the address when using another port.

The dashboard compares selected runs through `/api/experiments/compare?run_ids=<id>,<id>`. Export JSON, CSV or Markdown through `/api/experiments/<run-id>/export?format=json`. Every result identifies dataset version, experiment ID and timestamp. The exact stored configuration is available from `inspect-run` and each run's `configuration.json`. To repeat a run, restore those pinned settings and the referenced immutable dataset/adapter/index versions, then create a new run; never overwrite the original.

To recompute backend metrics from saved predictions after a documented definition update, run `python -m backend.cli recompute-metrics '<run-id>'`. This performs no model inference, appends a SQLite metric revision and writes an immutable JSON snapshot under `results/reports/<run-id>/`. Compare runs using the same metric-definition version. Batched timing confidence intervals resample entire generation batches.

## Archived external-GPU handoff

The active execution is local. `scripts/bundle.ps1` creates `results/campusqa-source.zip` containing source/config/docs/notebook, reviewed campus curation and versioned FAQ/test JSONL, the expected benchmark manifest, pinned acquisition provenance and training-source preparation report. Benchmark records are not embedded: reacquire the pinned original English, IndicQA and approved IndicSQuAD files with `acquire`, then `prepare`, and compare checksums. The archive excludes runtime, dependency caches, credentials, base/adapter weights, benchmark records, SQLite, Chroma, full prediction logs and raw university HTML. Lightweight audit/protocol artifacts are included under `handoff/`; original project-relative references inside these historical files still describe the working repository. It is a source handoff, not a complete runtime backup. Preserve the original local snapshot directories and model/data artifacts separately when reproducing historical campus versions; fresh acquisition can produce different source hashes.

`notebooks/colab_training.ipynb` remains an external-GPU reference. For the original 7B design, first restore both archived 7B profiles and audit the remote GPU; those runs must use separate IDs and must not be mixed with the local 1.5B experiment. The notebook does not claim access to your laptop GPU or automatically buy compute.
