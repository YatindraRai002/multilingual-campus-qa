# Frozen citation-policy follow-up

The original campus study is preserved as a negative result. In the 63-question test, original-model RAG C and LoRA RAG D both abstained on all questions. C rejected 51 and D rejected 50 model responses for missing/invalid source labels, despite some raw responses containing the relevant entity. Twelve per arm had insufficient retrieved evidence; D also had one model abstention. The model received the citation instruction correctly. Original predictions, raw text and metric snapshots were not rewritten.

## Extension and freeze

The separate follow-up was frozen before any inference on its 45 new test questions. Its protocol is `results/citation-policy-followup/sealed_protocol.json`, SHA-256 `57829556ce330d64253b3d3dcabdad2820234fbc3585d9c84af945b582a4cecd`. It records the original metric digests, new corpus/test/index versions, configuration and code hashes. `results/final-model-validation.json` verifies that those hashes and original metric snapshots remain unchanged.

The new `model-or-verbatim-v2` policy retains model-emitted source citations. Only when the model omits a label, the entire normalized answer may match the entire FAQ answer or evidence quotation from exactly one source document actually supplied in context. Normalization permits NFC, case folding, whitespace collapse and terminal periods/dandas. Internal punctuation, signs, symbols and Indic combining marks remain significant. Ambiguous matches, partial matches, novel text and unknown model labels still cause abstention.

This rule never reads reference answers, test aliases, correctness labels, substrings or embedding similarity. It attaches the matching supplied source's real label and URL, preserving `raw_generated_answer`, `citation_origin` and `citation_policy`. **Exact text provenance does not establish that the answer is relevant, complete or factually correct.** Human claim verification remains necessary. Historical indexes default to the original `model-emitted-v1` rule.

No model weights, training, prompt, generation setting, embedding model or retrieval threshold changed. The original 24 validation questions and original threshold were retained. Eight isolated policy tests and the full 103-test suite passed before follow-up test inference.

## Fresh population and outcome

Follow-up study: `9ed4cb93-716a-4953-b588-606e6d999d88`. Test: `29ed6c44573105ff`, sealed at `2026-11-08T22:58:59.199377+00:00`; corpus: `b07405a784a7045c`; index: `6e044fab88609b53`. All four arms completed 45 predictions with zero failures. The final arm completed at `2026-11-08T23:11:53.271431+00:00`.

Six new official source pages are disjoint from the entire original corpus and the validation source pages. The test has two paraphrases per fact per language: 36 answerable questions and nine future/personal unknowns, 15 per language. References and aliases were fixed before inference. All arms receive the same questions; C/D receive identical actual retrieved contexts.

| Arm | English EM / F1 | Hindi EM / F1 | Tamil EM / F1 |
|---|---:|---:|---:|
| A original, closed book | 0.00 / 17.20 | 0.00 / 12.07 | 0.00 / 11.53 |
| B LoRA, closed book | 20.00 / 20.00 | 20.00 / 20.00 | 20.00 / 20.00 |
| C original + RAG | 80.00 / 80.00 | 66.67 / 66.67 | 46.67 / 49.63 |
| D LoRA + RAG | 80.00 / 80.00 | 40.00 / 40.00 | 53.33 / 53.33 |

Values are backend-calculated from actual stored outputs and AI-curated references. Run IDs, confidence intervals, abstentions, retrieval and timing metrics are in [the final report](FINAL_RESEARCH_REPORT.md) and the run artifacts. Human factuality metrics remain Pending.

Within this population LoRA ties base RAG in English, scores lower in Hindi and higher in Tamil. The sample is small and correlated. The original and follow-up populations differ, so their percentages do not isolate the causal effect of the citation extension. Neither study establishes human factual accuracy, hallucination reduction or a general benefit from combining LoRA with RAG. No additional rule or threshold tuning was performed on follow-up test results.
