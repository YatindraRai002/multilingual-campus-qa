# Detailed multilingual chatbot demo

Current project folder: `D:\multilingual_faq`. The landing page is a chatbot at `http://127.0.0.1:8765/`.

## Five detailed guides

| Topic | Example English question |
|---|---|
| SRM overview | Tell me about SRM. |
| Hostels and accommodation | Tell me about hostels at SRM. |
| Placements and career preparation | Tell me about placements at SRM. |
| Admissions and courses | Tell me about admissions at SRM. |
| Campus life and facilities | Tell me about campus life and facilities. |

Every topic has an authored English, Hindi and Tamil version: 15 detailed answers. Each answer contains a title, an introduction and four named sections, rather than a one-line FAQ response. Examples in Hindi include `एसआरएम के छात्रावासों के बारे में बताइए।`; in Tamil, `எஸ்ஆர்எம் வேலைவாய்ப்புகள் பற்றி சொல்லுங்கள்.`

The user's short forms such as `tell about hostels` and `tell about placements` are also supported. Common polite prefixes, spacing and punctuation are normalized. Matching uses explicit supported questions and variants, rather than assigning a topic merely because its keyword appears in an unrelated question.

## Edit the demo answers

All prepared content is in [`config/demo_answers.json`](../config/demo_answers.json). Each topic provides localized `labels`, `questions`, `aliases`, and `answers`. An answer has `title`, `intro`, and four `sections`, each containing `heading` and `text`. Official reference links are provided in `sources`.

The application reads this file for each request, so content edits do not require model training. Refresh the page after changing suggestions. The demo is scoped to Kattankulathur. It avoids invented placement rates, salary packages, current fees, deadlines and room guarantees; users can follow the official references for current details.

Prepared answers are visibly labelled as demo overviews. They are not represented as generated Qwen answers, human-certified policies or new experimental predictions. Responses explicitly include `answer_method: "prepared_demo"`, `model_inference_performed: false`, `research_scored: false` and `is_demo: true`. Reference links are identified as demo references, not vector-retrieval hits.

## Language and interface

Auto-detection uses English, Devanagari Hindi and Tamil script. English entity names inside Hindi/Tamil do not override the Indic script. An explicit reply-language selector remains available for transliteration, numeric-only queries or mixed Indic scripts.

Click a topic or type a question. Enter sends; Shift + Enter adds a line. **New chat** clears the browser conversation. Conversation text is not inserted into research predictions or human annotations. Long answers render as escaped text in semantic headings and paragraphs. The conversation moves immediately to the start of the latest answer, allowing its introduction to be read before scrolling through the sections.

## Compatibility and research boundaries

`GET /api/chat/suggestions` now returns the five broad demo topics in all three languages. The UI calls `POST /api/chat` with `answer_mode: "faq_first"` and automatic language selection. In C/D application mode, a supported demo question is answered first; older exact source-FAQ questions still use their existing source-backed path. Unmatched questions continue to the local model when available. The default `answer_mode: "model"` and closed-book A/B behavior remain unchanged.

Busy or unavailable model requests receive a localized availability notice. The five prepared guides remain usable without free GPU memory. No unrelated GPU service is stopped.

The benchmark workers, frozen model prompts and inference code, training data, adapter, retrieval threshold, sealed campus corpus/tests and historical metrics are unchanged. This is an application demo update, not an additional model-quality experiment.

## Validation

The update passed 157 isolated Python tests. Browser checks verified all 15 detailed answer/language combinations, structured sections, visible demo labels, actual source links, language retention and mobile layout. Four directly affected browser cases passed; the environment-dependent unavailable-model case was skipped because the model was available. The supported demo questions themselves never load the GPU model.

The original 10 research runs, 28,274 predictions and zero human annotations are preserved. See [`handoff/detailed-demo-validation.json`](../handoff/detailed-demo-validation.json) for the application verification record. The earlier short-FAQ interface record remains separately preserved in [`handoff/chat-interface-validation.json`](../handoff/chat-interface-validation.json).
