# College FAQ dataset report

Generated from sealed records: 2026-11-08T23:08:26.502247+00:00.

**This is an AI-curated, official-source-backed Kattankulathur pilot. Independent human source, translation and reference certification remains pending.** Source review does not create human response annotations.

Corpus version: `b07405a784a7045c`. Records: **57** from **19** official source pages. Eligible source-reviewed records: 57; human-verified records: 0.

| Language | FAQ records | Retrieval validation queries | Campus test queries | Test answerable / unanswerable |
|---|---:|---:|---:|---:|
| en | 19 | 8 | 15 | 12 / 3 |
| hi | 19 | 8 | 15 | 12 / 3 |
| ta | 19 | 8 | 15 | 12 / 3 |

## Source scope and review

21 public official university/department pages were captured after the full benchmark A, training and B workflow completed. 19 pages supply this corpus. The initial discovery registry is preserved. Each capture keeps original HTML, normalized text, a SHA-256 document version, URL and capture timestamp. FAQ validation checks the exact evidence quotation against that archived text.

Campus scope was checked against the Kattankulathur main-site hierarchy, department addresses and KTR hostel references. Additional official search results corroborated the aquatic complex, temple and astronomy-club identities. The facts are representations of official published pages, rather than an on-site audit.

English questions/answers were authored from those facts. Hindi and Tamil versions were checked by the named AI reviewer for entity identity, scope and meaning, and use `machine_translation_ai_reviewed`. All records retain `reviewer_kind: ai`, `human_review_status: pending` and `verification_status: source_verified`. They are not human-verified records.

No current fees, fines, admissions deadlines, changing headcounts, personal student records or dynamic zero-valued homepage counters are included in the FAQ corpus. Some source pages contain historical information; a recent capture does not independently establish that every policy on the website is current. Student contact details are not curated or indexed. Raw page archives remain local and are excluded from the source-only distribution.

