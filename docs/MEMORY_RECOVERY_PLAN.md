# Controlled recovery of the local LoRA benchmark

> Historical, unexecuted proposal. The original worker later completed all 13,921 predictions naturally, uninterrupted, on 8 November 2026. No recovery run was created. The identifiers below describe that completed historical worker, not an active process. All later campus runs used the bounded allocator and passed; see the final research report.

This proposal is prepared and tested. The user chose **Keep the current run uninterrupted**, so the proposed stop/recovery is **not executed**. The active worker continues with its original settings. The allocator limit is ready for subsequent runs.

The source is run `fc7c6a02-bb45-4aed-8ecb-35b2611ddb07`, actual inference PID 35664 (creation time 1794099903.415357), registered launcher PID 11308. A read-only checkpoint at 2026-11-08T04:57:01 UTC recorded 11,948 of 13,921 saved predictions, with prefix checksum `e0b3b57005d3b9d92e037686e4f5cc89500a7daa7c14fe3f7415f2a5894012cb`. More results may finish before a stop; the stop script checkpoints the latest prefix again.

Windows process counters showed over 5.6 GiB of shared GPU memory associated with this worker, contributing to system RAM pressure. Production inference had no enforced allocator budget. The short initial capacity probes measured allocated peaks and explicitly emptied cache between probes; they did not establish bounded cache residency across thousands of varying input shapes.

The proposed operation is:

1. Revalidate the exact worker's command, project directory, process creation time and registered launcher. Checksum all currently saved prediction bytes.
2. Stop only that inference worker, wait for both worker and launcher to exit, then let normal interrupted-job recovery record terminal status. Verify that every previously saved prediction byte remains unchanged. An unfinished, unsaved answer will be recomputed.
3. Apply a CUDA allocator limit of 75% of visible device memory: 3 GiB on this 4 GiB GPU. Validate the trained adapter at the required long input lengths with this limit before continuing. This controls memory management; it does not change weights, prompts, references, generation settings, sampling or checkpoint selection.
4. Create a new recovery run with the same complete test population and frozen model settings. Reuse successful complete batches as actual measured observations, each linked to its source prediction ID. Keep the original interrupted run intact. Regenerate incomplete batches and questions without saved observations. Do not copy human annotations.
5. Resume the existing study using that recovery run, complete the benchmark, and then proceed to campus collection and A/B/C/D comparisons.

The correctness population remains unchanged. Timings combine original and recovered execution segments under substantial desktop contention and a changed allocator policy; they cannot isolate adapter overhead. All original measured durations remain present. No artificial predictions or metric values are introduced.

Validation: 22 isolated tests passed in `results/memory-recovery-validation.log`. They cover active-worker refusal, frozen generation checks, partial-batch handling, source checksums, original run preservation, unique prediction IDs, pending-only generation, no copied human annotations, allocator bounds, and cleanup ordering. These use temporary CPU fixtures and are not model-quality evidence. The actual adapter capacity check requires the currently occupied GPU to be released first.

Reviewable code: `scripts/stop_evaluation_worker.py`, `backend/recovery.py`, `backend/gpu_memory.py`, `config/runtime_gpu.yaml`. The stop script defaults to a read-only proposal. Only its explicit `--apply` mode stops the verified worker.

Automatic approval review rejected the earlier proposal to mark the run interrupted while its worker remained alive, because of possible continued writes and inconsistent state. This revised procedure stops and confirms the writer's exit before changing status. Explicit user approval is requested for that controlled interruption. Until then the benchmark continues running.
