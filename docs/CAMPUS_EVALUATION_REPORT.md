# Campus evaluation report

Generated from the persisted experiment at 2026-11-08T23:11:53.275356+00:00.

Run ID: 54ab8518-0d9a-4a4d-9fbc-8270e3ff2ad3

Status: completed

Track: campus

Dataset version: 29ed6c44573105ff

Campus reference-review provenance is recorded in the run configuration. AI-curated references support pilot overlap/retrieval scores and remain pending independent human certification. Null factuality metrics mean insufficient human annotations, not zero error or zero accuracy. Confidence intervals and metric denominators are included with the calculated results. Failed-record exclusions remain explicit.

```json
{
  "run": {
    "run_id": "54ab8518-0d9a-4a4d-9fbc-8270e3ff2ad3",
    "track": "campus",
    "experiment": "D",
    "status": "completed",
    "dataset_version": "29ed6c44573105ff",
    "evaluation_fingerprint": "c9f4700e72eb8fbc98436d726a926c4dd7c6fc548a144cbfc160cb9636dae443",
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
        "measured_at": "2026-11-08T23:10:04.066037+00:00",
        "os": "Windows-10-10.0.26300-SP0",
        "cpu": "Intel64 Family 6 Model 141 Stepping 1, GenuineIntel",
        "physical_cores": 6,
        "logical_cores": 12,
        "ram_gib": 23.73,
        "available_ram_gib": 7.65,
        "project_disk_free_gib": 707.68,
        "python": "3.11.14",
        "python_executable": "D:\\shameek RAI\\.venv\\Scripts\\python.exe",
        "gpu": {
          "name": "NVIDIA GeForce RTX 2050",
          "total_vram_gib": 4.0,
          "free_vram_gib": 3.78,
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
      "ingestion": {
        "version": "6e044fab88609b53",
        "collection": "campus_faq_6e044fab88609b53",
        "corpus_version": "b07405a784a7045c",
        "chunks": 57,
        "faq_records": 57,
        "languages": {
          "en": 19,
          "hi": 19,
          "ta": 19
        },
        "reviewer_kinds": {
          "ai": 57
        },
        "configuration": {
          "embedding_model": "intfloat/multilingual-e5-small",
          "embedding_revision": "614241f622f53c4eeff9890bdc4f31cfecc418b3",
          "embedding_status": "validated",
          "candidate_models": [
            "intfloat/multilingual-e5-small",
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
          ],
          "candidate_revisions": {
            "intfloat/multilingual-e5-small": "614241f622f53c4eeff9890bdc4f31cfecc418b3",
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": "e8f8c211226b894fcb81acc59f3b34ba3efd5f42"
          },
          "collection": "campus_faq",
          "device": "cpu",
          "top_k": 4,
          "max_cosine_distance": 0.12740584881953368,
          "max_context_characters": 5500,
          "chunk_characters": 1000,
          "chunk_overlap": 150,
          "max_source_age_days": 180,
          "require_verified": true,
          "accepted_verification_statuses": [
            "human_verified",
            "source_verified"
          ],
          "validation_query_fingerprint": "10f0070d60c4d0f543e97eec99c2b2cedfcb809fc4dad9bc0fbffed27f35e845",
          "citation_policy": "model-or-verbatim-v2"
        },
        "created_at": "2026-11-08T22:59:12.625675+00:00",
        "content_fingerprint": "4c28d0b0e481e6613865022901b016194d5e262f7ae52aed92586c16a25cc86d"
      },
      "limit_per_language": null,
      "evidence_as_of": "2026-11-08T23:10:06.742528+00:00",
      "context_condition": "retrieved_verified_campus_evidence",
      "inference_execution": {
        "maximum_batch_size": 1,
        "batch_token_budget": 4096,
        "batching_policy": "language/input-length/stable-ID; no reference-answer selection"
      },
      "model_execution": {
        "attention_implementation": "explicit_gqa_sdpa",
        "quantization": "nf4",
        "double_quantization": true,
        "compute_dtype": "float16"
      },
      "runtime_memory_policy": {
        "version": "bounded-cuda-cache-v1",
        "per_process_memory_fraction": 0.75,
        "device": 0
      },
      "reference_annotation_policy": {
        "reviewer_kinds": {
          "ai": 45
        },
        "human_reference_review_complete": false,
        "response_factuality_metrics": "pending until actual human response annotations exist"
      },
      "test_ids_summary": {
        "count": 45,
        "sha256": "807199dc4aefce3dce20ba9007365fd5911bc7c9054b1df275560512ee7d1583",
        "location": "/api/experiments/54ab8518-0d9a-4a4d-9fbc-8270e3ff2ad3/export?format=json"
      }
    },
    "created_at": "2026-11-08T23:10:06.742528+00:00",
    "ended_at": "2026-11-08T23:11:53.271431+00:00",
    "total": 45,
    "completed": 45,
    "error": null
  },
  "metrics": {
    "status": "scored",
    "completed_predictions": 45,
    "excluded_failed_predictions": 0,
    "populations": {
      "SRM-KTR-source-reviewed-campus": {
        "languages": {
          "en": {
            "count": 15,
            "human_reviewed": 0,
            "accuracy": {
              "value": null,
              "numerator": 0,
              "denominator": 12,
              "reviewed_or_scored": 0,
              "unit": "percent",
              "status": "pending",
              "definition": "Human-validated correct answerable responses / all answerable responses × 100.",
              "confidence_interval": null
            },
            "exact_match": {
              "value": 80.0,
              "numerator": 12.0,
              "denominator": 15,
              "reviewed_or_scored": 15,
              "unit": "percent",
              "status": "scored",
              "definition": "Best normalized reference exact match; English articles removed only for English.",
              "confidence_interval": {
                "lower": 60.0,
                "upper": 100.0,
                "level": 0.95,
                "method": "percentile_bootstrap",
                "resamples": 1000,
                "seed": 42,
                "resampling_unit": "response",
                "limitation": "Responses sharing a source document may be correlated."
              }
            },
            "f1": {
              "value": 80.0,
              "numerator": 12.0,
              "denominator": 15,
              "reviewed_or_scored": 15,
              "unit": "percent",
              "status": "scored",
              "definition": "Best whitespace-token reference F1 × 100; Indic combining marks preserved.",
              "confidence_interval": {
                "lower": 60.0,
                "upper": 100.0,
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
              "denominator": 9,
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
              "value": 60.0,
              "numerator": 9.0,
              "denominator": 15,
              "reviewed_or_scored": 15,
              "unit": "percent",
              "status": "scored",
              "definition": "Queries retrieving a relevant document in top 4 / all retrieval queries × 100. Explicitly empty relevance lists contribute zero; missing labels leave the scope pending.",
              "confidence_interval": {
                "lower": 33.33333333333333,
                "upper": 86.66666666666667,
                "level": 0.95,
                "method": "percentile_bootstrap",
                "resamples": 1000,
                "seed": 42,
                "resampling_unit": "response",
                "limitation": "Responses sharing a source document may be correlated."
              }
            },
            "mrr": {
              "value": 0.6,
              "numerator": 9.0,
              "denominator": 15,
              "reviewed_or_scored": 15,
              "unit": "ratio",
              "status": "scored",
              "definition": "Mean reciprocal rank of the first relevant document in top 4, over all retrieval queries; empty relevance lists contribute zero.",
              "confidence_interval": {
                "lower": 0.3333333333333333,
                "upper": 0.8666666666666667,
                "level": 0.95,
                "method": "percentile_bootstrap",
                "resamples": 1000,
                "seed": 42,
                "resampling_unit": "response",
                "limitation": "Responses sharing a source document may be correlated."
              }
            },
            "abstention_accuracy": {
              "value": 80.0,
              "numerator": 12.0,
              "denominator": 15,
              "reviewed_or_scored": 15,
              "unit": "percent",
              "status": "scored",
              "definition": "Correct answer/abstain decisions / responses with answerability ground truth × 100.",
              "confidence_interval": {
                "lower": 60.0,
                "upper": 100.0,
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
                "mean": 0.4996639599946017,
                "median": 0.42448149994015694,
                "p95": 1.238756579940673,
                "count": 15,
                "measurement_clusters": 15,
                "mean_ci": {
                  "lower": 0.2717510390126457,
                  "upper": 0.7439074748310182,
                  "level": 0.95,
                  "method": "percentile_bootstrap",
                  "resamples": 1000,
                  "seed": 42,
                  "resampling_unit": "response",
                  "limitation": "Responses sharing a source document may be correlated."
                }
              },
              "retrieval_seconds": {
                "mean": 0.026300493340628842,
                "median": 0.023522899951785803,
                "p95": 0.03808400001144033,
                "count": 15,
                "measurement_clusters": 15,
                "mean_ci": {
                  "lower": 0.02319090450978062,
                  "upper": 0.03136131750109295,
                  "level": 0.95,
                  "method": "percentile_bootstrap",
                  "resamples": 1000,
                  "seed": 42,
                  "resampling_unit": "response",
                  "limitation": "Responses sharing a source document may be correlated."
                }
              },
              "generation_seconds": {
                "mean": 0.47014035332637527,
                "median": 0.3981093999464065,
                "p95": 1.2108210599632003,
                "count": 15,
                "measurement_clusters": 15,
                "mean_ci": {
                  "lower": 0.24424323799437844,
                  "upper": 0.7120952466768601,
                  "level": 0.95,
                  "method": "percentile_bootstrap",
                  "resamples": 1000,
                  "seed": 42,
                  "resampling_unit": "response",
                  "limitation": "Responses sharing a source document may be correlated."
                }
              },
              "throughput": {
                "value": 7.799089443660746,
                "numerator": 55,
                "denominator": 7.052105299895629,
                "unit": "tokens/s",
                "confidence_interval": {
                  "lower": 7.175814115476176,
                  "upper": 8.196475051066749,
                  "level": 0.95,
                  "method": "response_clustered_ratio_bootstrap",
                  "resamples": 1000,
                  "valid_resamples": 1000,
                  "seed": 42,
                  "resampling_unit": "response"
                },
                "definition": "Generated tokens / measured generation seconds; batch durations counted once; excludes loading and retrieval."
              }
            }
          },
          "hi": {
            "count": 15,
            "human_reviewed": 0,
            "accuracy": {
              "value": null,
              "numerator": 0,
              "denominator": 12,
              "reviewed_or_scored": 0,
              "unit": "percent",
              "status": "pending",
              "definition": "Human-validated correct answerable responses / all answerable responses × 100.",
              "confidence_interval": null
            },
            "exact_match": {
              "value": 40.0,
              "numerator": 6.0,
              "denominator": 15,
              "reviewed_or_scored": 15,
              "unit": "percent",
              "status": "scored",
              "definition": "Best normalized reference exact match; English articles removed only for English.",
              "confidence_interval": {
                "lower": 13.333333333333334,
                "upper": 66.66666666666666,
                "level": 0.95,
                "method": "percentile_bootstrap",
                "resamples": 1000,
                "seed": 42,
                "resampling_unit": "response",
                "limitation": "Responses sharing a source document may be correlated."
              }
            },
            "f1": {
              "value": 40.0,
              "numerator": 6.0,
              "denominator": 15,
              "reviewed_or_scored": 15,
              "unit": "percent",
              "status": "scored",
              "definition": "Best whitespace-token reference F1 × 100; Indic combining marks preserved.",
              "confidence_interval": {
                "lower": 13.333333333333334,
                "upper": 66.66666666666666,
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
              "denominator": 5,
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
              "value": 80.0,
              "numerator": 12.0,
              "denominator": 15,
              "reviewed_or_scored": 15,
              "unit": "percent",
              "status": "scored",
              "definition": "Queries retrieving a relevant document in top 4 / all retrieval queries × 100. Explicitly empty relevance lists contribute zero; missing labels leave the scope pending.",
              "confidence_interval": {
                "lower": 59.83333333333334,
                "upper": 100.0,
                "level": 0.95,
                "method": "percentile_bootstrap",
                "resamples": 1000,
                "seed": 42,
                "resampling_unit": "response",
                "limitation": "Responses sharing a source document may be correlated."
              }
            },
            "mrr": {
              "value": 0.8,
              "numerator": 12.0,
              "denominator": 15,
              "reviewed_or_scored": 15,
              "unit": "ratio",
              "status": "scored",
              "definition": "Mean reciprocal rank of the first relevant document in top 4, over all retrieval queries; empty relevance lists contribute zero.",
              "confidence_interval": {
                "lower": 0.5983333333333334,
                "upper": 1.0,
                "level": 0.95,
                "method": "percentile_bootstrap",
                "resamples": 1000,
                "seed": 42,
                "resampling_unit": "response",
                "limitation": "Responses sharing a source document may be correlated."
              }
            },
            "abstention_accuracy": {
              "value": 40.0,
              "numerator": 6.0,
              "denominator": 15,
              "reviewed_or_scored": 15,
              "unit": "percent",
              "status": "scored",
              "definition": "Correct answer/abstain decisions / responses with answerability ground truth × 100.",
              "confidence_interval": {
                "lower": 13.333333333333334,
                "upper": 66.66666666666666,
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
                "mean": 2.042476186652978,
                "median": 1.752456699963659,
                "p95": 4.5119505700538864,
                "count": 15,
                "measurement_clusters": 15,
                "mean_ci": {
                  "lower": 1.4124542764828463,
                  "upper": 2.6927784949903915,
                  "level": 0.95,
                  "method": "percentile_bootstrap",
                  "resamples": 1000,
                  "seed": 42,
                  "resampling_unit": "response",
                  "limitation": "Responses sharing a source document may be correlated."
                }
              },
              "retrieval_seconds": {
                "mean": 0.025229426667404672,
                "median": 0.024968400015495718,
                "p95": 0.02812593999551609,
                "count": 15,
                "measurement_clusters": 15,
                "mean_ci": {
                  "lower": 0.024440829496791897,
                  "upper": 0.026131713500556847,
                  "level": 0.95,
                  "method": "percentile_bootstrap",
                  "resamples": 1000,
                  "seed": 42,
                  "resampling_unit": "response",
                  "limitation": "Responses sharing a source document may be correlated."
                }
              },
              "generation_seconds": {
                "mean": 2.0131191533446935,
                "median": 1.7217780000064522,
                "p95": 4.482190940063447,
                "count": 15,
                "measurement_clusters": 15,
                "mean_ci": {
                  "lower": 1.3835412716694797,
                  "upper": 2.6633766150146645,
                  "level": 0.95,
                  "method": "percentile_bootstrap",
                  "resamples": 1000,
                  "seed": 42,
                  "resampling_unit": "response",
                  "limitation": "Responses sharing a source document may be correlated."
                }
              },
              "throughput": {
                "value": 7.815400944943182,
                "numerator": 236,
                "denominator": 30.1967873001704,
                "unit": "tokens/s",
                "confidence_interval": {
                  "lower": 7.229780868808152,
                  "upper": 8.167153510153655,
                  "level": 0.95,
                  "method": "response_clustered_ratio_bootstrap",
                  "resamples": 1000,
                  "valid_resamples": 1000,
                  "seed": 42,
                  "resampling_unit": "response"
                },
                "definition": "Generated tokens / measured generation seconds; batch durations counted once; excludes loading and retrieval."
              }
            }
          },
          "ta": {
            "count": 15,
            "human_reviewed": 0,
            "accuracy": {
              "value": null,
              "numerator": 0,
              "denominator": 12,
              "reviewed_or_scored": 0,
              "unit": "percent",
              "status": "pending",
              "definition": "Human-validated correct answerable responses / all answerable responses × 100.",
              "confidence_interval": null
            },
            "exact_match": {
              "value": 53.333333333333336,
              "numerator": 8.0,
              "denominator": 15,
              "reviewed_or_scored": 15,
              "unit": "percent",
              "status": "scored",
              "definition": "Best normalized reference exact match; English articles removed only for English.",
              "confidence_interval": {
                "lower": 26.666666666666668,
                "upper": 80.0,
                "level": 0.95,
                "method": "percentile_bootstrap",
                "resamples": 1000,
                "seed": 42,
                "resampling_unit": "response",
                "limitation": "Responses sharing a source document may be correlated."
              }
            },
            "f1": {
              "value": 53.333333333333336,
              "numerator": 8.0,
              "denominator": 15,
              "reviewed_or_scored": 15,
              "unit": "percent",
              "status": "scored",
              "definition": "Best whitespace-token reference F1 × 100; Indic combining marks preserved.",
              "confidence_interval": {
                "lower": 26.666666666666668,
                "upper": 80.0,
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
              "denominator": 10,
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
              "value": 80.0,
              "numerator": 12.0,
              "denominator": 15,
              "reviewed_or_scored": 15,
              "unit": "percent",
              "status": "scored",
              "definition": "Queries retrieving a relevant document in top 4 / all retrieval queries × 100. Explicitly empty relevance lists contribute zero; missing labels leave the scope pending.",
              "confidence_interval": {
                "lower": 59.83333333333334,
                "upper": 100.0,
                "level": 0.95,
                "method": "percentile_bootstrap",
                "resamples": 1000,
                "seed": 42,
                "resampling_unit": "response",
                "limitation": "Responses sharing a source document may be correlated."
              }
            },
            "mrr": {
              "value": 0.8,
              "numerator": 12.0,
              "denominator": 15,
              "reviewed_or_scored": 15,
              "unit": "ratio",
              "status": "scored",
              "definition": "Mean reciprocal rank of the first relevant document in top 4, over all retrieval queries; empty relevance lists contribute zero.",
              "confidence_interval": {
                "lower": 0.5983333333333334,
                "upper": 1.0,
                "level": 0.95,
                "method": "percentile_bootstrap",
                "resamples": 1000,
                "seed": 42,
                "resampling_unit": "response",
                "limitation": "Responses sharing a source document may be correlated."
              }
            },
            "abstention_accuracy": {
              "value": 73.33333333333333,
              "numerator": 11.0,
              "denominator": 15,
              "reviewed_or_scored": 15,
              "unit": "percent",
              "status": "scored",
              "definition": "Correct answer/abstain decisions / responses with answerability ground truth × 100.",
              "confidence_interval": {
                "lower": 53.16666666666668,
                "upper": 93.33333333333333,
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
                "mean": 3.273231780009034,
                "median": 3.011012400034815,
                "p95": 7.093607850011898,
                "count": 15,
                "measurement_clusters": 15,
                "mean_ci": {
                  "lower": 2.300862990168777,
                  "upper": 4.6051965908424854,
                  "level": 0.95,
                  "method": "percentile_bootstrap",
                  "resamples": 1000,
                  "seed": 42,
                  "resampling_unit": "response",
                  "limitation": "Responses sharing a source document may be correlated."
                }
              },
              "retrieval_seconds": {
                "mean": 0.02487260001556327,
                "median": 0.024885499966330826,
                "p95": 0.02773704003775492,
                "count": 15,
                "measurement_clusters": 15,
                "mean_ci": {
                  "lower": 0.023982060336275028,
                  "upper": 0.025749993354741794,
                  "level": 0.95,
                  "method": "percentile_bootstrap",
                  "resamples": 1000,
                  "seed": 42,
                  "resampling_unit": "response",
                  "limitation": "Responses sharing a source document may be correlated."
                }
              },
              "generation_seconds": {
                "mean": 3.244095726652692,
                "median": 2.982842899975367,
                "p95": 7.068141580023797,
                "count": 15,
                "measurement_clusters": 15,
                "mean_ci": {
                  "lower": 2.2714268899862264,
                  "upper": 4.577278346815341,
                  "level": 0.95,
                  "method": "percentile_bootstrap",
                  "resamples": 1000,
                  "seed": 42,
                  "resampling_unit": "response",
                  "limitation": "Responses sharing a source document may be correlated."
                }
              },
              "throughput": {
                "value": 8.137860970964605,
                "numerator": 396,
                "denominator": 48.661435899790376,
                "unit": "tokens/s",
                "confidence_interval": {
                  "lower": 7.609497330171197,
                  "upper": 8.491930976853602,
                  "level": 0.95,
                  "method": "response_clustered_ratio_bootstrap",
                  "resamples": 1000,
                  "valid_resamples": 1000,
                  "seed": 42,
                  "resampling_unit": "response"
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
    "run_id": "54ab8518-0d9a-4a4d-9fbc-8270e3ff2ad3",
    "dataset_version": "29ed6c44573105ff",
    "track": "campus",
    "experiment": "D",
    "computed_at": "2026-11-08T23:11:53.264092+00:00"
  }
}
```