| Topic ID | Query split | Official source | Document version prefix |
|---|---|---|---|
| ktr-library-rfid | validation | [Library — SRMIST](https://www.srmist.edu.in/library/) | `aa051c3d41af32d5` |
| ktr-transport-booking | knowledge only (primary-study fact) | [Transport Facility — SRMIST](https://www.srmist.edu.in/transport-facility/) | `05d1ba9b15526a9f` |
| ktr-facilities-division | validation | [Facilities and Operations — SRMIST](https://www.srmist.edu.in/life-at-srm/facilities-and-operations/) | `8cffc6f00045ae65` |
| ktr-sports-aquatic | knowledge only (primary-study fact) | [Sports — SRMIST](https://www.srmist.edu.in/sports/) | `6050888a6ec198d5` |
| ktr-astronomy-club | knowledge only (primary-study fact) | [Clubs — SRMIST](https://www.srmist.edu.in/life-at-srm/student-life/clubs/) | `7ed6c14c4901d5c7` |
| ktr-annsh-school | knowledge only (primary-study fact) | [Community Centers — SRMIST](https://www.srmist.edu.in/life-at-srm/student-life/community-centers/) | `fb303f09176e7781` |
| ktr-vinayagar-temple | validation | [Religious Life — SRMIST](https://www.srmist.edu.in/life-at-srm/student-life/religious-life/) | `84f00409e4871742` |
| ktr-hostel-directorate | knowledge only (primary-study fact) | [SRM Hostels — SRMIST](https://www.srmist.edu.in/srm-hostels/) | `efb344c164c97b96` |
| ktr-kopperundevi-name | knowledge only (primary-study fact) | [Hostel for Women — SRMIST](https://www.srmist.edu.in/srm-hostels/hostel-for-women/) | `94895dcde3c32317` |
| ktr-oori-ac | validation | [Hostel for Men — SRMIST](https://www.srmist.edu.in/srm-hostels/hostel-for-men/) | `0226617da422dc30` |
| ktr-green-pearl | knowledge only (primary-study fact) | [International Hostel — SRMIST](https://www.srmist.edu.in/srm-hostels/international-hostel/) | `2d69cffc6938417a` |
| ktr-dining-station | knowledge only (primary-study fact) | [Dining and Eateries — SRMIST](https://www.srmist.edu.in/srm-hostels/dining-eateries/) | `320c1a26f260af72` |
| ktr-student-affairs | knowledge only (primary-study fact) | [Student Life — SRMIST](https://www.srmist.edu.in/life-at-srm/student-life/) | `f0d141dc0270a95c` |
| ktr-dental-ebsco | test | [Dental Library — SRM Kattankulathur Dental College](https://dental.srmist.edu.in/dental-library/) | `694354efd93d7eac` |
| ktr-dental-pierre-hostel | test | [Dental Hostels — SRM Kattankulathur Dental College](https://dental.srmist.edu.in/hostels/) | `be2951ddc033451e` |
| ktr-mobile-powered-chairs | test | [Mobile Clinic — SRM Kattankulathur Dental College](https://dental.srmist.edu.in/mobile-clinic/) | `a944893185eb0a9d` |
| ktr-stratus-centre | test | [Simulation Center — SRM Kattankulathur Dental College](https://dental.srmist.edu.in/simulation-center/) | `9122ad0e5ce2617f` |
| ktr-medical-cafe | test | [Cafeteria — SRM Medical College Kattankulathur](https://medical.srmist.edu.in/cafeteria/) | `35b7909d2e25283e` |
| ktr-medical-clinicalkey | test | [Medical College Central Library — SRMIST Kattankulathur](https://medical.srmist.edu.in/srm-medical-college-hospital-research-centre-central-library/) | `25a81b67ca9adb8b` |

## Query design and sealing

The **24** retrieval-validation queries cover 4 source documents. The **45** held-out campus questions cover 6 different source documents plus explicitly out-of-corpus future/personal requests. Validation and test source groups are disjoint. Every question explicitly identifies the Kattankulathur campus, identically for all four conditions.

All FAQ facts are intentionally present in the knowledge index. The split holds out retrieval-query facts from embedding selection; it is evaluation over a fixed knowledge corpus, not a claim about retrieval from unseen corpora. Each answerable fact has two question variants per language. Those variants are correlated and do not establish independent evidence of broad generalization.

Test version: `29ed6c44573105ff`; checksum: `41a79c24acc3de44cbd749c4fcf5bb83cc69db1320d31b82501c6cfcc06f680d`. The test was sealed at 2026-11-08T22:58:59.199377+00:00. The embedding and threshold choices were fixed on primary validation at 2026-11-08T22:20:51.700061+00:00. Reference aliases and answerability labels were fixed before inference on this test version. Three negatives per language ask about unspecified future fees, future examination dates or personal room allocation; these are clear out-of-corpus cases, not a comprehensive robustness test.

The corpus, retrieval labels and references disclose AI curation. EM, F1 and retrieval scores are conditional on those annotations. Human accuracy, hallucination incidence, unsupported-claim rate and the corresponding accuracy gap remain pending until actual human response reviews exist.

## Storage and training separation

Versioned FAQ data: `data/college_faq/versions/b07405a784a7045c/faq.jsonl`. Versioned test: `data/college_faq/test_versions/29ed6c44573105ff/test.jsonl`. The curation source and review manifest preserve translations, aliases, source assignments and provenance. The approved LoRA adapter was trained before campus collection, exclusively on benchmark training data; no campus FAQ was added to supervised fine-tuning.

University pages retain their own copyright. Facts are paraphrased, brief evidence excerpts are attributed, and public availability is not represented as an open-content licence.

## Follow-up provenance

This corpus retains the original 39 FAQs and adds 18 reviewed language records from six new department pages. The primary study's 63-question test and all four results remain intact. Its strict citation policy rejected uncited model answers. A separately documented engineering extension attributes only complete verbatim source matches; the new 45-question test uses source documents absent from the entire original FAQ corpus. Its questions, references and source assignments were sealed before follow-up inference. Embedding model, threshold, training, model prompts and generation settings were retained. Compare arms within a test version; primary/follow-up percentages are not a paired causal estimate. See [CITATION_POLICY_AMENDMENT.md](CITATION_POLICY_AMENDMENT.md).
