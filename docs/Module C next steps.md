# Module C demo status and next steps

Updated 21 October 2026. The local analysis demo is ready. Human review and a validated performance
score are separate remaining milestones. See [API/UI integration](MODULE_C_API_AND_UI.md) and
[future work](MODULE_C_FUTURE_WORK.md).

## 1. Completed work

- Audited 31,857 source rows; excluded 1,634 exact-pixel duplicate copies, leaving **30,223 distinct images**.
- Installed PyTorch 2.11.0+cu128 and vision/OCR dependencies; confirmed the RTX 4050 is available.
- Extracted the full corpus using cached, frozen CLIP embeddings and CRAFT text-region geometry on CUDA.
- Indexed **24,163 development thumbnails**, excluding final-test channels and matching duplicate groups.
- Trained/evaluated five experiments on **5,989 images from 71 unseen channels**.
- Generated eighteen review reports and a human review CSV, with a saved-example catalog for the UI.
- Added a responsive local upload studio, historical comparisons, evidence, report export/printing, and
  descriptive comparisons of the last two live uploads in the same category.
- Verified 28 automated tests, lint, real English/Sinhala upload behavior, all eighteen report schemas,
  desktop/mobile browser behavior, JSON export, and upload error feedback.

The analysis UI is functional. The current study does not justify a creator-facing prediction score:
combined AUROC **0.531910**, title/category **0.527420**, paired difference interval
**[-0.009148, 0.017295]**; combined Brier **0.275438** versus prior **0.250010**.
Both API prediction fields remain null. Preserve these results; do not tune repeatedly against fold 4.

## 2. Start the panel demonstration

Use the existing environment; installation, extraction, indexing, and training do not need repeating.

```powershell
cd C:\Users\Janith\Desktop\Research-backend\creator-performance-backend

$env:MODULE_C_DEVICE = "cuda"
$env:MODULE_C_WRITER = "rules"
$env:MODULE_C_OCR_ENABLED = "true"

.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000/**. Keep the terminal running. The initial live request loads cached models.
The demo uses local assets/models and rules; it needs no external API key or frontend build.

Suggested presentation flow:

1. Point out the ready reference library and select a saved corpus example. Its report is clearly
   labeled as precomputed; show the mobile preview, measured properties, suggestions, and similar images.
2. Upload a creator-made or generated JPEG/PNG/WebP with title, category, and explicit language.
   Click **Analyze thumbnail** to run real inference.
3. Open a suggestion's evidence, explain a category percentile, and follow a historical source link.
   Percentiles are descriptive, not quality scores; similarity is not a forecast.
4. Upload an edited second version in the same category to see measured changes between the last two
   live reports. The comparison does not identify which version will get more views.
5. Download report JSON or print the result. Explain that the predictive study is preliminary and that
   the current report supplies measured feedback and design experiments.

Generated thumbnails can test the interface and its sensitivity to edits. Predictive accuracy needs
independent outcome labels; image uploads alone cannot measure it.

## 3. Review queue and remaining human work

Open **http://127.0.0.1:8000/review** and download the human review CSV from its link. The files live in
`artifacts/module_c/review/`. For each example, a creator/designer must enter `yes`, `partial`, or `no`
for supported findings, specific advice, absence of unsupported claims, and useful historical matches.
Record Sinhala/Tamil detection mistakes in `notes`. These judgments are still pending.

Also complete `artifacts/module_c/channel_review.csv` for category and Sri Lankan relevance. Material
dataset corrections require a separately versioned study. Automated checks cannot replace these judgments.

To regenerate reports/catalog after a deliberate artifact change, stop the server, then run:

```powershell
.\.venv\Scripts\python.exe -m app.modules.module_c.cli review
```

This preserves existing human judgments, including rows no longer selected. Start the server again.
Avoid running artifact-changing jobs concurrently with the demo.

## 4. Verification and recovery

These checks passed after the UI changes. If source or dependencies change, rerun:

```powershell
$testTmp = Join-Path (Get-Location).Path ("artifacts/module_c/pytest_tmp_" + [guid]::NewGuid().ToString("N"))
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp $testTmp
.\.venv\Scripts\python.exe -m ruff check --no-cache app tests
```

The fresh test directory and disabled pytest cache avoid the earlier Windows permission failures in
`%TEMP%/pytest-of-Janith` and `.pytest_cache`. Tests use isolated fixtures rather than depending on the
real review queue. Report generation order did not cause those failures.

For readiness, use `/health`, `/api/module-c/status`, and one real upload. Status checks the index without
loading models; the resulting report must show `image_embeddings: available`, `text_detection: available`,
and historical comparisons. English alignment appears only for `title_language=en`. Predictions remain
null. The API continues to produce reduced-capability reports when optional models are unavailable.

Verification artifacts from this implementation are in ignored `artifacts/module_c/qa/`: API/browser
summaries, desktop/mobile screenshots, and synthetic test fixtures. They are functional checks, not
expert judgments or evidence of predictive accuracy.

## 5. Work after the demonstration

Use [the future-work plan](MODULE_C_FUTURE_WORK.md) for better labels, newer/prospective evaluation,
multilingual checks, calibration, and any later model fine-tuning. A reliable score requires additional
research and API inference integration. Actual CTR requires creator-consented impressions/CTR records.

For a Next.js frontend, use [the API contract and migration example](MODULE_C_API_AND_UI.md).
The backend remains responsible for image processing, local models, retrieval, evidence, and optional
wording adapters. Human usefulness and controlled edit outcomes remain unverified.
