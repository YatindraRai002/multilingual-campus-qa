# Multilingual campus chatbot

Application update: 11 November 2026. This interface update is separate from the completed research experiments and introduces no new benchmark scores or model training.

Open `http://127.0.0.1:8765/` for the chatbot. The research overview, training charts, experiment history, source corpus, reviews and reports remain available in the sidebar.

## Ask in your language

The default **Auto-detect** setting routes English, Devanagari Hindi and Tamil questions to the corresponding reply language. English entity names inside a Hindi or Tamil question do not override the Indic script. Questions mixing both Indic scripts require an explicit reply-language choice. Transliteration and numeric-only queries also need an explicit language choice.

Choose a suggested question or type in the message box. Enter sends the question; Shift + Enter inserts a new line. **New chat** clears the current conversation. Conversation history stays in the open browser session and is not written to research predictions or human annotations.

## Five quick topics

| Topic | Information returned from the reviewed FAQ |
|---|---|
| Library technology | The technology used for Central Library automation |
| Campus bus booking | Where students manage bus bookings |
| Oori hostel rooms | Whether the hostel has air-conditioned rooms |
| Temple on campus | The listed campus temple |
| Campus maintenance | The division responsible for facilities |

Each suggestion has English, Hindi and Tamil questions and answers drawn from the active versioned FAQ corpus. Clicking a suggestion sends its full localized question through the API and displays a real source citation. Exact canonical questions and a small set of authored question variants use this FAQ path without GPU inference. It does not use keyword matching or held-out test references to assign an answer.

Source records must pass the corpus checksum, existing evidence/version checks, accepted review status, freshness and effective-date checks. These are AI source-reviewed pilot records; independent human review remains pending. Source citations retain that provenance.

## Other questions and availability

Other questions continue through the existing local Qwen + LoRA + RAG path. A response in the wrong script is replaced with the corresponding reviewed FAQ translation only when the inference pipeline established exact source attribution to that FAQ. Otherwise, the application abstains in the requested language. Raw model text remains available in the API response.

When the model is unavailable because of GPU memory, missing prerequisites or another active request, the chatbot returns a localized availability notice and keeps its quick-question buttons usable. An availability notice is not a factual answer or evidence that a question is unanswerable. The app does not stop other projects or unload their GPU models.

## API and experiment boundaries

- `GET /api/chat/suggestions` returns the five available topics and their three question localizations.
- `POST /api/chat` with `answer_mode: "faq_first"` enables the application FAQ path, conversational script routing and localized availability handling. `language: null` requests automatic detection.
- The default `answer_mode: "model"` preserves the existing model API. Closed-book A/B requests do not receive FAQ shortcut answers.
- Responses identify `answer_method`, include actual source citations when applicable and set `research_scored: false`. Direct FAQ replies additionally identify that no model inference was performed.

The benchmark and campus evaluation workers, model prompts, quantization, embedding threshold, sealed datasets, adapters and historical metric snapshots are unchanged. The FAQ shortcut is not claimed as a new fine-tuned model result. Original research validation counts in the manuscript describe the recorded research snapshot; current interface checks are recorded separately in `results/chat-ui-full-suite.xml` and `results/chat-ui-browser.log`.

## Verification

The interface update passed 133 isolated Python tests. The full Edge run passed seven browser tests and skipped the model-generation smoke check while free GPU memory was below its minimum. When GPU capacity became available, that exact model smoke check passed separately with a real cited response. The final targeted chat run passed all four core chat/mobile cases, including all 15 topic/language combinations and same-language follow-up chips; its unavailable-model case was skipped because the model was then available. That unavailable branch had already passed against the real website and is also covered by isolated tests in all three languages.

The original ten research runs, 28,274 predictions and zero human annotations are unchanged. See the public [interface validation record](../handoff/chat-interface-validation.json). Desktop and mobile screenshots are retained locally under `results/chat-ui-*.png`.
