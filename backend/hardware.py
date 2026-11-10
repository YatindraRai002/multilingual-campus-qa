from __future__ import annotations

import importlib.metadata
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

import psutil

from backend.settings import ROOT, config, read_json, utcnow, write_json


def audit(check_torch: bool = False) -> dict:
    memory = psutil.virtual_memory()
    disk = shutil.disk_usage(ROOT)
    result = {
        "measured_at": utcnow(), "os": platform.platform(),
        "cpu": platform.processor(), "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(), "ram_gib": round(memory.total / 2**30, 2),
        "available_ram_gib": round(memory.available / 2**30, 2),
        "project_disk_free_gib": round(disk.free / 2**30, 2),
        "python": sys.version.split()[0], "python_executable": sys.executable,
        "gpu": None, "cuda_test": "not_run", "dependencies": {},
    }
    try:
        proc = subprocess.run([
            "nvidia-smi", "--query-gpu=name,memory.total,memory.free,driver_version,compute_cap",
            "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=15)
        if proc.returncode == 0:
            parts = [v.strip() for v in proc.stdout.splitlines()[0].split(",")]
            result["gpu"] = dict(name=parts[0], total_vram_gib=round(float(parts[1])/1024, 2),
                                 free_vram_gib=round(float(parts[2])/1024, 2),
                                 driver=parts[3], compute_capability=parts[4])
    except (OSError, subprocess.TimeoutExpired, IndexError, ValueError) as exc:
        result["gpu_probe_error"] = str(exc)
    for name in ["torch", "transformers", "peft", "bitsandbytes", "accelerate",
                 "sentence-transformers", "chromadb", "fastapi", "uvicorn"]:
        try:
            result["dependencies"][name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result["dependencies"][name] = None
    if check_torch:
        try:
            import torch
            result["pytorch_cuda"] = torch.version.cuda
            if torch.cuda.is_available():
                a = torch.ones((32, 32), device="cuda")
                result["cuda_test"] = "passed" if (a @ a)[0, 0].item() == 32 else "failed"
                result["bf16_supported"] = torch.cuda.is_bf16_supported()
                torch.cuda.empty_cache()
            else:
                result["cuda_test"] = "cuda_unavailable"
        except Exception as exc:
            result["cuda_test"] = "failed"
            result["cuda_error"] = str(exc)
    result["training_readiness"] = readiness(result, training=True)
    return result


def readiness(hardware: dict | None = None, *, training=False) -> dict:
    hardware = hardware or audit()
    model = config("model_config")
    required = model["min_training_vram_gib" if training else "min_inference_vram_gib"]
    gpu = hardware.get("gpu")
    blockers = []
    if not gpu:
        blockers.append("A CUDA GPU is required for the configured 4-bit Qwen execution.")
    elif gpu["free_vram_gib"] < required:
        blockers.append(f"{model['model_id']} needs at least {required} GiB free VRAM for this configuration; "
                        f"{gpu['name']} currently has {gpu['free_vram_gib']} GiB free.")
    for name in ["torch", "transformers", "bitsandbytes", "accelerate"] + (["peft"] if training else []):
        if not hardware.get("dependencies", {}).get(name):
            blockers.append(f"Missing ML dependency: {name}.")
    if hardware.get("cuda_test") in {"failed", "cuda_unavailable"}:
        blockers.append("The PyTorch CUDA smoke test did not pass.")
    return {"ready": not blockers, "blockers": blockers, "required_free_vram_gib": required,
            "recommended_vram_gib": model["recommended_training_vram_gib"] if training else 8}


def save_report(check_torch=False):
    result = audit(check_torch)
    write_json(ROOT / "results" / "environment.json", result)
    gpu = result["gpu"] or {}
    selected = config('model_config')
    training = config('training')
    metadata = read_json(ROOT/'results'/'model_registry.json',{})
    capacity = read_json(ROOT/'results'/'local_model_preflight.json')
    report = f"""# Environment report

Measured at {result['measured_at']} (UTC). This workspace was empty before implementation.

## Architecture
FastAPI Python API, SQLite experiment store, ChromaDB retrieval, and a buildless JavaScript dashboard.
No existing application or database was overwritten. Node is optional for browser tests only.

## Measured hardware
- OS: {result['os']}
- CPU: {result['cpu']}; {result['physical_cores']} physical / {result['logical_cores']} logical cores
- RAM: {result['ram_gib']} GiB total; {result['available_ram_gib']} GiB available at audit
- GPU: {gpu.get('name', 'unavailable')}; {gpu.get('total_vram_gib', 'unknown')} GiB total,
  {gpu.get('free_vram_gib', 'unknown')} GiB free; driver {gpu.get('driver', 'unknown')}; compute {gpu.get('compute_capability', 'unknown')}
- Project drive free: {result['project_disk_free_gib']} GiB
- Python: {result['python']}; {result['python_executable']}
- PyTorch CUDA test: {result['cuda_test']}

## Active study and capacity
Selected model: {selected['model_id']} at revision {selected['revision']}.
Checkpoint bytes from the official model metadata: {metadata.get('checkpoint_bytes','not inspected')}.
Configured free-VRAM gate: {selected['min_training_vram_gib']} GiB for training;
recommended installed GPU memory: {selected['recommended_training_vram_gib']} GiB.

The user explicitly approved Qwen2.5-1.5B for local GPU execution after the original 7B
configuration exceeded the laptop's 4 GiB capacity. Original model/training profiles and the
initial environment report are preserved separately. No 1.5B result may be presented as a 7B result.

NF4/double quantization, FP16, rank {training['lora_rank']}, batch {training['batch_size']},
sequence length {training['max_sequence_length']}, accumulation {training['gradient_accumulation_steps']}
and gradient checkpointing are selected. Actual model memory preflight:

```json
{json.dumps(capacity,indent=2) if capacity else 'Model-capacity preflight has not completed yet.'}
```

C: had little free disk space at the initial audit. Runtime, caches, downloads and artifacts
stay on D:. CUDA driver capability and a CUDA toolkit installation are different; the
PyTorch calculation above tests the actual installed runtime. Initial capacity estimates
are in ENVIRONMENT_REPORT_ORIGINAL_MODEL.md; the current model preflight is measured separately.

## Current blockers
{chr(10).join('- ' + item for item in result['training_readiness']['blockers']) or 'None detected by static gate; still run preflight.'}

## Dependency inventory
```json
{json.dumps(result['dependencies'], indent=2)}
```
"""
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "ENVIRONMENT_REPORT.md").write_text(report, encoding="utf-8")
    return result
