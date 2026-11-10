# LoRA training report

```json
{
  "training_id": "7e800833-02fb-4f7f-88e0-883f7fd4dfa3",
  "model_id": "Qwen/Qwen2.5-1.5B-Instruct",
  "model_revision": "989aa7980e4cf806f80c7fef2b1adb7bc71aa306",
  "dataset_version": "acbff74f81c1a1d1",
  "configuration": {
    "lora_rank": 8,
    "lora_alpha": 16,
    "lora_dropout": 0.05,
    "target_modules": [
      "q_proj",
      "k_proj",
      "v_proj",
      "o_proj",
      "gate_proj",
      "up_proj",
      "down_proj"
    ],
    "learning_rate": 0.0001,
    "batch_size": 1,
    "gradient_accumulation_steps": 16,
    "epochs": 2,
    "warmup_ratio": 0.03,
    "weight_decay": 0.01,
    "max_sequence_length": 1024,
    "gradient_checkpointing": true,
    "precision": "float16",
    "optimizer": "paged_adamw_8bit",
    "seed": 42,
    "language_balanced_sampling": false,
    "language_balanced_selection": true,
    "maximum_training_examples_per_language": 256,
    "maximum_validation_examples_per_language": 32,
    "supervised_logits_only": true,
    "required_training_languages": [
      "en",
      "hi",
      "ta"
    ],
    "abstention_augmentation": true,
    "abstention_fraction": 0.1,
    "evaluation_steps": 20,
    "save_steps": 20
  },
  "hardware": {
    "measured_at": "2026-11-08T00:05:49.068653+00:00",
    "os": "Windows-10-10.0.26300-SP0",
    "cpu": "Intel64 Family 6 Model 141 Stepping 1, GenuineIntel",
    "physical_cores": 6,
    "logical_cores": 12,
    "ram_gib": 23.73,
    "available_ram_gib": 5.25,
    "project_disk_free_gib": 709.79,
    "python": "3.11.14",
    "python_executable": "D:\\shameek RAI\\.venv\\Scripts\\python.exe",
    "gpu": {
      "name": "NVIDIA GeForce RTX 2050",
      "total_vram_gib": 4.0,
      "free_vram_gib": 3.59,
      "driver": "592.00",
      "compute_capability": "8.6"
    },
    "cuda_test": "passed",
    "dependencies": {
      "torch": "2.7.1+cu126",
      "transformers": "4.57.3",
      "peft": "0.18.0",
      "bitsandbytes": "0.48.2",
      "accelerate": "1.12.0",
      "sentence-transformers": "5.1.2",
      "chromadb": "1.3.5",
      "fastapi": "0.115.12",
      "uvicorn": "0.34.2"
    },
    "pytorch_cuda": "12.6",
    "bf16_supported": true,
    "training_readiness": {
      "ready": true,
      "blockers": [],
      "required_free_vram_gib": 2.5,
      "recommended_vram_gib": 4
    }
  },
  "started_at": "2026-11-08T00:06:01.434050+00:00",
  "training_counts": {
    "en": 78437,
    "hi": 8954,
    "ta": 8950
  },
  "validation_counts": {
    "en": 8961,
    "hi": 1044,
    "ta": 1047
  },
  "status": "completed",
  "used_training_counts": {
    "en": 256,
    "hi": 256,
    "ta": 256
  },
  "training_abstention_augmentation_count": 68,
  "training_abstention_augmentation_by_language": {
    "en": 25,
    "hi": 17,
    "ta": 26
  },
  "used_validation_counts": {
    "en": 32,
    "hi": 32,
    "ta": 32
  },
  "dropped_overlength_training_counts": {
    "en": 5,
    "hi": 2052,
    "ta": 4549
  },
  "dropped_overlength_validation_counts": {
    "hi": 279,
    "ta": 579
  },
  "selection_sha256": "aedb8bda2474c94a2727ca8090c4b53e16bf6715439863d4f985dd635e1510f9",
  "selection_manifest": "results/training/7e800833-02fb-4f7f-88e0-883f7fd4dfa3/selection.json",
  "total_optimizer_steps": 106,
  "training_examples_including_augmentation": 836,
  "validation_examples": 96,
  "ended_at": "2026-11-08T01:04:55.385788+00:00",
  "duration_seconds": 3533.9171452000155,
  "best_checkpoint": "D:\\shameek RAI\\models\\qwen2.5-1.5b\\training\\7e800833-02fb-4f7f-88e0-883f7fd4dfa3\\checkpoint-80",
  "best_validation_loss": 0.3460770547389984,
  "adapter_path": "models/qwen2.5-1.5b/lora_adapter/7e800833-02fb-4f7f-88e0-883f7fd4dfa3",
  "adapter_revision": "3e2e65278413ed82c219d9b0c60c88cea0c1bfc22243f6af9772d13df1b2798d",
  "peak_gpu_memory_gib": 2.435372829437256
}
```
