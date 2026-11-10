# Environment report

The initial hardware audit was measured at 2026-11-07T15:59:49.686728+00:00 (UTC). The original 7B assessment is archived in `ENVIRONMENT_REPORT_ORIGINAL_MODEL.md`. Current model capacity was measured at 2026-11-07T17:58:36.013922+00:00.

## Architecture

The workspace was initially empty. This project uses FastAPI, SQLite, ChromaDB and a buildless JavaScript dashboard. Python, dependencies and caches are project-local on D:.

## Audited hardware and runtime

- CPU: Intel64 Family 6 Model 141 Stepping 1, GenuineIntel; 6 physical / 12 logical cores.
- RAM: 23.73 GiB installed.
- GPU: NVIDIA GeForce RTX 2050, 4.0 GiB dedicated VRAM; driver 592.00.
- Python: 3.11.14.
- PyTorch: 2.7.1+cu126; CUDA runtime 12.6; real CUDA matrix check: passed.
- Model: Qwen/Qwen2.5-1.5B-Instruct; revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`. Official checkpoint: 3,087,467,144 bytes, SHA-256 verified.

## Approved local execution

The user explicitly approved 1.5B in place of 7B for the laptop experiment. The original 7B configuration exceeds 4 GiB and remains archived. Local results apply to 1.5B only.

The real 9,216-token inference probe peaked at 1.906 GiB of CUDA tensor allocation; four-by-1,024-token inference peaked at 1.447 GiB. Three training forward/backward/optimizer probes peaked at 2.311 GiB. These short probes stayed within the 3.122 GiB allocation budget and explicitly cleared cache between probes. They do not establish bounded allocator reservations or dedicated-memory residency across thousands of varying input shapes. Probe adapters were discarded.

NF4/double quantization, FP16, rank 8, batch 1, sequence length 1024, accumulation 16 and gradient checkpointing are configured. Explicit grouped-query KV-head expansion avoids the installed Windows build's quadratic SDPA fallback; causal/padding output and gradient equivalence tests passed. Answer-only logits projection preserves the exact supervised loss while reducing memory.

Actual training follows full baseline completion. Static memory estimates and compatibility probes are not completed training or evaluation. Current process status is in `results/studies/` and the dashboard. Do not launch overlapping GPU jobs.

## Storage and dependencies

C: had little free space; runtime, HF/npm/uv caches, original datasets, checkpoints and outputs are kept on D:. The project drive had 717.31 GiB free at initial audit. The project-local Windows inventory is `requirements-local-lock.txt`; portable pinned requirements are in `requirements*.txt`. No system driver was modified.

```json
{
  "torch": "2.7.1+cu126",
  "transformers": "4.57.3",
  "peft": "0.18.0",
  "bitsandbytes": "0.48.2",
  "accelerate": "1.12.0",
  "sentence-transformers": "5.1.2",
  "chromadb": "1.3.5",
  "fastapi": "0.115.12",
  "uvicorn": "0.34.2"
}
```

Full capacity measurements: `results/local_model_preflight.json`. The earlier shared-memory fallback probe is archived separately and is not evidence of fitting dedicated VRAM.

The full LoRA benchmark later showed substantial Windows shared GPU memory use (`results/studies/0f3dfb3d-298f-47c1-a020-4be01eb4bcec/runtime_health/shared_gpu_memory_before_stop.json`). Its original worker had no enforced allocator budget and completed all 13,921 predictions naturally, uninterrupted, as requested. The proposed stop/recovery was not executed. All eight subsequent campus runs used `config/runtime_gpu.yaml` to bound PyTorch's allocator to 75% of visible VRAM (3 GiB here), with measured peak reserved bytes below budget. A six-case real adapter stress check, including 9,216 input tokens and 192 forced output tokens without between-case cache clears, also passed: peak allocated 2,637,300,224 bytes, peak reserved 3,066,036,224 bytes, budget 3,220,832,256 bytes. Evidence: `results/bounded_adapter_capacity/499b2181-0723-4cee-bd4b-99c1bee0a616/result.json`. Actual Windows residency still depends on other desktop usage; an allocator budget does not reserve physical VRAM exclusively.
