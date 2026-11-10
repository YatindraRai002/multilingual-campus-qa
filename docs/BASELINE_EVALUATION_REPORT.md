# Original model baseline report

Generated from the persisted experiment at 2026-11-08T22:01:34.211718+00:00.

Run ID: 013018a0-f42d-418d-8de8-922d7ca8e728

Status: completed

Track: benchmark

Dataset version: acbff74f81c1a1d1

English SQuAD and Hindi/Tamil IndicQA are separate populations. Null factuality metrics mean insufficient human annotations, not zero error or zero accuracy. Confidence intervals and metric denominators are included with the calculated results. Failed-record exclusions remain explicit.

```json
{
  "run": {
    "run_id": "013018a0-f42d-418d-8de8-922d7ca8e728",
    "track": "benchmark",
    "experiment": "A",
    "status": "completed",
    "dataset_version": "acbff74f81c1a1d1",
    "evaluation_fingerprint": "d151264a4bd8987e21f2a1fe2b411e4bfcbb280760a33b5d9c74340ee5ae8683",
    "configuration": {
      "model_id": "Qwen/Qwen2.5-1.5B-Instruct",
      "model_revision": "989aa7980e4cf806f80c7fef2b1adb7bc71aa306",
      "adapter": null,
      "prompt_version": "grounded-qa-v1",
      "generation": {
        "max_new_tokens": 192,
        "do_sample": false,
        "repetition_penalty": 1.0
      },
      "max_input_tokens": 9216,
      "seed": 42,
      "hardware": {
        "measured_at": "2026-11-07T17:59:36.025859+00:00",
        "os": "Windows-10-10.0.26300-SP0",
        "cpu": "Intel64 Family 6 Model 141 Stepping 1, GenuineIntel",
        "physical_cores": 6,
        "logical_cores": 12,
        "ram_gib": 23.73,
        "available_ram_gib": 7.69,
        "project_disk_free_gib": 711.03,
        "python": "3.11.14",
        "python_executable": "D:\\shameek RAI\\.venv\\Scripts\\python.exe",
        "gpu": {
          "name": "NVIDIA GeForce RTX 2050",
          "total_vram_gib": 4.0,
          "free_vram_gib": 3.53,
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
      "evidence_as_of": "2026-11-07T17:59:38.980031+00:00",
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
        "location": "/api/experiments/013018a0-f42d-418d-8de8-922d7ca8e728/export?format=json"
      }
    },
    "created_at": "2026-11-07T17:59:39.171392+00:00",
    "ended_at": "2026-11-07T23:51:33.202152+00:00",
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
              "value": 38.78902554399243,
              "numerator": 4100.0,
              "denominator": 10570,
              "reviewed_or_scored": 10570,
              "unit": "percent",
              "status": "scored",
              "definition": "Best normalized reference exact match; English articles removed only for English.",
              "confidence_interval": {
                "lower": 37.83349101229896,
                "upper": 39.744560075685904,
                "level": 0.95,
                "method": "percentile_bootstrap",
                "resamples": 1000,
                "seed": 42,
                "resampling_unit": "response",
                "limitation": "Responses sharing a source document may be correlated."
              }
            },
            "f1": {
              "value": 62.76950889473167,
              "numerator": 6634.737090173138,
              "denominator": 10570,
              "reviewed_or_scored": 10570,
              "unit": "percent",
              "status": "scored",
              "definition": "Best whitespace-token reference F1 × 100; Indic combining marks preserved.",
              "confidence_interval": {
                "lower": 62.035609779227975,
                "upper": 63.45729767257144,
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
              "denominator": 10567,
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
              "value": 99.97161778618732,
              "numerator": 10567.0,
              "denominator": 10570,
              "reviewed_or_scored": 10570,
              "unit": "percent",
              "status": "scored",
              "definition": "Correct answer/abstain decisions / responses with answerability ground truth × 100.",
              "confidence_interval": {
                "lower": 99.93377483443709,
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
                "mean": 2.4042300041630718,
                "median": 2.1315700000268407,
                "p95": 4.638136800029315,
                "count": 10570,
                "measurement_clusters": 2643,
                "mean_ci": {
                  "lower": 2.357019798367171,
                  "upper": 2.4565870335448805,
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
                "mean": 2.392594444294735,
                "median": 2.1203170000226237,
                "p95": 4.627603300032206,
                "count": 10570,
                "measurement_clusters": 2643,
                "mean_ci": {
                  "lower": 2.3454173377357206,
                  "upper": 2.4449276354100866,
                  "level": 0.95,
                  "method": "generation_batch_clustered_ratio_bootstrap",
                  "resamples": 1000,
                  "valid_resamples": 1000,
                  "seed": 42,
                  "resampling_unit": "generation_batch"
                }
              },
              "throughput": {
                "value": 22.026756363343086,
                "numerator": 139282,
                "denominator": 6323.309601398825,
                "unit": "tokens/s",
                "confidence_interval": {
                  "lower": 21.7695677199284,
                  "upper": 22.272775570308728,
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
              "value": 16.7420814479638,
              "numerator": 259.0,
              "denominator": 1547,
              "reviewed_or_scored": 1547,
              "unit": "percent",
              "status": "scored",
              "definition": "Best normalized reference exact match; English articles removed only for English.",
              "confidence_interval": {
                "lower": 14.802844214608921,
                "upper": 18.74595992243051,
                "level": 0.95,
                "method": "percentile_bootstrap",
                "resamples": 1000,
                "seed": 42,
                "resampling_unit": "response",
                "limitation": "Responses sharing a source document may be correlated."
              }
            },
            "f1": {
              "value": 27.561146698815257,
              "numerator": 426.370939430672,
              "denominator": 1547,
              "reviewed_or_scored": 1547,
              "unit": "percent",
              "status": "scored",
              "definition": "Best whitespace-token reference F1 × 100; Indic combining marks preserved.",
              "confidence_interval": {
                "lower": 25.68246338329494,
                "upper": 29.557831616737595,
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
              "denominator": 1547,
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
              "value": 68.00258564964447,
              "numerator": 1052.0,
              "denominator": 1547,
              "reviewed_or_scored": 1547,
              "unit": "percent",
              "status": "scored",
              "definition": "Correct answer/abstain decisions / responses with answerability ground truth × 100.",
              "confidence_interval": {
                "lower": 65.48157724628312,
                "upper": 70.458952811894,
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
                "mean": 5.26483156354322,
                "median": 4.546277599991299,
                "p95": 12.508646049990784,
                "count": 1547,
                "measurement_clusters": 1158,
                "mean_ci": {
                  "lower": 5.015832188832153,
                  "upper": 5.50638235796621,
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
                "mean": 5.254196868907421,
                "median": 4.532339200028218,
                "p95": 12.501589670014798,
                "count": 1547,
                "measurement_clusters": 1158,
                "mean_ci": {
                  "lower": 5.005315971356819,
                  "upper": 5.495784234071791,
                  "level": 0.95,
                  "method": "generation_batch_clustered_ratio_bootstrap",
                  "resamples": 1000,
                  "valid_resamples": 1000,
                  "seed": 42,
                  "resampling_unit": "generation_batch"
                }
              },
              "throughput": {
                "value": 7.925779295122301,
                "numerator": 45674,
                "denominator": 5762.714087699715,
                "unit": "tokens/s",
                "confidence_interval": {
                  "lower": 7.598516634904259,
                  "upper": 8.250438105175585,
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
              "value": 5.099778270509978,
              "numerator": 92.0,
              "denominator": 1804,
              "reviewed_or_scored": 1804,
              "unit": "percent",
              "status": "scored",
              "definition": "Best normalized reference exact match; English articles removed only for English.",
              "confidence_interval": {
                "lower": 4.1019955654102,
                "upper": 6.154379157427937,
                "level": 0.95,
                "method": "percentile_bootstrap",
                "resamples": 1000,
                "seed": 42,
                "resampling_unit": "response",
                "limitation": "Responses sharing a source document may be correlated."
              }
            },
            "f1": {
              "value": 13.195445749082902,
              "numerator": 238.04584131345555,
              "denominator": 1804,
              "reviewed_or_scored": 1804,
              "unit": "percent",
              "status": "scored",
              "definition": "Best whitespace-token reference F1 × 100; Indic combining marks preserved.",
              "confidence_interval": {
                "lower": 11.851014303304298,
                "upper": 14.557595804551696,
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
              "denominator": 1803,
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
              "value": 70.84257206208426,
              "numerator": 1278.0,
              "denominator": 1804,
              "reviewed_or_scored": 1804,
              "unit": "percent",
              "status": "scored",
              "definition": "Correct answer/abstain decisions / responses with answerability ground truth × 100.",
              "confidence_interval": {
                "lower": 68.79018847006651,
                "upper": 72.9490022172949,
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
                "mean": 6.844855214079621,
                "median": 5.813191349996487,
                "p95": 17.79341420001583,
                "count": 1804,
                "measurement_clusters": 1407,
                "mean_ci": {
                  "lower": 6.52722721462688,
                  "upper": 7.114493298452813,
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
                "mean": 6.834515070066126,
                "median": 5.803613249998307,
                "p95": 17.782011099974625,
                "count": 1804,
                "measurement_clusters": 1407,
                "mean_ci": {
                  "lower": 6.517077906363971,
                  "upper": 7.104067514755234,
                  "level": 0.95,
                  "method": "generation_batch_clustered_ratio_bootstrap",
                  "resamples": 1000,
                  "valid_resamples": 1000,
                  "seed": 42,
                  "resampling_unit": "generation_batch"
                }
              },
              "throughput": {
                "value": 9.618859961834243,
                "numerator": 84926,
                "denominator": 8829.112840499787,
                "unit": "tokens/s",
                "confidence_interval": {
                  "lower": 9.37104349011528,
                  "upper": 9.883040205917762,
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
    "run_id": "013018a0-f42d-418d-8de8-922d7ca8e728",
    "dataset_version": "acbff74f81c1a1d1",
    "track": "benchmark",
    "experiment": "A",
    "snapshot_reason": "paired_v3_replay_after_uninterrupted_full_benchmark",
    "computed_at": "2026-11-08T22:01:34.203215+00:00"
  }
}
```
