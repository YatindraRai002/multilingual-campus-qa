# Validation report

Updated: 2026-11-08T23:28:35.764055+00:00.

**103 Python tests and 3 Edge browser tests passed. All 10 model evaluations completed: 28,274 predictions, zero failures.** Local QLoRA training completed with a real, validated adapter. Full outcomes and run IDs are in [the final research report](FINAL_RESEARCH_REPORT.md). The model is the explicitly approved 1.5B version; 7B was not run.

## Verification evidence

- `results/pytest-current.log` and XML: isolated formula, data, API, persistence, CUDA-policy, attention/loss, PEFT contract, recovery and citation-policy tests; 103 passed, no skips. Test fixtures never become research data.
- `results/browser-trained-profile.log`: real data, completed results, actual loss curve, blank human review form, responsive mobile navigation and a live GPU chat answer with an official source link and AI-review badge.
- `results/chat-smoke.json`: four unscored live API requests, citation/source checks, safe unknown-request abstention and unchanged research-store counts. Hindi wording abstained; this is recorded as an actual limitation.
- `results/final-model-validation.json`: read-only checks of every completed row, paired questions/references/settings, identical C/D evidence, correct adapter, all eight bounded campus runs, actual citations, frozen code and unchanged original metrics.
- `results/final-api-validation.json`: final report and matched four-arm comparison returned HTTP 200; no active training/evaluation jobs remained. `results/final-session-cleanup.json` records temporary preview/power-hold cleanup.
- `results/reproduction-check.json`: clean preparation from preserved originals reproduced every processed split checksum and dataset version. This is not a claim of executing the full experiment on Linux.
- `results/training/7e800833-02fb-4f7f-88e0-883f7fd4dfa3/adapter_validation.json`: 392 finite tensors; all 196 LoRA-B tensors have updates; actual adapter tree checksum matched.
- `results/bounded_adapter_capacity/499b2181-0723-4cee-bd4b-99c1bee0a616/result.json`: six real CUDA stress cases without between-case cache clears; all passed within the 3 GiB allocator budget.
- `results/campus-embedding-selection.json`: actual semantic candidate comparison on 24 validation queries. `results/retrieval_validation/6e044fab88609b53.json`: persisted current Chroma index, fresh-process validation, 57 chunks.

## Scientific limits

Human source/reference certification and response factuality remain pending (zero human annotations). Human accuracy, hallucination and unsupported-claim metrics remain unscored. The original strict-citation campus C/D arms abstained on all questions; this negative finding is preserved. The separate frozen follow-up uses fresh source-disjoint questions and cannot be treated as a paired estimate of the policy change. No weights/prompts/generation settings were tuned on its test results.

The long original B benchmark completed naturally, uninterrupted, and was not recovered. Windows RAM/shared GPU contention limits timing conclusions. Later campus allocations stayed within the same bounded policy. Short probes and CUDA allocation peaks do not establish exclusive physical GPU residency. Minor Starlette/AnyIO, test-only PEFT and Playwright color-environment warnings were non-failing.
