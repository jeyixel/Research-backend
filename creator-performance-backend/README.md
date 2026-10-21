# Module C — Thumbnail Expert

A local FastAPI service and reproducible research pipeline for Gaming, Education, and Cooking thumbnails.
It reports measured visual properties, category references, similar public examples, and testable design
suggestions. All reports are in English. It does **not** forecast CTR or claim that editing a thumbnail
causes a view increase. Research predictions remain separate from the upload API.

## Windows setup

Run from `creator-performance-backend`, using this directory's Python 3.11 environment.
Keep the collector's environment separate. No Postgres, Redis, cloud hosting, or paid AI subscription is needed.

```powershell
uv venv --python 3.11
uv pip install --python .venv/Scripts/python.exe -e ".[dev,vision,ocr,gemini]" --torch-backend cu128
Copy-Item .env.example .env  # only if you do not already have a .env
```

CUDA wheels must suit your NVIDIA driver. CPU-only installs can use `--torch-backend cpu`.
The core API can run without the optional `vision`, `ocr`, and `gemini` extras; unavailable measurements
are explicit. Extraction requires `vision`; OCR adds estimated text-region geometry, never Sinhala OCR claims.

## Offline corpus pipeline

The collector's `data/training_table.csv` must already exist. These commands only read the collector's
CSV and images; generated output goes to ignored `artifacts/module_c/`.

```powershell
.\.venv\Scripts\python.exe -m app.modules.module_c.cli audit
.\.venv\Scripts\python.exe -m app.modules.module_c.cli extract --limit 500
.\.venv\Scripts\python.exe -m app.modules.module_c.cli extract
.\.venv\Scripts\python.exe -m app.modules.module_c.cli index
.\.venv\Scripts\python.exe -m app.modules.module_c.cli train
.\.venv\Scripts\python.exe -m app.modules.module_c.cli review
```

- `audit` opens every image, writes an exclusion manifest, exact-pixel hashes, and conservative dHash
  near-duplicate groups. Exact-pixel copies are represented once. dHash matches are candidates, not
  proof of copying; inspect `near_duplicate_candidates.csv`. Original rows and labels are preserved.
- `extract --limit 500` benchmarks at most 500 **new** images. `extract` resumes the versioned cache,
  starts at batch size 32, and halves batches after CUDA memory errors. Frozen weights are downloaded
  only by extraction. `--offline` disables downloads. Expect several hundred MB of model downloads.
- CLIP receives an aspect-preserving, gray-padded full image before its normal processor, avoiding a
  center crop that discards side text. Visual statistics and OCR use the full image. This preprocessing
  is versioned and shared with inference. Embeddings, model commit, detector version, and corpus hash
  are recorded. Model/version changes cause a separate cache entry rather than reusing stale features.
- Text boxes come from CRAFT through EasyOCR with recognition disabled. Box union area, counts, and
  mobile-scaled region heights are measured; these do not establish character size or legibility.
  Detector absence/failure yields `null`, not a false zero. Sinhala/Tamil detection still needs local checks.
- `index` uses folds 0–3 only and purges near-duplicate groups appearing in fold 4. Retrieval ranks by
  image cosine similarity before reading labels, returns up to six same-category examples, and caps
  each channel at two examples. It excludes self matches and duplicate groups. Similarity is uncalibrated.
- `train` selects regularization on development folds and evaluates fold 4. It compares prior,
  visual-only, title/category character-TF-IDF, CLIP-only, and combined logistic models. It fits transforms
  on training partitions only and purges test-related duplicates from development training/validation.
  It reports AUROC, balanced accuracy, Brier score, category/script slices, equal-channel metrics, and
  channel-bootstrap intervals. `train --target y_rel_prev` runs the alternative target separately.
  Treat the final test as a one-time assessment; do not tune against its results.
- `review` creates eighteen public-corpus reports, a local HTML preview, and an unfilled human review CSV.
  It never sends these reports to Gemini. `channel_review.csv` separately queues ten channels per category
  for locality/category review. Generating these files is **not** completion of human validation.

Important outputs:

| Artifact | Purpose |
|---|---|
| `audit.json`, `manifest.csv`, `exclusions.csv` | Corpus counts, validity, duplicate groups, exclusions |
| `features.sqlite`, `extraction.json` | Resumable features and frozen embeddings with provenance |
| `index.json`, `index.csv`, `index_embeddings.npy` | Development-only retrieval/reference corpus |
| `research/y_rel_neighbors/RESULTS.md` | Readable held-out results and limitations |
| `research/y_rel_neighbors/evaluation.json` | Metrics, slices, intervals, split counts, configurations |
| `review/review.html`, `review/human_review.csv` | Eighteen-example human review queue |

Joblib files are local, research-only artifacts. Never load joblib files from users or untrusted sources.
If the training CSV or thumbnails change, rerun audit, extraction, and indexing. Restart the API after
rebuilding artifacts. Do not run independent audit/extraction processes against the same artifact directory.

