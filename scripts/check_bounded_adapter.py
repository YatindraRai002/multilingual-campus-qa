"""Stress the trained adapter's allocator budget using synthetic inputs, after benchmark B."""
from __future__ import annotations

import argparse
import json
import time
import uuid
from contextlib import ExitStack
from pathlib import Path

from backend.artifacts import tree_fingerprint
from backend.db import Database
from backend.experiments import gpu_lock
from backend.gpu_memory import apply_inference_memory_policy, memory_observation, memory_policy
from backend.modeling import QwenEngine, adapter_manifest
from backend.settings import ROOT, config, read_json, utcnow, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("study_id")
    args = parser.parse_args()
    state = read_json(ROOT / "results" / "studies" / args.study_id / "state.json")
    if not state or not state.get("run_ids", {}).get("benchmark_B"):
        parser.error("The study must have a completed benchmark B")
    run = Database().run(state["run_ids"]["benchmark_B"])
    if not run or run["status"] != "completed" or state.get("stage") == "benchmark_B":
        parser.error("Wait for the uninterrupted benchmark and its coordinator comparison to finish")
    adapter = adapter_manifest()
    if adapter["adapter_revision"] != state.get("adapter_revision"):
        parser.error("Current trained adapter differs from this study")
    selected = config("model_config")
    if selected["revision"] != run["configuration"]["model_revision"]:
        parser.error("Pinned model differs from the completed benchmark")
    result = {"started_at": utcnow(), "status": "running", "research_run": False,
              "study_id": args.study_id, "model_id": selected["model_id"],
              "model_revision": selected["revision"], "adapter_revision": adapter["adapter_revision"],
              "input_source": "synthetic repeated token tensors; no benchmark or campus questions",
              "training_performed": False, "cache_cleared_between_cases": False,
              "probe_generation": {**selected["generation"],
                                   "min_new_tokens": selected["generation"]["max_new_tokens"]},
              "interpretation": "CUDA allocator capacity and repeated-shape stress only; not quality, dedicated-memory residency or a long-run guarantee.",
              "cases": []}
    folder = ROOT / "results" / "bounded_adapter_capacity" / str(uuid.uuid4())
    # A zero-timeout lock refuses to compete with any current project GPU job.
    with gpu_lock().acquire(timeout=0), ExitStack() as cleanup:
        folder.mkdir(parents=True, exist_ok=False)
        try:
            import psutil
            import torch

            result["allocator"] = apply_inference_memory_policy(memory_policy(), torch_module=torch)
            result["device"] = torch.cuda.get_device_name(0)
            engine = QwenEngine(adapter)
            cleanup.callback(engine.close)
            result["loading_seconds"] = engine.loading_seconds
            torch.cuda.reset_peak_memory_stats()
            # Vary sizes and revisit them without empty_cache to expose cache growth.
            shapes = [(4, 1024), (1, 4096), (1, 8192),
                      (1, selected["max_input_tokens"]), (4, 1024),
                      (1, selected["max_input_tokens"])]
            for batch, length in shapes:
                inputs = torch.full((batch, length), 100, device="cuda", dtype=torch.long)
                mask = torch.ones_like(inputs)
                torch.cuda.synchronize()
                started = time.perf_counter()
                with torch.inference_mode():
                    outputs = engine.model.generate(
                        input_ids=inputs, attention_mask=mask, **result["probe_generation"],
                        pad_token_id=engine.tokenizer.pad_token_id, logits_to_keep=1)
                torch.cuda.synchronize()
                expected = length + selected["generation"]["max_new_tokens"]
                if tuple(outputs.shape) != (batch, expected):
                    raise RuntimeError("The worst-case synthetic probe ended before the configured generation budget")
                observation = {"batch_size": batch, "input_tokens_per_sequence": length,
                               "output_tokens_per_sequence": expected - length,
                               "seconds": time.perf_counter() - started,
                               "memory": memory_observation(engine),
                               "host_available_ram_bytes": psutil.virtual_memory().available}
                result["cases"].append(observation)
                del inputs, mask, outputs
                write_json(folder / "result.json", result)
                print(json.dumps(observation), flush=True)
            result["memory"] = memory_observation(engine)
            if result["memory"]["peak_reserved_bytes"] > result["allocator"]["allocator_budget_bytes"]:
                raise RuntimeError("Observed caching-allocator reservation exceeds its configured budget")
            if tree_fingerprint(Path(adapter["adapter_path"])) != adapter["adapter_revision"]:
                raise RuntimeError("Adapter bytes changed during an inference-only capacity check")
            result["adapter_checksum_unchanged"] = True
            result["status"] = "passed"
        except Exception as error:
            result.update(status="failed", error=f"{type(error).__name__}: {error}")
            raise
        finally:
            cleanup.close()
            result["ended_at"] = utcnow()
            write_json(folder / "result.json", result)
            print(json.dumps({"status": result["status"], "artifact": str(folder / "result.json")}), flush=True)


if __name__ == "__main__":
    main()
