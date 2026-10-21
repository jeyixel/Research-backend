# Next tasks to finish Module C

## Intended outcome and current scope

The intended creator experience is to upload a proposed thumbnail with its title and category, receive
evidence-based feedback about the design, see relevant historical examples, and, if the research supports
it, receive a calibrated estimate of **relative view performance**. The current API already provides
measurements, comparisons, and rule-based suggestions. It does **not** use the trained classifiers to
score uploads: `relative_performance_prediction` and `predicted_ctr` are both `null`.

The commands below finish and validate this **first version**. They do not, by themselves, deliver the
full scoring goal. Public thumbnail and view data can show associations with above- or below-baseline
views; it cannot identify why a video went viral, recover CTR, or prove that changing one design element
will improve an outcome. The later work needed for a defensible creator score is listed in section 6.

## 1. Verified starting point

I read the docs and checked the artifacts without modifying files.

- Implementation is ready; **24 tests and lint previously passed**.
- Audit completed: **30,223 distinct images**, after excluding 1,634 exact duplicate copies.
- CLIP and CRAFT weights are cached.
- **CUDA installation is incomplete.** The resumable wheel download is still running. PyTorch, torchvision, transformers, and EasyOCR are not installed yet.
- Extraction, indexing, model evaluation, and the review page have **not** run.

Run the following commands yourself, **one stage at a time**. They generate local artifacts but do not change your collector’s source dataset.

## 2. Finish installation and verify the GPU

Open PowerShell in the backend directory. Use its existing environment; do not recreate it.

```powershell
cd C:\Users\Janith\Desktop\Research-backend\creator-performance-backend

$env:MODULE_C_DEVICE = "cuda"
$env:MODULE_C_WRITER = "rules"
$env:MODULE_C_OCR_ENABLED = "true"
```

**First, let the existing download finish.** It should print `Verified` followed by the wheel path.

If that process exits before completion, resume it with the existing helper—do not run two copies:

```powershell
.\.venv\Scripts\python.exe artifacts/module_c/download_torch.py
```

Once complete, verify the downloaded wheel and install it together with the remaining dependencies:

```powershell
$wheel = ".\artifacts\module_c\.cache\wheels\torch-2.11.0+cu128-cp311-cp311-win_amd64.whl"
$expected = "90ef0c2454e5296a9fb021ddd42252e4ce1abe2c0a4988a173ef90a6cded0bf5"

if (-not (Test-Path -LiteralPath $wheel)) {
    throw "Download has not finished."
}

if ((Get-FileHash -LiteralPath $wheel -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) {
    throw "Wheel checksum mismatch. Do not install."
}

uv pip install --python .venv/Scripts/python.exe $wheel -e ".[dev,vision,ocr,gemini]" --torch-backend cu128
```

Verify actual CUDA availability:

```powershell
.\.venv\Scripts\python.exe -c "import torch; print('PyTorch:', torch.__version__); print('CUDA available:', torch.cuda.is_available()); assert torch.cuda.is_available(), 'Stop: CUDA is unavailable'; print('GPU:', torch.cuda.get_device_name(0))"
```

**Proceed only if CUDA is available and your RTX 4050 appears.**

## 3. Extract features, build references, and evaluate

**A. Benchmark 500 images**

```powershell
.\.venv\Scripts\python.exe -m app.modules.module_c.cli extract --offline --limit 500

Get-Content .\artifacts\module_c\extraction.json
```

Check that:

- `device` is `cuda`.
- `detector` starts with `craft-`.
- `processed_this_run` is 500 on the first successful run.
- `complete` is `false`, which is expected at this stage.

If the detector says `no-text-detector-v1`, stop and resolve that before extracting the entire corpus. Use the printed images/second to estimate the remaining runtime.

**B. Resume extraction for the whole corpus — long-running**

```powershell
.\.venv\Scripts\python.exe -m app.modules.module_c.cli extract --offline
```

It reuses the benchmark cache. After completion:

```powershell
Get-Content .\artifacts\module_c\extraction.json
```

