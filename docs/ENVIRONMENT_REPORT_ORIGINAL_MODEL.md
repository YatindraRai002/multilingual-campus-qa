# Environment report

Measured at 2026-11-07T15:59:49.686728+00:00 (UTC). This workspace was empty before implementation.

## Architecture
FastAPI Python API, SQLite experiment store, ChromaDB retrieval, and a buildless JavaScript dashboard.
No existing application or database was overwritten. Node is optional for browser tests only.

## Measured hardware
- OS: Windows-10-10.0.26300-SP0
- CPU: Intel64 Family 6 Model 141 Stepping 1, GenuineIntel; 6 physical / 12 logical cores
- RAM: 23.73 GiB total; 3.54 GiB available at audit
- GPU: NVIDIA GeForce RTX 2050; 4.0 GiB total,
  3.5 GiB free; driver 592.00; compute 8.6
- Project drive free: 717.31 GiB
- Python: 3.11.14; D:\shameek RAI\.venv\Scripts\python.exe
- PyTorch CUDA test: passed

## Capacity estimates (not measured training usage)
Official 7.61B-parameter checkpoint: approximately 15.2 GB decimal in BF16 on disk.
Budget 25–35 GB disk for checkpoint/cache, adapters, and run artifacts; 40 GB free recommended.
NF4 weights plus unquantized tensors, runtime, optimizer, activations and adapter gradients exceed
4 GiB. This implementation requires 12 GiB free for short-sequence QLoRA and recommends >=16 GiB.
Actual peak memory must be measured on the target GPU. A 4 GiB GPU is not approved for 7B training.

## Recommendation
Keep Qwen/Qwen2.5-7B-Instruct, NF4/double quantization, FP16, rank 8, batch 1,
sequence length 1024, gradient accumulation 16 and gradient checkpointing.
Use an external >=16 GiB CUDA GPU (Colab T4 or larger); no model substitution is authorized.
The user explicitly selected retaining 7B after the laptop VRAM audit.
C: had only about 1.44 GiB free at initial audit; runtime, caches, and data are placed on D:.
See the JSON audit for exact dependency versions and checks. Driver CUDA capability is not a
statement that a CUDA toolkit or CUDA-enabled PyTorch is installed.

## Current blockers
- Qwen2.5-7B needs at least 12 GiB free VRAM for this configuration; NVIDIA GeForce RTX 2050 currently has 3.5 GiB free.

## Dependency inventory
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
