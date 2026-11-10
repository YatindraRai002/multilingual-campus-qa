# LoRA evaluation report

Generated from the persisted experiment at 2026-11-08T22:01:41.176820+00:00.

Run ID: fc7c6a02-bb45-4aed-8ecb-35b2611ddb07

Status: completed

Track: benchmark

Dataset version: acbff74f81c1a1d1

English SQuAD and Hindi/Tamil IndicQA are separate populations. Null factuality metrics mean insufficient human annotations, not zero error or zero accuracy. Confidence intervals and metric denominators are included with the calculated results. Failed-record exclusions remain explicit.

```json
{
  "run": {
    "run_id": "fc7c6a02-bb45-4aed-8ecb-35b2611ddb07",
    "track": "benchmark",
    "experiment": "B",
    "status": "completed",
    "dataset_version": "acbff74f81c1a1d1",
    "evaluation_fingerprint": "d151264a4bd8987e21f2a1fe2b411e4bfcbb280760a33b5d9c74340ee5ae8683",
    "configuration": {
      "model_id": "Qwen/Qwen2.5-1.5B-Instruct",
      "model_revision": "989aa7980e4cf806f80c7fef2b1adb7bc71aa306",
      "adapter": {
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
        "adapter_path": "D:\\shameek RAI\\models\\qwen2.5-1.5b\\lora_adapter\\7e800833-02fb-4f7f-88e0-883f7fd4dfa3",
        "adapter_revision": "3e2e65278413ed82c219d9b0c60c88cea0c1bfc22243f6af9772d13df1b2798d",
        "peak_gpu_memory_gib": 2.435372829437256
      },
      "prompt_version": "grounded-qa-v1",
      "generation": {
        "max_new_tokens": 192,
        "do_sample": false,
        "repetition_penalty": 1.0
      },
      "max_input_tokens": 9216,
      "seed": 42,
      "hardware": {
        "measured_at": "2026-11-08T01:04:59.251104+00:00",
        "os": "Windows-10-10.0.26300-SP0",
        "cpu": "Intel64 Family 6 Model 141 Stepping 1, GenuineIntel",
        "physical_cores": 6,
        "logical_cores": 12,
        "ram_gib": 23.73,
        "available_ram_gib": 7.18,
        "project_disk_free_gib": 709.6,
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
      "ingestion": null,
      "limit_per_language": null,
      "evidence_as_of": "2026-11-08T01:05:03.153515+00:00",
      "context_condition": "supplied_benchmark_context",
      "inference_execution": {
        "maximum_batch_size": 4,
        "batch_token_budget": 4096,
        "batching_policy": "language/input-length/stable-ID; no reference-answer selection"
      },
      "model_execution": {
        "attention_implementation": "explicit_gqa_sdpa",
        "quantization": "nf4",
        "double_quantization": true,
        "compute_dtype": "float16"
      },
      "test_ids_summary": {
        "count": 13921,
        "sha256": "ba4be5c48116274250b9141703bbdb9f5999eae91a759ac855702cf55cb92a17",
        "location": "/api/experiments/fc7c6a02-bb45-4aed-8ecb-35b2611ddb07/export?format=json"
      }
    },
    "created_at": "2026-11-08T01:05:03.353393+00:00",
    "ended_at": "2026-11-08T21:56:08.128025+00:00",
    "total": 13921,
    "completed": 13921,
    "error": null
  },
  "metrics": {
    "status": "scored",
    "completed_predictions": 13921,
    "excluded_failed_predictions": 0,
    "populations": {
      "SQuAD-v1.1": {
        "languages": {
          "en": {
            "count": 10570,
            "human_reviewed": 0,
            "accuracy": {
              "value": null,
              "numerator": 0,
              "denominator": 10570,
              "reviewed_or_scored": 0,
              "unit": "percent",
              "status": "pending",
              "definition": "Human-validated correct answerable responses / all answerable responses × 100.",
              "confidence_interval": null
            },
            "exact_match": {
              "value": 77.52128666035951,
              "numerator": 8194.0,
              "denominator": 10570,
              "reviewed_or_scored": 10570,
              "unit": "percent",
              "status": "scored",
              "definition": "Best normalized reference exact match; English articles removed only for English.",
              "confidence_interval": {
                "lower": 76.74526963103122,
                "upper": 78.32592242194892,
                "level": 0.95,
                "method": "percentile_bootstrap",
                "resamples": 1000,
                "seed": 42,
                "resampling_unit": "response",
                "limitation": "Responses sharing a source document may be correlated."
              }
            },
            "f1": {
              "value": 86.07608470539529,
              "numerator": 9098.242153360283,
              "denominator": 10570,
              "reviewed_or_scored": 10570,
              "unit": "percent",
              "status": "scored",
              "definition": "Best whitespace-token reference F1 × 100; Indic combining marks preserved.",
              "confidence_interval": {
                "lower": 85.48697525360438,
                "upper": 86.66207409362084,
                "level": 0.95,
                "method": "percentile_bootstrap",
                "resamples": 1000,
                "seed": 42,
                "resampling_unit": "response",
                "limitation": "Responses sharing a source document may be correlated."
              }
            },
            "hallucination_incidence": {
              "value": null,
              "numerator": 0,
              "denominator": 10533,
              "reviewed_or_scored": 0,
              "unit": "percent",
              "status": "pending",
              "definition": "Responses with >=1 human-verified unsupported claim / all non-abstained responses × 100.",
              "confidence_interval": null
            },
            "unsupported_claim_rate": {
              "value": null,
              "numerator": 0,
              "denominator": 0,
              "status": "pending",
              "unit": "percent",
              "definition": "Human-verified unsupported factual claims / all evaluated factual claims × 100.",
              "confidence_interval": null
            },
            "recall_at_k": {
              "value": null,
              "numerator": 0,
              "denominator": 0,
              "reviewed_or_scored": 0,
              "unit": "percent",
              "status": "pending",
              "definition": "Queries retrieving a relevant document in top 4 / all retrieval queries × 100. Explicitly empty relevance lists contribute zero; missing labels leave the scope pending.",
              "confidence_interval": null
            },
            "mrr": {
              "value": null,
              "numerator": 0,
              "denominator": 0,
              "reviewed_or_scored": 0,
              "unit": "ratio",
              "status": "pending",
              "definition": "Mean reciprocal rank of the first relevant document in top 4, over all retrieval queries; empty relevance lists contribute zero.",
              "confidence_interval": null
            },
            "abstention_accuracy": {
              "value": 99.64995269631032,
              "numerator": 10533.0,
              "denominator": 10570,
              "reviewed_or_scored": 10570,
              "unit": "percent",
              "status": "scored",
              "definition": "Correct answer/abstain decisions / responses with answerability ground truth × 100.",
              "confidence_interval": {
                "lower": 99.5364238410596,
                "upper": 99.75402081362347,
                "level": 0.95,
                "method": "percentile_bootstrap",
                "resamples": 1000,
                "seed": 42,
                "resampling_unit": "response",
                "limitation": "Responses sharing a source document may be correlated."
              }
            },
            "latency": {
              "total_seconds": {
                "mean": 1.6901248794143744,
                "median": 1.4599982000654563,
                "p95": 3.1656891999882646,
                "count": 10570,
                "measurement_clusters": 2643,
                "mean_ci": {
                  "lower": 1.652597268746364,
                  "upper": 1.7280559388385512,
                  "level": 0.95,
                  "method": "generation_batch_clustered_ratio_bootstrap",
                  "resamples": 1000,
                  "valid_resamples": 1000,
                  "seed": 42,
                  "resampling_unit": "generation_batch"
                }
              },
              "retrieval_seconds": {
                "mean": 0.0,
                "median": 0.0,
                "p95": 0.0,
                "count": 10570,
                "measurement_clusters": 2643,
                "mean_ci": {
                  "lower": 0.0,
                  "upper": 0.0,
                  "level": 0.95,
                  "method": "generation_batch_clustered_ratio_bootstrap",
                  "resamples": 1000,
                  "valid_resamples": 1000,
                  "seed": 42,
                  "resampling_unit": "generation_batch"
                }
              },
              "generation_seconds": {
                "mean": 1.6788527099707304,
                "median": 1.4485997000010684,
                "p95": 3.15192069998011,
                "count": 10570,
                "measurement_clusters": 2643,
                "mean_ci": {
                  "lower": 1.6413311339330012,
                  "upper": 1.7167226648989473,
                  "level": 0.95,
                  "method": "generation_batch_clustered_ratio_bootstrap",
                  "resamples": 1000,
                  "valid_resamples": 1000,
                  "seed": 42,
                  "resampling_unit": "generation_batch"
                }
              },
              "throughput": {
                "value": 12.712641850718837,
                "numerator": 56411,
                "denominator": 4437.3939470976475,
                "unit": "tokens/s",
                "confidence_interval": {
                  "lower": 12.538912340604512,
                  "upper": 12.892559950055354,
                  "level": 0.95,
                  "method": "generation_batch_clustered_ratio_bootstrap",
                  "resamples": 1000,
                  "valid_resamples": 1000,
                  "seed": 42,
                  "resampling_unit": "generation_batch"
                },
                "definition": "Generated tokens / measured generation seconds; batch durations counted once; excludes loading and retrieval."
              }
            }
          }
        },
        "language_performance_gap": {
          "value": null,
          "unit": "percentage_points",
          "status": "pending",
          "languages": [],
          "definition": "Highest minus lowest validated language accuracy within the same source dataset.",
          "note": "This is a descriptive gap; different source datasets are never treated as parallel populations."
        }
      },
      "ai4bharat/IndicQA": {
        "languages": {
          "hi": {
            "count": 1547,
            "human_reviewed": 0,
            "accuracy": {
              "value": null,
              "numerator": 0,
              "denominator": 1052,
              "reviewed_or_scored": 0,
              "unit": "percent",
              "status": "pending",
              "definition": "Human-validated correct answerable responses / all answerable responses × 100.",
              "confidence_interval": null
            },
            "exact_match": {
              "value": 28.829993535875886,
              "numerator": 446.0,
              "denominator": 1547,
              "reviewed_or_scored": 1547,
              "unit": "percent",
              "status": "scored",
              "definition": "Best normalized reference exact match; English articles removed only for English.",
              "confidence_interval": {
                "lower": 26.6305753070459,
                "upper": 31.092436974789916,
                "level": 0.95,
                "method": "percentile_bootstrap",
                "resamples": 1000,
                "seed": 42,
                "resampling_unit": "response",
                "limitation": "Responses sharing a source document may be correlated."
              }
            },
            "f1": {
              "value": 39.22182859157651,
              "numerator": 606.7616883116885,
              "denominator": 1547,
              "reviewed_or_scored": 1547,
              "unit": "percent",
              "status": "scored",
              "definition": "Best whitespace-token reference F1 × 100; Indic combining marks preserved.",
              "confidence_interval": {
                "lower": 36.885523906532335,
                "upper": 41.449533659617664,
                "level": 0.95,
                "method": "percentile_bootstrap",
                "resamples": 1000,
                "seed": 42,
                "resampling_unit": "response",
                "limitation": "Responses sharing a source document may be correlated."
              }
            },
            "hallucination_incidence": {
              "value": null,
              "numerator": 0,
              "denominator": 1545,
              "reviewed_or_scored": 0,
              "unit": "percent",
              "status": "pending",
              "definition": "Responses with >=1 human-verified unsupported claim / all non-abstained responses × 100.",
              "confidence_interval": null
            },
            "unsupported_claim_rate": {
              "value": null,
              "numerator": 0,
              "denominator": 0,
              "status": "pending",
              "unit": "percent",
              "definition": "Human-verified unsupported factual claims / all evaluated factual claims × 100.",
              "confidence_interval": null
            },
            "recall_at_k": {
              "value": null,
              "numerator": 0,
              "denominator": 0,
              "reviewed_or_scored": 0,
              "unit": "percent",
              "status": "pending",
              "definition": "Queries retrieving a relevant document in top 4 / all retrieval queries × 100. Explicitly empty relevance lists contribute zero; missing labels leave the scope pending.",
              "confidence_interval": null
            },
            "mrr": {
              "value": null,
              "numerator": 0,
              "denominator": 0,
              "reviewed_or_scored": 0,
              "unit": "ratio",
              "status": "pending",
              "definition": "Mean reciprocal rank of the first relevant document in top 4, over all retrieval queries; empty relevance lists contribute zero.",
              "confidence_interval": null
            },
            "abstention_accuracy": {
              "value": 68.13186813186813,
              "numerator": 1054.0,
              "denominator": 1547,
              "reviewed_or_scored": 1547,
              "unit": "percent",
              "status": "scored",
              "definition": "Correct answer/abstain decisions / responses with answerability ground truth × 100.",
              "confidence_interval": {
                "lower": 65.67388493859082,
                "upper": 70.58823529411765,
                "level": 0.95,
                "method": "percentile_bootstrap",
                "resamples": 1000,
                "seed": 42,
                "resampling_unit": "response",
                "limitation": "Responses sharing a source document may be correlated."
              }
            },
            "latency": {
              "total_seconds": {
                "mean": 15.276573282222666,
                "median": 8.29358910000883,
                "p95": 33.902358199970124,
                "count": 1547,
                "measurement_clusters": 1158,
                "mean_ci": {
                  "lower": 13.552362505418506,
                  "upper": 17.086745010825663,
                  "level": 0.95,
                  "method": "generation_batch_clustered_ratio_bootstrap",
                  "resamples": 1000,
                  "valid_resamples": 1000,
                  "seed": 42,
                  "resampling_unit": "generation_batch"
                }
              },
              "retrieval_seconds": {
                "mean": 0.0,
                "median": 0.0,
                "p95": 0.0,
                "count": 1547,
                "measurement_clusters": 1158,
                "mean_ci": {
                  "lower": 0.0,
                  "upper": 0.0,
                  "level": 0.95,
                  "method": "generation_batch_clustered_ratio_bootstrap",
                  "resamples": 1000,
                  "valid_resamples": 1000,
                  "seed": 42,
                  "resampling_unit": "generation_batch"
                }
              },
              "generation_seconds": {
                "mean": 15.254089746476135,
                "median": 8.282838399987668,
                "p95": 33.88655475005486,
                "count": 1547,
                "measurement_clusters": 1158,
                "mean_ci": {
                  "lower": 13.532027517354361,
                  "upper": 17.057395473886782,
                  "level": 0.95,
                  "method": "generation_batch_clustered_ratio_bootstrap",
                  "resamples": 1000,
                  "valid_resamples": 1000,
                  "seed": 42,
                  "resampling_unit": "generation_batch"
                }
              },
              "throughput": {
                "value": 0.9308434020463247,
                "numerator": 18622,
                "denominator": 20005.513235698105,
                "unit": "tokens/s",
                "confidence_interval": {
                  "lower": 0.8132520188591748,
                  "upper": 1.083455119990551,
                  "level": 0.95,
                  "method": "generation_batch_clustered_ratio_bootstrap",
                  "resamples": 1000,
                  "valid_resamples": 1000,
                  "seed": 42,
                  "resampling_unit": "generation_batch"
                },
                "definition": "Generated tokens / measured generation seconds; batch durations counted once; excludes loading and retrieval."
              }
            }
          },
          "ta": {
            "count": 1804,
            "human_reviewed": 0,
            "accuracy": {
              "value": null,
              "numerator": 0,
              "denominator": 1277,
              "reviewed_or_scored": 0,
              "unit": "percent",
              "status": "pending",
              "definition": "Human-validated correct answerable responses / all answerable responses × 100.",
              "confidence_interval": null
            },
            "exact_match": {
              "value": 14.412416851441243,
              "numerator": 260.0,
              "denominator": 1804,
              "reviewed_or_scored": 1804,
              "unit": "percent",
              "status": "scored",
              "definition": "Best normalized reference exact match; English articles removed only for English.",
              "confidence_interval": {
                "lower": 12.914356984478934,
                "upper": 16.07538802660754,
                "level": 0.95,
                "method": "percentile_bootstrap",
                "resamples": 1000,
                "seed": 42,
                "resampling_unit": "response",
                "limitation": "Responses sharing a source document may be correlated."
              }
            },
            "f1": {
              "value": 20.588953383759186,
              "numerator": 371.4247190430157,
              "denominator": 1804,
              "reviewed_or_scored": 1804,
              "unit": "percent",
              "status": "scored",
              "definition": "Best whitespace-token reference F1 × 100; Indic combining marks preserved.",
              "confidence_interval": {
                "lower": 18.8919106201575,
                "upper": 22.35736842097001,
                "level": 0.95,
                "method": "percentile_bootstrap",
                "resamples": 1000,
                "seed": 42,
                "resampling_unit": "response",
                "limitation": "Responses sharing a source document may be correlated."
              }
            },
            "hallucination_incidence": {
              "value": null,
              "numerator": 0,
              "denominator": 1804,
              "reviewed_or_scored": 0,
              "unit": "percent",
              "status": "pending",
              "definition": "Responses with >=1 human-verified unsupported claim / all non-abstained responses × 100.",
              "confidence_interval": null
            },
            "unsupported_claim_rate": {
              "value": null,
              "numerator": 0,
              "denominator": 0,
              "status": "pending",
              "unit": "percent",
              "definition": "Human-verified unsupported factual claims / all evaluated factual claims × 100.",
              "confidence_interval": null
            },
            "recall_at_k": {
              "value": null,
              "numerator": 0,
              "denominator": 0,
              "reviewed_or_scored": 0,
              "unit": "percent",
              "status": "pending",
              "definition": "Queries retrieving a relevant document in top 4 / all retrieval queries × 100. Explicitly empty relevance lists contribute zero; missing labels leave the scope pending.",
              "confidence_interval": null
            },
            "mrr": {
              "value": null,
              "numerator": 0,
              "denominator": 0,
              "reviewed_or_scored": 0,
              "unit": "ratio",
              "status": "pending",
              "definition": "Mean reciprocal rank of the first relevant document in top 4, over all retrieval queries; empty relevance lists contribute zero.",
              "confidence_interval": null
            },
            "abstention_accuracy": {
              "value": 70.78713968957871,
              "numerator": 1277.0,
              "denominator": 1804,
              "reviewed_or_scored": 1804,
              "unit": "percent",
              "status": "scored",
              "definition": "Correct answer/abstain decisions / responses with answerability ground truth × 100.",
              "confidence_interval": {
                "lower": 68.68070953436806,
                "upper": 72.83952328159646,
                "level": 0.95,
                "method": "percentile_bootstrap",
                "resamples": 1000,
                "seed": 42,
                "resampling_unit": "response",
                "limitation": "Responses sharing a source document may be correlated."
              }
            },
            "latency": {
              "total_seconds": {
                "mean": 40.422815544402006,
                "median": 35.124210399982985,
                "p95": 95.5538241849572,
                "count": 1804,
                "measurement_clusters": 1407,
                "mean_ci": {
                  "lower": 38.71160309804475,
                  "upper": 42.15197541248573,
                  "level": 0.95,
                  "method": "generation_batch_clustered_ratio_bootstrap",
                  "resamples": 1000,
                  "valid_resamples": 1000,
                  "seed": 42,
                  "resampling_unit": "generation_batch"
                }
              },
              "retrieval_seconds": {
                "mean": 0.0,
                "median": 0.0,
                "p95": 0.0,
                "count": 1804,
                "measurement_clusters": 1407,
                "mean_ci": {
                  "lower": 0.0,
                  "upper": 0.0,
                  "level": 0.95,
                  "method": "generation_batch_clustered_ratio_bootstrap",
                  "resamples": 1000,
                  "valid_resamples": 1000,
                  "seed": 42,
                  "resampling_unit": "generation_batch"
                }
              },
              "generation_seconds": {
                "mean": 40.41265889129794,
                "median": 35.11340090003796,
                "p95": 95.54373497506022,
                "count": 1804,
                "measurement_clusters": 1407,
                "mean_ci": {
                  "lower": 38.7014024335651,
                  "upper": 42.1418336644918,
                  "level": 0.95,
                  "method": "generation_batch_clustered_ratio_bootstrap",
                  "resamples": 1000,
                  "valid_resamples": 1000,
                  "seed": 42,
                  "resampling_unit": "generation_batch"
                }
              },
              "throughput": {
                "value": 0.7527403958257677,
                "numerator": 37941,
                "denominator": 50403.831401100964,
                "unit": "tokens/s",
                "confidence_interval": {
                  "lower": 0.715785273303579,
                  "upper": 0.7911422159597763,
                  "level": 0.95,
                  "method": "generation_batch_clustered_ratio_bootstrap",
                  "resamples": 1000,
                  "valid_resamples": 1000,
                  "seed": 42,
                  "resampling_unit": "generation_batch"
                },
                "definition": "Generated tokens / measured generation seconds; batch durations counted once; excludes loading and retrieval."
              }
            }
          }
        },
        "language_performance_gap": {
          "value": null,
          "unit": "percentage_points",
          "status": "pending",
          "languages": [],
          "definition": "Highest minus lowest validated language accuracy within the same source dataset.",
          "note": "This is a descriptive gap; different source datasets are never treated as parallel populations."
        }
      }
    },
    "definitions_version": "qa-metrics-v3-all-retrieval-queries",
    "human_metrics_policy": "pending until every eligible response in the scope is reviewed",
    "comparison_note": "English SQuAD and Hindi/Tamil IndicQA are separate populations.",
    "run_id": "fc7c6a02-bb45-4aed-8ecb-35b2611ddb07",
    "dataset_version": "acbff74f81c1a1d1",
    "track": "benchmark",
    "experiment": "B",
    "snapshot_reason": "paired_v3_replay_after_uninterrupted_full_benchmark",
    "computed_at": "2026-11-08T22:01:41.166371+00:00"
  }
}
```
