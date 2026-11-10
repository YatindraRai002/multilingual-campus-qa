# Multilingual Qwen Fine-Tuning and Grounded Campus FAQ Research

**[Read the research-paper draft](RESEARCH_DRAFT.md)** — manuscript with abstract, related work, methods, actual results, limitations, references and experimental provenance. Author and affiliation details remain to be confirmed; human factuality review is pending.

**The website opens as a chatbot.** Type in English, Hindi or Tamil for a reply in the same language, or use one of five suggested questions about library technology, bus booking, Oori hostel rooms, the campus temple and campus maintenance. Quick answers come directly from source-reviewed FAQs; other questions use the local model when available. If it is busy or short of GPU memory, the assistant gives a localized availability message while the five FAQ topics remain usable. The research dashboard remains under **Overview**. See [the chat interface guide](docs/CHAT_INTERFACE.md).

**Active study: Qwen/Qwen2.5-1.5B-Instruct on the laptop RTX 2050.** The user explicitly approved this change so actual GPU experiments can run with 4 GiB VRAM. The original 7B model/training settings are archived in `config/profiles/`; 1.5B results must never be represented as 7B results. See [the authorized study amendments](docs/STUDY_AMENDMENTS.md).

**Completed locally:** QLoRA training, two full 13,921-question benchmark runs, and two separate four-arm campus experiments (63 and 45 questions per arm). All **10 runs / 28,274 predictions** succeeded. At the research snapshot, **103 Python tests and 3 Edge browser tests passed**, including real GPU-backed chat. The later chat-interface update passed **133 Python tests** and verified all **15 FAQ/language combinations**, with desktop, mobile and real model-chat checks recorded [separately](handoff/chat-interface-validation.json). See the [final research report and handover](docs/FINAL_RESEARCH_REPORT.md) for all run IDs, metrics, artifacts and limitations.

Benchmark F1 changed from **62.77 → 86.08 English**, **27.56 → 39.22 Hindi**, and **13.20 → 20.59 Tamil**. The original campus citation guard rejected every C/D answer; those negative results are preserved. A frozen follow-up on fresh source-disjoint questions produces cited answers, with mixed LoRA-versus-base-RAG results. Human factuality metrics remain **Pending**; these are lexical scores, not certified factual accuracy.

IndicQA remains an untouched evaluation-only source. The separately approved L3Cube IndicSQuAD training extension supplies Hindi/Tamil data. Campus acquisition follows completed benchmark A → training → B. Source checks and AI translation review are explicitly distinguished from human verification; unreviewed translations are excluded. Human factuality scores remain pending until actual human response annotations exist. See the [corpus review policy](docs/CORPUS_REVIEW_POLICY.md).

## Get the source

```powershell
git clone https://github.com/YatindraRai002/multilingual-campus-qa.git
Set-Location 'multilingual-campus-qa'
```

The public repository includes the implementation, pinned configuration, reviewed campus FAQ/test snapshots, research reports and lightweight validation records in [`handoff/`](handoff/). Model weights, adapters, raw benchmark downloads, university page archives, SQLite, Chroma and dependency caches remain local. Follow the fresh-installation and [reproduction instructions](docs/REPRODUCIBILITY.md) to provision them. Historical reports and curation manifests retain the original experiment machine's paths; the repository is a source handoff rather than a preloaded runtime.

## Open the local dashboard

In PowerShell:

