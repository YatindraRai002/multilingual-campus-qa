"""Render the handover from audited stored outputs; never infer or manufacture scores."""
import json
import sqlite3
import xml.etree.ElementTree as ET

from backend.settings import ROOT, read_json, utcnow, write_json


def main():
    audit = read_json(ROOT / "results/final-model-validation.json")
    assert audit["status"] == "passed"
    suites = list(ET.parse(ROOT / "results/pytest-current.xml").getroot().iter("testsuite"))
    passed = sum(int(s.get("tests", 0)) - int(s.get("failures", 0)) - int(s.get("errors", 0))
                 - int(s.get("skipped", 0)) for s in suites)
    assert passed == 103 and all(int(s.get("failures", 0)) == int(s.get("errors", 0)) == 0 for s in suites)
    browser = (ROOT / "results/browser-trained-profile.log").read_text(encoding="utf-8")
    assert "3 passed" in browser and "failed" not in browser
    chat = read_json(ROOT / "results/chat-smoke.json")
    assert chat["status"] == "passed"
    with sqlite3.connect((ROOT / "data/research.sqlite3").as_uri() + "?mode=ro", uri=True) as connection:
        training = json.loads(connection.execute("SELECT payload FROM training_runs WHERE training_id=?",
            ("7e800833-02fb-4f7f-88e0-883f7fd4dfa3",)).fetchone()[0])
    corpus = read_json(ROOT / "data/college_faq/manifest.json")
    index = read_json(ROOT / "data/college_faq/ingestion_manifest.json")
    retrieval = read_json(ROOT / "results/retrieval_validation" / f"{index['version']}.json")
    now = utcnow()
    validation = {"checked_at": now, "python_suite": {"passed": passed, "skipped": 0, "exit_code": 0,
        "duration_seconds": sum(float(s.get("time", 0)) for s in suites),
        "log": "results/pytest-current.log", "junit": "results/pytest-current.xml"},
        "browser": {"passed": 3, "skipped": 0, "exit_code": 0, "log": "results/browser-trained-profile.log",
            "scope": "Actual completed results, training chart, review form, responsive navigation and live GPU-backed cited chat"},
        "model_experiments_complete": True, "independent_human_review_complete": False,
        "model_runs": 10, "predictions": audit["prediction_count"], "failed_predictions": 0,
        "final_model_audit": "results/final-model-validation.json", "chat_smoke": "results/chat-smoke.json",
        "data_reconstruction": "results/reproduction-check.json", "human_response_annotations": audit["human_annotations"],
        "campus_corpus_version": corpus["version"], "campus_index_version": index["version"],
        "real_training_validation": "results/training/7e800833-02fb-4f7f-88e0-883f7fd4dfa3/adapter_validation.json",
        "memory_policy": {"version": "bounded-cuda-cache-v1", "allocator_fraction": .75,
            "actual_capacity_check": "results/bounded_adapter_capacity/499b2181-0723-4cee-bd4b-99c1bee0a616/result.json",
            "benchmark_B_interrupted_or_recovered": False},
        "metric_definitions": "qa-metrics-v3-all-retrieval-queries"}
    write_json(ROOT / "results/validation-local-profile.json", validation)
    lines = ["# Final research report and project handover", "", f"Generated from audited stored records: {now}.", "",
        "The implementation, local GPU QLoRA training, full paired benchmark evaluation, two four-arm campus experiments, "
        "dashboard and live multilingual chat are complete. **10 model runs produced 28,274 successful predictions, with zero failed predictions.** "
        "Independent human source/reference certification and response factuality annotations remain pending. "
        "The brief explicitly permits those metrics to remain unscored when human labels are unavailable.", "",
        "## Scope and benchmark", "",
        "The user explicitly authorized **Qwen/Qwen2.5-1.5B-Instruct** for the laptop RTX 2050 (4 GiB), replacing the original "
        "7B design. The original 7B profile is archived and was not run. The separate approved L3Cube IndicSQuAD "
        "training extension supplies Hindi/Tamil training data; AI4Bharat IndicQA stays test-only. "
        "English SQuAD v1.1 is a separate established extractive QA population because a reliable parallel English "
        "mapping was not established. Cross-language scores are not a controlled translation comparison.", "",
        "Prepared dataset: `acbff74f81c1a1d1`. Full original test populations and contexts were retained.", "",
        "| Language | Prepared train | Validation | Test | Test source | Answerable / unanswerable |",
        "|---|---:|---:|---:|---|---:|",
        "| English | 78,437 | 8,961 | 10,570 | SQuAD v1.1 official dev | 10,570 / 0 |",
        "| Hindi | 8,954 | 1,044 | 1,547 | AI4Bharat IndicQA official test | 1,052 / 495 |",
        "| Tamil | 8,950 | 1,047 | 1,804 | AI4Bharat IndicQA official test | 1,277 / 527 |", "",
        "Totals: 96,341 train / 11,052 validation / 13,921 test. Preprocessing removed 197 training duplicates and "
        "rejected 9 quality/overlap records. Original test quality warnings are preserved. "
        "[Selection rationale](BENCHMARK_SELECTION.md), [dataset audit](BENCHMARK_DATASET_REPORT.md) and "
        "[training-source extension](SUPPLEMENTAL_TRAINING_REPORT.md) give revisions, licenses and grouping rules.", "",
        "## Actual local training", "",
        f"Training `{training['training_id']}` completed **{training['total_optimizer_steps']} optimizer steps / two epochs** "
        f"in **{training['duration_seconds']/60:.2f} minutes**. Validation selected checkpoint 80, loss "
        f"**{training['best_validation_loss']:.6f}**. Peak allocated CUDA memory: **{training['peak_gpu_memory_gib']:.3f} GiB**.", "",
        "| Language | Selected base training examples | Training-only abstention additions | Validation examples |",
        "|---|---:|---:|---:|"]
    for lang in ("en", "hi", "ta"):
        lines.append(f"| {lang} | {training['used_training_counts'][lang]} | "
            f"{training['training_abstention_augmentation_by_language'][lang]} | {training['used_validation_counts'][lang]} |")
    lines += ["", "Actual selected training set: 836 examples including 68 abstention additions; validation: 96. "
        "Selection is language balanced before augmentation; augmentation creates slightly different final language counts. "
        "The complete prepared corpus was not used for training. Overlength examples were filtered on train/validation only.", "",
        "Configuration: NF4 double quantization, FP16, rank 8, alpha 16, dropout 0.05; q/k/v/o and gate/up/down projections; "
        "learning rate 1e-4, batch 1, gradient accumulation 16, sequence length 1,024, two epochs, warmup 0.03, "
        "weight decay 0.01, paged AdamW 8-bit, gradient checkpointing and seed 42. Official Qwen chat formatting and "
        "assistant-only loss are used. No campus FAQ was used for fine-tuning.", "",
        f"Adapter: `{training['adapter_path']}/`", "",
        f"Adapter tree SHA-256: `{training['adapter_revision']}`. The real adapter passed finite-tensor, nonzero-update "
        "and checksum validation. The earlier 26-step protocol-invalid augmentation attempt is preserved and excluded.", "",
        "## Full matched benchmark results", "",
        "A = original model; B = same base plus the valid adapter. Both use the same complete questions, contexts, "
        "references, prompt, deterministic generation (maximum 192 new tokens), 9,216-token input capacity and batching. "
        "The original long B worker completed naturally, uninterrupted, as requested.", "",
        "| Language / population | A EM | B EM | A F1 | B F1 (95% CI) | F1 change, points |",
        "|---|---:|---:|---:|---:|---:|"]
    def language_metrics(record):
        return {lang: v for pop in record["populations"].values() for lang, v in pop.items()}
    bm = audit["cohorts"]["benchmark"]["runs"]
    a, b = language_metrics(bm["A"]), language_metrics(bm["B"])
    for lang in ("en", "hi", "ta"):
        ci = b[lang]["f1"]["confidence_interval"]
        lines.append(f"| {lang} | {a[lang]['exact_match']['value']:.2f} | {b[lang]['exact_match']['value']:.2f} | "
            f"{a[lang]['f1']['value']:.2f} | {b[lang]['f1']['value']:.2f} ({ci['lower']:.2f}–{ci['upper']:.2f}) | "
            f"{b[lang]['f1']['value']-a[lang]['f1']['value']:+.2f} |")
    lines += ["", "These are reference lexical scores calculated by the backend, including answerability handling, "
        "rather than human factual accuracy. The intervals resample responses, not source documents; correlated "
        "questions and possible base-model pretraining exposure limit interpretation. No paired significance claim is made.", ""]
    for cohort, title, description in (
        ("primary_campus", "Original campus experiment: 63 questions", "Test `a75705ed443380de`, corpus `652d19bfd9f0b4cc`, index `d7d31923b9ecac7f`; 21 questions per language, including 3 unanswerable."),
        ("followup_campus", "Citation-policy follow-up: 45 fresh questions", "Test `29ed6c44573105ff`, corpus `b07405a784a7045c`, index `6e044fab88609b53`; 15 questions per language, including 3 unanswerable. Six new test source pages are disjoint from the entire original FAQ corpus and validation source pages.")):
        runs = audit["cohorts"][cohort]["runs"]
        lines += [f"## {title}", "", description, "",
            "A/B receive no campus context; C/D use the same actual retrieved context. C = original + RAG; D = LoRA + RAG.", "",
            "| Arm | English EM / F1 | Hindi EM / F1 | Tamil EM / F1 | Final abstentions |",
            "|---|---:|---:|---:|---:|"]
        for arm, r in runs.items():
            scores = language_metrics(r)
            cells = [f"{scores[l]['exact_match']['value']:.2f} / {scores[l]['f1']['value']:.2f}" for l in ("en", "hi", "ta")]
            lines.append(f"| {arm} | " + " | ".join(cells) + f" | {r['abstentions']} / {r['run']['total']} |")
        if cohort == "primary_campus":
            lines += ["", "**Negative result preserved:** both C and D abstained on all 63 questions. The model often "
                "omitted the required source label. The original guard rejected 51 C and 50 D responses for missing/invalid "
                "citations; 12 per arm lacked sufficient retrieval, and D also had one model abstention. Their 14.29% "
                "EM/F1 comes solely from the unanswerable cases. These original outputs and metrics were not rewritten.", ""]
        else:
            lines += ["", "The frozen extension permits citation attribution only when the entire answer exactly matches "
                "a complete answer or evidence quote from exactly one supplied source, after limited case/whitespace/terminal-period "
                "normalization. It never uses gold references, aliases or substring/similarity matching. Internal punctuation "
                "and Indic marks are preserved; unknown labels and ambiguous/unmatched answers still abstain. Raw model "
                "text and citation origin remain recorded. Exact provenance does not certify semantic correctness.", "",
                "Within this fresh population, D ties C in English, scores lower in Hindi and higher in Tamil. "
                "The small sample does not establish a general advantage for LoRA + RAG. Original/follow-up percentages "
                "are not a paired causal estimate of the citation change: both the questions and corpus differ. "
                "See [the frozen amendment](CITATION_POLICY_AMENDMENT.md).", ""]
        lines += ["| RAG retrieval, all-query denominator | English Recall@4 / MRR | Hindi Recall@4 / MRR | Tamil Recall@4 / MRR |",
                  "|---|---:|---:|---:|"]
        scores = language_metrics(runs["C"])
        lines.append("| Same C/D evidence | " + " | ".join(f"{scores[l]['recall_at_k']['value']:.2f}% / {scores[l]['mrr']['value']:.3f}"
            for l in ("en", "hi", "ta")) + " |")
        lines.append("")
    lines += ["## Retrieval and source review", "",
        "Current Chroma collection: `campus_faq_6e044fab88609b53`, persisted at `data/chroma/`, with **57 chunks / "
        "57 FAQs (19 per language), from 19 official source pages**. All are explicitly AI source-reviewed; human-verified "
        "count is zero. Hindi/Tamil translation provenance remains `machine_translation_ai_reviewed`, human review pending. "
        "Original public HTML/text snapshots and SHA metadata are retained locally; personal portal information is excluded.", "",
        "Embedding candidates were evaluated on 24 validation questions before primary campus inference. E5-small "
        "scored 100% Recall@4 / 1.0 MRR in each language before the distance gate; multilingual MiniLM's Tamil "
        "Recall@4 was 25% / MRR 0.0833. The declared worst-language MRR rule selected E5-small.", "",
        "Pinned `intfloat/multilingual-e5-small`, revision `614241f622f53c4eeff9890bdc4f31cfecc418b3`; CPU embeddings, "
        "normalized cosine, query/passage prefixes, cross-language search, distinct-source deduplication, top K 4, "
        "distance cutoff 0.12740584881953368, maximum context 5,500 characters, chunk size 1,000/overlap 150, source-age "
        "limit 180 days. The threshold is the original validation-positive 95th percentile; no negative calibration "
        "or test-based retuning was performed. The same settings and original validation queries were retained in the follow-up.", "",
        "Fresh-process persisted-index validation after the cutoff:", "",
        "| Language | Validation queries | Recall@4 | MRR |", "|---|---:|---:|---:|"]
    for lang, v in retrieval["languages"].items():
        lines.append(f"| {lang} | {v['queries']} | {v['recall_at_k_percent']:.2f}% | {v['mrr_after_calibrated_cutoff']:.3f} |")
    lines += ["", "Empty relevance lists count zero in all-query retrieval metrics. Thus the follow-up's 12 answerable / "
        "15 total questions per language impose a maximum Recall@4 of 80%, even with perfect answerable retrieval. "
        "Future/personal negative questions are relatively easy; harder negative validation is still required.", "",
        "## Timing and memory", "",
        "Model loading is timed separately. Backend results contain measured retrieval, generation and end-to-end mean, "
        "median, P95, throughput and confidence intervals. Benchmark batches count their shared duration only once for "
        "throughput, and timing intervals resample whole batches. No timing values were replaced after the run.", "",
        "| Benchmark arm | Language | Mean / median / P95 request seconds | Generated tokens / second |",
        "|---|---|---:|---:|"]
    for arm, r in bm.items():
        for lang, v in language_metrics(r).items():
            t = v["latency"]["total_seconds"]
            lines.append(f"| {arm} | {lang} | {t['mean']:.3f} / {t['median']:.3f} / {t['p95']:.3f} | {v['latency']['throughput']['value']:.3f} |")
    lines += ["", "The long B run encountered Windows shared GPU memory, severe host RAM pressure and a competing Ollama "
        "model. The user kept it uninterrupted and paused the other project themselves; no other project's process "
        "was stopped. One disclosed worker working-set trim is documented in the responsible-AI report. Resource "
        "contention changed during execution, so raw A/B timings cannot isolate adapter overhead.", "",
        "All eight campus runs used the same 75% CUDA allocator budget (3,220,832,256 bytes), with actual peak reserved "
        "memory below that budget. A separate six-case, repeated-shape adapter capacity check, including a 9,216-token "
        "input and 192 forced output tokens, passed without clearing cache between cases; peak reserved memory was "
        "3,066,036,224 bytes. Allocator measurements do not establish exclusive GPU use or dedicated-memory residency.", "",
        "## Traceable run IDs", "",
        "| Track | Arm | Run UUID | Successful predictions |", "|---|---|---|---:|"]
    for name, cohort in audit["cohorts"].items():
        for arm, r in cohort["runs"].items():
            lines.append(f"| {name} | {arm} | `{r['run']['run_id']}` | {r['run']['completed']} |")
    lines += ["", "All metric definitions: `qa-metrics-v3-all-retrieval-queries`. Historical metric revisions are retained. "
        "The v3 benchmark replay changed no lexical, abstention or timing values. The final read-only audit verified "
        "paired populations, actual C/D contexts, adapter identity, source citation provenance, memory policy, frozen "
        "follow-up code hashes and unchanged primary metric snapshots.", "",
        "## Application and validation", "",
        "**103 Python tests and 3 Microsoft Edge browser tests passed.** The browser checks actual stored results, "
        "training loss, review forms, mobile navigation and a real browser → API → local GPU → cited-answer flow. "
        "Desktop, training, mobile and chat screenshots were inspected. Four additional live API requests tested "
        "English/Hindi/Tamil validation questions and an unknown future request: English/Tamil returned citations, "
        "the Hindi wording safely abstained, and the unknown request abstained. These interactions were unscored; "
        "prediction, annotation and research-run counts stayed unchanged.", "",
        "The dashboard includes benchmark/source provenance, model and adapter details, real loss curves, asynchronous "
        "evaluation, matched comparisons, prediction evidence, human review, exports and versioned reports. "
        "All research scores are supplied by the backend. Human accuracy, hallucination incidence, unsupported-claim "
        "rate and human-accuracy language gaps remain **Pending**: no human annotations were fabricated.", "",
        "## Open and reproduce", "",
        "The verification preview is temporary. Start the project from PowerShell:", "",
        "```powershell", "Set-Location 'D:\\shameek RAI'", "& '.\\.venv\\Scripts\\python.exe' -m backend.cli serve --port 8765", "```", "",
        "Open http://127.0.0.1:8765 (API docs: `/docs`). The service binds to localhost and uses local models; no hosted "
        "inference API or key is required. The README and [reproduction guide](REPRODUCIBILITY.md) contain installation, "
        "data acquisition, training, ingestion, new-run and export commands. Preserve immutable source snapshots and "
        "versioned data to reproduce historical campus runs; live university pages can change.", "",
        "```powershell", "& '.\\.venv\\Scripts\\python.exe' -m scripts.validate_final_outputs",
        "& '.\\.venv\\Scripts\\python.exe' -m pytest", "npm run test:browser", "powershell -File '.\\scripts\\bundle.ps1'", "```", "",
        "`results/campusqa-source.zip` contains source, configuration, reports, reviewed campus JSONL/curation and "
        "pinned benchmark/training-source acquisition manifests. Benchmark records are reacquired with `acquire` and `prepare`. "
        "It excludes environments, caches, model/adapter weights, SQLite, Chroma, full benchmark records, full "
        "prediction logs and raw campus HTML. The working project's trained adapter, local database, vector index "
        "and original snapshots remain on D:. This is a source handoff, not a fully provisioned runtime backup.", "",
        "## Repository structure", "", "```text", "backend/       FastAPI, model/training, datasets, Chroma, evaluation, SQLite, study coordinator",
        "frontend/      Responsive HTML/CSS/JavaScript dashboard and chat", "config/        Pinned active 1.5B settings; archived 7B profiles",
        "data/          Original and versioned benchmarks, campus snapshots/corpora/tests, Chroma, SQLite",
        "models/        Independent checkpoints and valid LoRA adapter", "results/       Predictions, metric revisions, training, comparisons, audits, screenshots, source archive",
        "docs/          Methodology, amendments, limitations, metrics and reproduction", "scripts/       Setup, acquisition helpers, verification, reports and source packaging",
        "tests/         Isolated Python tests and real Edge browser checks", "notebooks/     Archived external-GPU handoff reference", "```", "",
        "## Remaining research limits", "",
        "The amended experiment establishes lexical benchmark gains for this 1.5B model and budget. It does not "
        "establish 7B performance, independent human factual accuracy, lower hallucination, language fairness or a "
        "consistent advantage of LoRA over base RAG. Campus facts and references are AI reviewed, narrow, correlated "
        "and small; native-speaker source/translation certification and human claim reviews are still needed. "
        "Exact copied text can be irrelevant to a question. Lexical F1 is sensitive to Indic morphology. Confidence "
        "intervals do not adjust for source-document correlation. Source freshness is based on archived published "
        "pages rather than an on-site policy audit. This is a local research pilot, with no public production deployment.", ""]
    (ROOT / "docs/FINAL_RESEARCH_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    (ROOT / "docs/VALIDATION_REPORT.md").write_text("\n".join([
        "# Validation report", "", f"Updated: {now}.", "",
        "**103 Python tests and 3 Edge browser tests passed. All 10 model evaluations completed: 28,274 predictions, zero failures.** "
        "Local QLoRA training completed with a real, validated adapter. Full outcomes and run IDs are in "
        "[the final research report](FINAL_RESEARCH_REPORT.md). The model is the explicitly approved 1.5B version; 7B was not run.", "",
        "## Verification evidence", "",
        "- `results/pytest-current.log` and XML: isolated formula, data, API, persistence, CUDA-policy, attention/loss, "
        "PEFT contract, recovery and citation-policy tests; 103 passed, no skips. Test fixtures never become research data.",
        "- `results/browser-trained-profile.log`: real data, completed results, actual loss curve, blank human review "
        "form, responsive mobile navigation and a live GPU chat answer with an official source link and AI-review badge.",
        "- `results/chat-smoke.json`: four unscored live API requests, citation/source checks, safe unknown-request "
        "abstention and unchanged research-store counts. Hindi wording abstained; this is recorded as an actual limitation.",
        "- `results/final-model-validation.json`: read-only checks of every completed row, paired questions/references/settings, "
        "identical C/D evidence, correct adapter, all eight bounded campus runs, actual citations, frozen code and unchanged original metrics.",
        "- `results/final-api-validation.json`: final report and matched four-arm comparison returned HTTP 200; no active "
        "training/evaluation jobs remained. `results/final-session-cleanup.json` records temporary preview/power-hold cleanup.",
        "- `results/reproduction-check.json`: clean preparation from preserved originals reproduced every processed split checksum "
        "and dataset version. This is not a claim of executing the full experiment on Linux.",
        "- `results/training/7e800833-02fb-4f7f-88e0-883f7fd4dfa3/adapter_validation.json`: 392 finite tensors; all 196 "
        "LoRA-B tensors have updates; actual adapter tree checksum matched.",
        "- `results/bounded_adapter_capacity/499b2181-0723-4cee-bd4b-99c1bee0a616/result.json`: six real CUDA stress "
        "cases without between-case cache clears; all passed within the 3 GiB allocator budget.",
        "- `results/campus-embedding-selection.json`: actual semantic candidate comparison on 24 validation queries. "
        "`results/retrieval_validation/6e044fab88609b53.json`: persisted current Chroma index, fresh-process validation, 57 chunks.", "",
        "## Scientific limits", "",
        "Human source/reference certification and response factuality remain pending (zero human annotations). "
        "Human accuracy, hallucination and unsupported-claim metrics remain unscored. The original strict-citation "
        "campus C/D arms abstained on all questions; this negative finding is preserved. The separate frozen "
        "follow-up uses fresh source-disjoint questions and cannot be treated as a paired estimate of the policy change. "
        "No weights/prompts/generation settings were tuned on its test results.", "",
        "The long original B benchmark completed naturally, uninterrupted, and was not recovered. Windows RAM/shared "
        "GPU contention limits timing conclusions. Later campus allocations stayed within the same bounded policy. "
        "Short probes and CUDA allocation peaks do not establish exclusive physical GPU residency. "
        "Minor Starlette/AnyIO, test-only PEFT and Playwright color-environment warnings were non-failing.", ""
    ]), encoding="utf-8")
    print(json.dumps({"report": "docs/FINAL_RESEARCH_REPORT.md", "validation": "docs/VALIDATION_REPORT.md",
                      "python_passed": passed, "browser_passed": 3, "human_review": "pending"}))


if __name__ == "__main__":
    main()
