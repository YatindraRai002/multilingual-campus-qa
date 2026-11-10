# Supplemental training dataset report

The user explicitly approved adding L3Cube IndicSQuAD as a training-only extension on 7 November 2026. IndicQA remains the untouched evaluation source. Published IndicSQuAD validation/test files are not used. Only original training records mapping by preserved IDs to SQuAD v1.1 original training are eligible. The original full Hindi/Tamil training files are preserved. Selection is capped at 10,000 eligible records per language by a fixed hash of source ID and seed 42, to bound local preprocessing memory and the planned training workload. This cap does not reduce 7B VRAM requirements. Matched translated questions and English source documents are grouped before train/validation splitting. No parallel relationship to IndicQA test questions is asserted.

The publisher declares CC BY 4.0; original SQuAD attribution/share-alike obligations are also retained. Translations are publisher-generated and have not been independently human-verified by this project. Question/context scripts and normalized answer presence are checked. Unknown original IDs, empty translations and mismatches are excluded with actual counts.

```json
{
  "selection": {
    "dataset_id": "l3cube-pune/indic-squad",
    "revision": "f5973900b6c0e3caf6a1698b49a3309bad3ae849",
    "approved_extension": true,
    "configuration": {
      "enabled": true,
      "user_approved": true,
      "dataset_id": "l3cube-pune/indic-squad",
      "revision": "f5973900b6c0e3caf6a1698b49a3309bad3ae849",
      "maximum_records_per_language": 10000,
      "seed": 42,
      "selection": "stable_hash_of_original_id_after_mapping_to_squad_v1_original_train"
    },
    "languages": {
      "hi": {
        "original_training_rows": 118516,
        "excluded_unmapped_original_training_id": 39633,
        "eligible_mapped_training_rows": 78026,
        "excluded_empty_or_unanswerable_translation": 849,
        "excluded_answer_not_in_context": 8,
        "selected_before_group_split": 10000,
        "eligible_not_selected_by_budget": 68026
      },
      "ta": {
        "original_training_rows": 118516,
        "excluded_unmapped_original_training_id": 39633,
        "eligible_mapped_training_rows": 77975,
        "excluded_empty_or_unanswerable_translation": 879,
        "excluded_answer_not_in_context": 29,
        "selected_before_group_split": 10000,
        "eligible_not_selected_by_budget": 67975
      }
    },
    "selection_uses_test_answers": false,
    "english_mapping": "original training ID only; no IndicQA English parallel mapping is asserted",
    "published_validation_and_test_files_used": false
  },
  "processed_splits": {
    "train": {
      "total": 96341,
      "languages": {
        "en": 78437,
        "hi": 8954,
        "ta": 8950
      },
      "sources": {
        "SQuAD-v1.1": 78437,
        "l3cube-pune/indic-squad": 17904
      },
      "answerability": {
        "en": {
          "answerable": 78437
        },
        "hi": {
          "answerable": 8954
        },
        "ta": {
          "answerable": 8950
        }
      }
    },
    "validation": {
      "total": 11052,
      "languages": {
        "en": 8961,
        "hi": 1044,
        "ta": 1047
      },
      "sources": {
        "SQuAD-v1.1": 8961,
        "l3cube-pune/indic-squad": 2091
      },
      "answerability": {
        "en": {
          "answerable": 8961
        },
        "hi": {
          "answerable": 1044
        },
        "ta": {
          "answerable": 1047
        }
      }
    },
    "test": {
      "total": 13921,
      "languages": {
        "hi": 1547,
        "ta": 1804,
        "en": 10570
      },
      "sources": {
        "ai4bharat/IndicQA": 3351,
        "SQuAD-v1.1": 10570
      },
      "answerability": {
        "en": {
          "answerable": 10570
        },
        "hi": {
          "unanswerable": 495,
          "answerable": 1052
        },
        "ta": {
          "answerable": 1277,
          "unanswerable": 527
        }
      }
    }
  },
  "version": "acbff74f81c1a1d1"
}
```

The approved local 1.5B study further selects a reproducible equal-language budget of up to 256 usable base examples per language after token-length filtering, with up to 32 validation examples per language. Source populations are imbalanced; selected and augmented exposure counts are logged separately during actual training. Source preparation counts are not completed training exposure.
