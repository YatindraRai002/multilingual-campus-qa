# Benchmark dataset report

Sources were inspected on 7 November 2026. The acquisition manifest and generated preprocessing report contain the exact downloaded bytes, SHA-256 checksums and immutable dataset version.

## Official source structure

AI4Bharat IndicQA configurations: `indicqa.as`, `indicqa.bn`, `indicqa.gu`, `indicqa.hi`, `indicqa.kn`, `indicqa.ml`, `indicqa.mr`, `indicqa.or`, `indicqa.pa`, `indicqa.ta`, `indicqa.te`. The loader exposes test only. Hindi and Tamil are acquired directly as JSON to avoid executing remote dataset-loader code and to avoid downloading all languages. The JSON hierarchy is articles → paragraphs → context + question/answers. Original question IDs, category, answer text and answer offsets remain in raw downloads. The card marks its records original; it does not establish an English translation mapping.

SQuAD uses the same article/paragraph layout. Official train and development downloads are preserved separately. This project labels official development as held-out evaluation/test, and records the source split explicitly in provenance. English training documents are partitioned into train/validation with seed 42 after connected-context/question grouping.

## Actual observations

| Population | Raw/evaluation questions | Answerable | Unanswerable |
|---|---:|---:|---:|
| IndicQA Hindi test | 1,547 | 1,052 | 495 |
| IndicQA Tamil test | 1,804 | 1,277 | 527 |
| SQuAD English dev, held out as test | 10,570 | 10,570 | 0 |

The combined evaluation manifest contains 13,921 records. These are stored together for orchestration but are **not** combined into one directly comparable accuracy score. The final prepared version is `acbff74f81c1a1d1`: English training/validation contain 78,437 / 8,961 records, Hindi contain 8,954 / 1,044 and Tamil contain 8,950 / 1,047. Hindi/Tamil training comes from the separately approved IndicSQuAD training extension. The normalized totals are 96,341 train and 11,052 validation. The complete original supplemental files contain 118,516 records per language; a fixed mapped-ID selection caps each at 10,000 before grouping and final deduplication/overlap checks. See the supplemental report for every exclusion count.

The `NO` category with empty answer text is interpreted as explicit unanswerability; those 1,022 questions are not malformed answers. The original test contains 1,949 span-offset mismatches, 29 normalized answer/context mismatches and 39 duplicate context/question/language pairs. These are retained and flagged. Reference-text EM/F1 does not depend on the original offsets. Duplicate test questions and repeated source articles can affect uncertainty estimates and must be discussed in publications.

The two selected IndicQA JSON files total about 5.4 MB decimal. SQuAD train/dev add tens of MB; normalized records with explicit provenance are larger. Acquisition writes actual byte counts, not estimates, to `data/benchmark/acquisition.json`.

## Limitations

This component is extractive and does not cover the full paper's abstractive collection. Unknown English correspondence to IndicQA is not inferred from row order or numeric identifiers. Source-quality warnings are transparent; there is no manually repaired test ground truth. The user approved L3Cube IndicSQuAD for supplemental Hindi/Tamil training; that mapped translation relationship applies to original SQuAD training IDs, not IndicQA evaluation. Content licenses must be honored independently of code licensing.
