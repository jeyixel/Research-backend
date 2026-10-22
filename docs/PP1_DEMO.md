# PP1 demonstration — October 23, 2026

## Start the two local services

Use the existing environments and packages. From `Research-backend/creator-performance-backend`:

```powershell
$env:MODULE_C_WRITER = "rules"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

From `Research-Frontend` in another terminal:

```powershell
$env:VIDEO_PREDICTION_API_URL = "http://127.0.0.1:8000"
npm.cmd run dev -- --hostname 127.0.0.1 --port 3000
```

Open `http://127.0.0.1:3000/video-prediction`. If port 8000 is in use, run FastAPI on another port and set `VIDEO_PREDICTION_API_URL` to match. No trend collector, model training, package install, or live API key is needed for the default demo. The existing standalone Module C studio remains at `http://127.0.0.1:8000/`.

Optional Gemini: set `MODULE_C_WRITER=gemini` and `GEMINI_API_KEY` in the backend's local environment or `.env`, then tick the consent checkbox in the page. **This can make a provider API call**; it remains off by default. A missing key, quota issue, timeout, invalid response, or no consent yields local explanations and the raw measurements. Only backend findings and approved explanation text are sent for Module C; the image is not sent for a separate visual assessment. For Module A, consent permits sending the supplied title, description, manually entered thumbnail text, and transcript for text comparison. Existing Module C rate and daily caps apply. `MODULE_C_GEMINI_MODEL` and `MODULE_C_WRITER_TIMEOUT_SECONDS` are optional backend settings.

## Live example verified during implementation

The existing public-corpus thumbnail `--3C_KNBTyQ.jpg` was uploaded through the **Next.js route handler** to the new FastAPI endpoint with category `education`, title `How to study with ChatGPT`, manually entered thumbnail text `Study better`, and a supplied example transcript. Gemini consent was false. The page returned HTTP 200, and the combined response had `status=partial`:

| Module | Execution result | Example evidence |
|---|---|---|
| A | Limited | Local term overlap only; no truth or contradiction verdict. Thumbnail words marked `user_supplied`. |
| B | Completed retrieval; experimental capability | `How to study with ChatGPT` matched a **sample fixture**. Its stored date and sample label were returned; no momentum claim. |
| C | Completed diagnostic; experimental advice | Actual brightness `0.857056`, contrast `0.251971`, saturation `0.12429`, text-region area `0.204049`, nine detected regions, and six historical visual matches. Explanations came from local rules. |
| D, E | Unavailable | Visible coming-soon sections with no synthetic retention or channel metrics. |
| F | Partial report | Four evidence-based checks from the available modules, no overall performance score. |

Those numbers are one executed example, not hardcoded demo output or model accuracy claims. The original `/api/module-c/analyze` endpoint also returned HTTP 200 for the same genuine image. The existing Module C tests and new PP1 failure-isolation tests pass. The frontend page and route were checked with HTTP requests, TypeScript, and ESLint. A manual browser click-through remains a sensible final rehearsal on the presentation machine.

The production Next.js build passed, and the built page and upload route both returned HTTP 200. The existing frontend Vitest command could not start in this managed Windows environment because esbuild was denied access while resolving `vitest.config.ts`; this is a test-runner startup issue, not a failing application test. No new package was installed to work around it.

## What is implemented

- **Module C:** Existing upload validation, measurements, CRAFT text-region geometry when available, CLIP retrieval, historical comparisons, rule recommendations, mobile preview, and standalone studio are preserved. New report keeps its raw response and adds separate explanations. Existing research-only outcome predictors remain unused.
- **Gemini explanation:** Optional, consented wording of approved Module C measurement explanations. The adapter cannot change numeric measurements or finding IDs; invalid provider output falls back to rules. No Gemini call is required for the demo.
- **Module A:** Optional Gemini text-to-text comparison when a transcript is marked complete and a key/consent is available. Structured categories and exact transcript excerpts are checked against the supplied text. With no Gemini, the local fallback reports limited term overlap only. A supplied transcript does not independently establish truth.
- **Module B:** Reads the existing SQLite topic database, calls Module B's keyword ranker without downloading an embedding model, and shows dated matches and sample provenance. Matching is experimental and does not prove a topic is trending or growing. Missing or unmatched data produces an explicit unavailable/limited result.
- **Module F:** One backend response with independent A/B/C statuses, raw Module C values, suggestions, limitations, and up to five combined actions. D and E explicitly return unavailable.
- **Frontend:** One page with upload, title, category, title language, optional description, manually entered thumbnail words, transcript, completeness and Gemini consent controls, and all six module sections. It uses `VIDEO_PREDICTION_API_URL` on the Next.js server only.

## Scope and limitations

- The CLIP image/title cosine is an experimental similarity measurement for explicitly selected English titles. It is not an integrity judgment.
- CRAFT detects possible text regions but does **not** recognize the words. Pretrained OCR recognition was skipped for PP1 because it adds model/dependency and language reliability risk. Manual thumbnail text is explicitly labeled as user supplied.
- Module A cannot make a defensible full integrity conclusion without a sufficiently complete transcript and a functioning consented text comparator. Even then, it checks only supplied material.
- Module B's stored database currently contains sample fixtures and collected topic observations. Dates are observation dates, not a popularity-growth measure; some source domain assignments require review.
- Rule suggestions and historical relative views are design hypotheses and descriptive records. The trained outcome models have weak held-out results and are kept research-only. No CTR, view, confidence, or retention forecast is returned.
- Modules D (hook/retention) and E (private channel-history baselines) have no implemented analysis.

## After PP1

1. Conduct human review of C findings and recommendations, including Sinhala/Tamil readability and retrieval relevance; validate any OCR option before claiming language support.
2. Evaluate B topic classification, provenance, source freshness, and retrieval on labeled local examples; separate fixtures from collected observations at storage level.
3. Validate A transcript completeness and evidence judgments with human annotations; add robust timestamp parsing and claim extraction if useful.
4. Implement D only with genuine opening-video data and retention evidence; implement E only with consented private YouTube Studio CSV uploads and creator-specific baselines.
5. Design and validate a fusion rubric only after module evidence quality and coverage are measured. Preserve the current research weights and held-out evaluation artifacts.