```powershell
Set-Location 'D:\shameek RAI'
& '.\.venv\Scripts\python.exe' -m backend.cli serve --port 8765
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765). API documentation: [http://127.0.0.1:8765/docs](http://127.0.0.1:8765/docs). Port 8000 was already in use on this laptop, so this startup command uses 8765.

The application binds to localhost. All model execution uses your hardware or the external GPU where you run this repository. There is no hosted inference service or API key requirement.

## Fresh installation

```powershell
powershell -ExecutionPolicy Bypass -File '.\scripts\setup.ps1' -WithML
& '.\.venv\Scripts\python.exe' -m backend.cli acquire
& '.\.venv\Scripts\python.exe' -m backend.cli prepare
& '.\.venv\Scripts\python.exe' -m backend.cli resolve-model
& '.\.venv\Scripts\python.exe' -m backend.cli tokenizer-check
& '.\.venv\Scripts\python.exe' -m backend.cli audit --check-torch
& '.\.venv\Scripts\python.exe' -m pytest
```

Use `scripts/setup.ps1` without `-WithML` for the lightweight dashboard and data tools. Runtime and caches stay in the project directory on D:.

## Actual acquired benchmark

| Language | Evaluation source | Test records | Answerable | Unanswerable |
|---|---|---:|---:|---:|
| English | SQuAD v1.1 development set, reserved as test | 10,570 | 10,570 | 0 |
| Hindi | AI4Bharat IndicQA official test | 1,547 | 1,052 | 495 |
| Tamil | AI4Bharat IndicQA official test | 1,804 | 1,277 | 527 |

The final prepared version is `acbff74f81c1a1d1`. All 13,921 test records remain, including source-quality warnings. The approved training supplement preserves its complete original files and selects at most 10,000 mapped, validated records per language before document grouping.

| Language | Train records | Validation records | Training source |
|---|---:|---:|---|
| English | 78,437 | 8,961 | Original SQuAD v1.1 train |
| Hindi | 8,954 | 1,044 | Approved IndicSQuAD train subset |
| Tamil | 8,950 | 1,047 | Approved IndicSQuAD train subset |

Total: 96,341 training / 11,052 validation records. Final preprocessing removed 197 training duplicates and rejected 9 quality/overlap records. Actual training used **256 base examples per language**, plus **25 en / 17 hi / 26 ta** training-only abstention additions (836 total), and **32 validation examples per language**. Two epochs completed 106 optimizer steps in 58.90 minutes; validation selected checkpoint 80 (loss 0.346077). The complete prepared corpus was not used for training.

English is not claimed to be parallel to IndicQA. Scores are grouped by source dataset and language. The paper named in the brief describes a larger benchmark; AI4Bharat IndicQA is one component. See [benchmark selection](docs/BENCHMARK_SELECTION.md).

## Research execution

After the real model-capacity preflight passes, the durable coordinator runs the required stages in order:

```powershell
& '.\.venv\Scripts\python.exe' -m backend.cli run-study --phase all
```

Its UUID identifies `results/studies/<study-id>/state.json`, which contains actual baseline/LoRA job IDs and phase status. It waits for each GPU job, runs local QLoRA after the full baseline, and evaluates the adapter on the same complete test population. It stops at the explicit verified-campus-data dependency rather than fabricating source reviews. Resume the campus phase with `run-study --phase campus --resume <study-id>` after review and ingestion.

The completed primary study is `0f3dfb3d-298f-47c1-a020-4be01eb4bcec`; the separate citation-policy follow-up is `9ed4cb93-716a-4953-b588-606e6d999d88`. Both report `model_experiments_completed`, with independent human review still pending. There is no need to retrain to use the saved application.


Read [REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md) and [the approved training extension](docs/SUPPLEMENTAL_TRAINING_REPORT.md) for the exact order and training selection policy. The GPU preflight validates the active 1.5B local profile. Original 7B settings remain archived and cannot pass the laptop memory gate.

```powershell
& '.\.venv\Scripts\python.exe' -m backend.cli preflight
# On a suitable GPU, after acquiring and preparing the approved multilingual dataset:
& '.\.venv\Scripts\python.exe' -m backend.cli run-evaluation --track benchmark --experiment A
# Wait for the reported run ID to complete; then:
& '.\.venv\Scripts\python.exe' -m backend.cli train
& '.\.venv\Scripts\python.exe' -m backend.cli run-evaluation --track benchmark --experiment B
```

Training uses assistant-token-only supervision, official Qwen chat formatting, NF4 QLoRA, FP16, rank 8, batch 1, accumulation 16 and validation-loss checkpoint selection. Every adapter gets its own directory under `models/qwen2.5-1.5b/lora_adapter/`.

The actual selected adapter is `models/qwen2.5-1.5b/lora_adapter/7e800833-02fb-4f7f-88e0-883f7fd4dfa3/`. Current Chroma index `6e044fab88609b53` contains **57 FAQ chunks / 19 per language**, using pinned multilingual-e5-small embeddings, top K 4 and the original validation-only distance cutoff. Every FAQ retains its official URL, archived evidence and explicit AI review provenance; human certification remains pending.

The current user-authorized execution is local. The older Colab notebook remains a handoff reference; restore the archived 7B model/training profiles before treating an external run as the original 7B study. No cloud resource is started automatically.

## Four configurations

| Experiment | Weights | Campus evidence |
|---|---|---|
| A | Original Qwen | None |
| B | Qwen + LoRA | None |
| C | Original Qwen | Verified ChromaDB retrieval |
| D | Qwen + LoRA | Verified ChromaDB retrieval |

Benchmark A/B both receive the supplied benchmark context. Campus A/B are closed-book; campus C/D receive retrieved context. Comparisons validate question/reference fingerprints, dataset version, base revision, generation parameters, prompt version and actual C/D evidence.

## Repository layout

```text
backend/
  datasets.py, hardware.py, modeling.py, training.py
  college.py, retrieval.py, experiments.py, db.py, main.py, cli.py
  evaluation/              accuracy, hallucination, retrieval, fairness, timing, statistics
config/                    pinned model, dataset, training, sources and retrieval settings
data/
  benchmark/raw/           immutable original downloads (ignored in Git)
  benchmark/versions/      immutable processed splits and manifests
  college_faq/             snapshots, reviewed corpus/test/index versions (created after gates)
  chroma/                  persistent vector database
  research.sqlite3         append-only experiment and annotation history
frontend/                  responsive dashboard, buildless HTML/CSS/JavaScript
models/qwen2.5-1.5b/        independent training/checkpoint/adapter directories
results/                   environment, training, baseline, LoRA and campus run artifacts
notebooks/                 Colab execution notebook
scripts/                   installation, dashboard startup, source bundle
tests/                     isolated formula, data, API, persistence and ML contract tests
docs/                      research reports, limitations and reproducibility
```

Test fixtures are confined to temporary directories and never inserted into the production experiment store. A tiny random Qwen architecture checks PEFT save/load contracts in tests; it is not an experimental substitute for the approved model checkpoint.