Require `complete: true` and `corpus_rows: 30223`.

**C. Build the historical comparison index**

```powershell
.\.venv\Scripts\python.exe -m app.modules.module_c.cli index
.\.venv\Scripts\python.exe -m app.modules.module_c.cli status
```

Expect `reference_index: available` and approximately **24,163 reference images**, with final-test channels and matching duplicate groups excluded.

**D. Train and evaluate the five experiments — long-running**

```powershell
.\.venv\Scripts\python.exe -m app.modules.module_c.cli train
```

This trains small classifiers on cached features; it does **not** fine-tune CLIP. The classifier study runs on CPU.

Read the results:

```powershell
Get-Content .\artifacts\module_c\research\y_rel_neighbors\RESULTS.md
```

Compare `combined` against `title_category`, then inspect category/script slices and channel-balanced results in the adjacent `evaluation.json`.

The paired combined-minus-title AUROC interval determines whether there is convincing evidence of added visual signal. If it includes zero, report the improvement as uncertain. **Do not repeatedly tune against fold 4.**

Before treating the study as final, complete the existing `channel_review.csv` checks for category and Sri Lankan relevance. Material dataset corrections require a separately versioned rerun.

## 4. Verify the API and obtain human review

**A. Run checks after installing the vision dependencies**

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check app tests
```

**B. Generate the 18-example review page**

```powershell
.\.venv\Scripts\python.exe -m app.modules.module_c.cli review
Invoke-Item .\artifacts\module_c\review\review.html
```

Give your creator/designer the HTML and adjacent `human_review.csv`. Ask them to mark `yes`, `partial`, or `no` for:

- Findings supported by the image.
- Specific, practical advice.
- Absence of unsupported claims.
- Useful similar-thumbnail matches.

Record Sinhala/Tamil detection mistakes in `notes`. These judgments remain pending until the reviewer completes them.

**C. Start the local upload demonstration**

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000/docs** and try `POST /api/module-c/analyze` with your thumbnail, title, category, and language.

Confirm:

- Image embeddings and text detection are available.
- Measurements, category references, mobile preview, suggestions, and up to six historical comparisons appear.
- Sinhala/Tamil/mixed titles receive honest capability limitations.
- English alignment appears only when `title_language=en`.
- Both prediction fields remain `null`.
- Reports work with Gemini disabled.

## 5. First-version completion criteria and defaults

Call this first version complete when installation succeeds, extraction is complete, evaluation artifacts exist, the real upload flow works, and reviewer judgments are recorded. This is a functioning analysis and research prototype, not yet a validated creator-facing prediction model.

Keep **rules-only wording** during validation. Gemini is optional afterward; configuration is documented in the [backend guide](creator-performance-backend/README.md).

The existing API needs no additional code changes to run this sequence. Predictive performance and expert usefulness remain unverified until these remaining checks finish. Even a positive model result establishes historical association, not CTR or guaranteed improvement from an edit.

## 6. Work required for a creator-facing score

1. Inspect the held-out results, especially `combined` versus `title_category`, calibration/Brier score,
   category and script slices, and channel-balanced metrics. Keep fold 4 untouched after this assessment.
   If the visual model does not add reliable value, improve the data or methods in a separately versioned
   study rather than publishing a score from weak evidence.
2. Validate the chosen score on newer fixed-age outcomes or a prospective creator sample, with stronger
   topic and language checks. Define the output precisely as an estimated chance of above-baseline
   **relative views** for comparable videos, with uncertainty and an explicit unsupported/uncertain state.
3. Only after those gates pass, implement versioned inference in the upload API using the same
   preprocessing as training. Calibrate and monitor the model, populate
   `relative_performance_prediction`, and keep `predicted_ctr` null unless consented Analytics data
   supports a separate CTR model. This requires additional code and validation.
4. Connect advice to measured facts, suitable historical comparisons, and validated model evidence.
   Have creators/designers review whether observations are correct and suggestions are useful. To claim
   an edit improves performance or explain why a thumbnail succeeded, run controlled creator experiments.
