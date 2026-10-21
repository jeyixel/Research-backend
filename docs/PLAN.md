# Finish Module C’s first working version today

## 1. Assessment and definition of success

**Your approach is sufficient for a useful thumbnail advisor and a credible model experiment. Its ability to predict performance or recommend changes that improve results remains unproven.**

The strongest version combines three capabilities:

- **Diagnostics:** explain what the system actually measured.
- **Historical comparisons:** show relevant thumbnails with their observed relative performance.
- **Recommendations:** suggest specific changes to test, tied to those findings.

CLIP and a relative-view classifier support this system, but they do not independently provide expert design judgment. Public views also cannot establish thumbnail CTR. [YouTube’s explanation](https://support.google.com/youtube/answer/7628154?hl=en) describes how audience and exposure affect these comparisons.

I inspected the database and reproduced the builder’s default filtering without writing the training CSV:

| Category | Eligible videos | Channels |
|---|---:|---:|
| Cooking | 6,229 | 71 |
| Education | 17,917 | 175 |
| Gaming | 7,711 | 67 |
| **Total** | **31,857** | **313** |

All eligible thumbnail paths exist; 120 sampled images passed validation. The relative-performance labels are approximately balanced within each category. These are encouraging starting conditions, although duplicates, category accuracy, and remaining image corruption still require auditing.

**Today’s completion target:** a local upload API producing English reports, measured diagnostics, similar examples, prioritized recommendations, optional Gemini wording, and a reproducible model evaluation. Predictive numbers remain experimental until evaluation supports exposing them.

## 2. Immediate steps and implementation order

Allow approximately **8–10 focused hours**, subject to dependency installation and measured extraction speed.

### Step 1 — Finish collection and audit: 45–60 minutes

Run the two existing commands from the collector folder:

```powershell
cd C:\Users\Janith\Desktop\Research-backend\data-collector
.\.venv\Scripts\python.exe yt_collector.py stats
.\.venv\Scripts\python.exe build_training_table.py
```

Then implement a read-only audit that:

- Opens every eligible image and records corrupt files, exact duplicates, and candidate near-duplicates.
- Reports category, script, channel, fold, age, and thumbnail-quality distributions.
- Resolves stored thumbnail paths relative to the collector directory.
- Produces an exclusion manifest without changing the original database or CSV.

Manually inspect ten channels per category for category and Sri Lankan relevance. Bulk approval does not establish either.

### Step 2 — Establish Module C and extract features: 1½–2 hours

Build Module C inside the existing shared backend, using its own Python 3.11 environment. The backend entrypoint and package manifest are currently empty, so include the minimal FastAPI foundation.

Use:

- Pillow/OpenCV for image handling and visual statistics.
- Frozen `openai/clip-vit-base-patch32` image embeddings.
- scikit-learn for baseline models and cosine retrieval.
- EasyOCR’s detector for estimated text-region geometry; recognition only where supported and checked.

Start GPU extraction with batches of 32, benchmark 500 images, and reduce batch size after GPU memory errors. Cache results by image hash, model revision, and preprocessing version.

Extract brightness, contrast, saturation, estimated text coverage, text-region sizes, and title structure. Preserve the full thumbnail for diagnostics and mobile previews; use documented, aspect-preserving square padding before CLIP preprocessing.

Do not infer subject clarity, emotion, or text legibility from brightness and contrast alone. Keep face detection and complex composition models outside today’s critical path.

### Step 3 — Build useful comparisons and recommendations: 1½ hours

Retrieve the six closest same-category examples using normalized image embeddings. Limit results to two per historical channel and exclude duplicate matches.

Select neighbors by similarity before inspecting their performance labels. Show their actual mix of outcomes; do not search farther away merely to display successful examples.

Implement recommendation rules that return:

- The measured finding.
- The relevant category comparison and reference count.
- A concrete suggested edit.
- A practical way to inspect or test the edit.
- Supporting evidence IDs and applicable limitations.

Examples include testing larger text, simplifying crowded text regions, or comparing a brighter version when luminance is unusually low. Present these as design experiments rather than proven improvements.

Include a **320 × 180 mobile preview** and estimated text-region sizing. Text coverage and mobile readability must remain separate findings.

### Step 4 — Train and evaluate small models: 1½–2 hours

Use `y_rel_neighbors > 0` as the initial classification target. Keep the existing continuous labels unchanged.

Compare:

1. Constant class-prior baseline.
2. Handcrafted image features.
3. Title/category features, including character-level TF-IDF.
4. CLIP image embeddings.
5. Combined features.

Use regularized logistic regression, testing regularization values `0.1`, `1`, and `10`. Reserve existing **fold 4** for final testing; use folds 0–3 for development and model selection.

Fit preprocessing only on training partitions. Exclude cross-partition duplicate matches from training and keep retrieval indexes and category reference distributions restricted to training data during evaluation. This follows the leakage precautions described in [scikit-learn’s guidance](https://scikit-learn.org/stable/common_pitfalls.html).

Report AUROC, balanced accuracy, Brier score, category results, script slices, and channel-bootstrap uncertainty. Also report channel-balanced results so prolific channels have less influence.

**The decisive experiment:** whether image features improve over title/category features. If they do not, report that finding and retain the useful diagnostic/retrieval advisor.

### Step 5 — Add the API and Gemini wording: 1½–2 hours

Create `POST /api/module-c/analyze` accepting multipart thumbnail, title, category, and optional title language.

Return:

- Measurements and capability statuses.
- Historical comparisons and similarity scores.
- Findings and prioritized recommendations.
- Data/model versions and limitations.
- `predicted_ctr: null`.
- `relative_performance_prediction: null` by default.

Keep model-study predictions in research artifacts today. Do not convert weak results into a thumbnail-quality percentage.

Use Swagger’s upload form for the local demonstration; a separate website is outside today’s scope.

## 3. Gemini integration and provider boundaries

Create a provider-independent `RecommendationWriter` interface with rule-based and Gemini implementations. A future Ollama implementation must consume the same verified recommendation context.

Use Google’s official **`google-genai` SDK**. Configure provider, API key, model, timeout, and local request budget through environment variables. [Official SDK documentation](https://googleapis.github.io/python-genai/).

Default to **`gemini-3.5-flash-lite`**. Google currently restricts 2.5 models to previous users, while 3.5 Flash-Lite lists free-tier input/output. Allow `gemini-2.5-flash-lite` through configuration for accounts that retain access. [Model availability](https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash-lite), [pricing](https://ai.google.dev/gemini-api/docs/pricing).

Implementation requirements:

- Generate the complete rule-based report before requesting Gemini wording.
- Send only an allowlisted summary of non-sensitive measurements, category comparisons, and approved actions. Exclude images, raw titles/OCR text, identifiers, CSVs, and datasets.
- Ask Gemini to rewrite approved recommendations and reference their evidence IDs. It must not calculate findings, invent observations, or change predictions.
- Validate structured responses; reject unsupported evidence references and numerical performance claims.
- Use an eight-second overall deadline, at most one retry for transient failures, and immediate fallback for authentication errors, exhausted quota, blocked responses, or invalid output.
- Honor rate-limit cooldowns without delaying the report; impose configurable development budgets, initially two requests/minute and twenty/day.
- Never enable billing, rotate keys to evade limits, or switch to paid models automatically.

Free-tier limits depend on the project and model; inspect actual limits in AI Studio. Google also states that unpaid-service content may be used to improve its products, reinforcing the restricted payload design. [Rate limits](https://ai.google.dev/gemini-api/docs/rate-limits), [data terms](https://ai.google.dev/gemini-api/terms).

Leave the trend module’s Anthropic integration untouched.

## 4. Validation and acceptance criteria

Automated checks must cover:

- Corrupt, oversized, and unsupported uploads.
- Consistent offline/inference preprocessing and resumable feature caching.
- Forbidden predictive inputs and channel overlap across evaluation partitions.
- Duplicate exclusion and retrieval without self-matches.
- Missing language capabilities, model artifacts, and category references.
- Missing Gemini key, timeout, quota exhaustion, invalid output, and fallback.
- Outbound payloads containing only permitted fields.

Manually review **18 reports**, six per category, covering English, Sinhala, Tamil, and mixed titles. Record whether each finding is supported, each suggestion is specific, and the report avoids unsupported claims. This is an initial usability check, not proof of expert-level accuracy.

Completion requires a working upload-to-report demonstration, reproducible evaluation artifacts, documented limitations, and successful operation without Gemini.

## 5. Defaults and improvements after today

- **English reports today.** Accept local-language titles, but do not treat Latin script as proof of English.
- Skip semantic title-image alignment unless English is explicitly selected. CLIP’s model card documents its English-language limitations. [Model card](https://huggingface.co/openai/clip-vit-base-patch32).
- Separate text detection from recognition: EasyOCR lists Tamil recognition but does not list Sinhala. [Supported languages](https://www.jaided.ai/easyocr/).
- Use the detected RTX 4050’s 6 GB VRAM for frozen feature extraction; benchmark before promising completion time.
- Keep uploads temporary, avoid storing creator content in logs, and defer deployment, queues, and database services.

The highest-value subsequent improvements are **human-annotated packaging judgments**, fixed-horizon view snapshots, stronger local-language validation, and consenting creator experiments. Evaluate actual redesigns using controlled comparisons and the experiment’s stated outcome—YouTube’s native testing selects winners using watch time. [YouTube testing guidance](https://support.google.com/youtube/answer/16391400?hl=en).

Those steps establish whether the recommendations help creators. Increasing model complexity alone will not answer that question.