Give `review/review.html` and `review/human_review.csv` to the creator or designer reviewing the reports.
Open the HTML locally and enter `yes`, `partial`, or `no` in each human-review column. Check whether
the observations match the image, the suggested experiment is specific and practical, the wording
avoids unsupported claims, and the retrieved thumbnails are useful comparisons. Use `notes` to record
the exact problem and any Sinhala/Tamil detection errors. Keep judgments independent of the displayed
view outcomes. Review `channel_review.csv` separately for category and Sri Lankan relevance.
An eighteen-example review is an initial usability check; preserve failures before changing rules.

## Local API/demo

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open [Swagger](http://127.0.0.1:8000/docs). Use `POST /api/module-c/analyze`:

| Field | Accepted values |
|---|---|
| `thumbnail` | JPEG, PNG, WebP; static image, max 10 MiB and 25 million pixels |
| `title` | Nonempty title, up to 500 characters |
| `category` | `cooking`, `education`, `gaming` |
| `title_language` | Optional: `en`, `si`, `ta`, `mixed`, `unknown`; defaults to `unknown` |

The response contains measurements, capability statuses, findings, category percentiles/reference counts,
evidence-linked recommendations with a test procedure, historical examples with source links, a 320×180
data-URI preview, cached previews of retrieved examples, provenance, and limitations. `predicted_ctr` and `relative_performance_prediction` are
always `null` in this version. `GET /health` checks the API; `GET /api/module-c/status` checks index readiness.

English title-image cosine is returned only when `title_language=en` and CLIP is available. Latin script
is not assumed to mean English. Cosine similarity is experimental, not a truthfulness or clickability score.
Reports do not infer that a face/dish/subject is visible or that text is unreadable from global statistics.
The mobile-preview check is always offered, with extra measured suggestions when category evidence permits.

The first request loads cached models and can be slower. Run the extraction command first to acquire
weights. API requests never download models. With missing artifacts the core visual report still works.
Uploaded content is processed in memory (multipart handling may temporarily spool files) and closed after
the request. The service does not store upload content or include titles, OCR text, or uploads in logs.
Bind to localhost: this MVP does not provide authentication or production ingress controls.

For an explicitly saved local report:

```powershell
.\.venv\Scripts\python.exe -m app.modules.module_c.cli analyze --image path/to/image.jpg --title "Recipe tutorial" --category cooking --title-language en --out local-report.json
```

## Optional Gemini wording (free-tier development)

Set `GEMINI_API_KEY` in the backend's `.env`. Never commit it. Defaults are in `.env.example`:

```dotenv
MODULE_C_WRITER=gemini
GEMINI_API_KEY=
MODULE_C_GEMINI_MODEL=gemini-3.5-flash-lite
MODULE_C_WRITER_TIMEOUT_SECONDS=8
MODULE_C_GEMINI_REQUESTS_PER_MINUTE=2
MODULE_C_GEMINI_REQUESTS_PER_DAY=20
```

The official `google-genai` SDK calls the Gemini Developer API. Model IDs are configurable, including
`gemini-2.5-flash-lite` for accounts that retain access. Check current availability, free eligibility, and
your actual quotas in AI Studio. This application never enables billing or switches models automatically;
use a project without billing for free-only development. Free quota is not unlimited or guaranteed.

The backend generates findings, actions, evidence, comparisons, and predictions independently. Gemini
can rewrite only approved explanation text. Its allowlisted payload contains category and non-sensitive
measurement summaries, plus backend-approved actions/explanations. It excludes uploaded images, raw
titles, OCR text, identifiers, private CSVs, similarity examples, and full datasets. Google's unpaid-service
terms permit product-improvement use; keep private material out of these requests.

Each result is schema-validated and checked for changed evidence IDs, invented numbers, outcome claims,
and unsupported subject descriptions. The original actions/test steps always remain unchanged. This
validation cannot establish perfect semantic faithfulness; the wording still needs human review.

Missing keys, quota errors, blocked/invalid responses, and failures return the complete original rule-based
report. There is an eight-second overall deadline, at most one short retry for transient server failures,
and persistent SQLite budgets/cooldowns shared by local processes. The local daily cap resets on the
Pacific calendar; provider limits remain authoritative. Set `MODULE_C_WRITER=rules` for fully offline wording.

`RecommendationWriter` defines the stable adapter boundary. Add a future Ollama writer behind that
interface without changing measurement or recommendation selection. The trend module is untouched.

## Verification and research limits

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check app tests
```

Tests use synthetic images and stubbed providers; they require no API key or model download.
Complete the human review CSVs before claiming expert-level guidance or reliable local-language behavior.
Predictive validity needs prospective fixed-horizon outcomes, stronger topic controls, and preferably
consenting creator experiments. A positive visual ablation is an association, not a causal design result.

Sources: [CLIP model card](https://huggingface.co/openai/clip-vit-base-patch32),
[EasyOCR languages](https://www.jaided.ai/easyocr/),
[Google Gen AI SDK](https://googleapis.github.io/python-genai/),
[Gemini models](https://ai.google.dev/gemini-api/docs/models),
[pricing](https://ai.google.dev/gemini-api/docs/pricing),
[rate limits](https://ai.google.dev/gemini-api/docs/rate-limits),
[data terms](https://ai.google.dev/gemini-api/terms).
