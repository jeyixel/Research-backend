# Module C implementation — 21 October 2026

Module C now lives in `creator-performance-backend/app/modules/module_c`. The shared FastAPI entrypoint
provides `POST /api/module-c/analyze`, `GET /api/module-c/status`, and `GET /health`.
See [the backend guide](../creator-performance-backend/README.md) for setup and exact commands.

## Local demonstration update

The browser studio is served at `/` by FastAPI with local HTML/CSS/JavaScript assets. It supports new
uploads, explicit category/language metadata, measured category comparisons, suggestions with evidence,
historical thumbnails, mobile preview, JSON download, printing, and descriptive comparisons of the last
two live uploads in the same category. Saved public-corpus examples are served from an allowlisted
review manifest and labeled as precomputed. `/review` and its CSV download expose the human review queue.
The default writer is now `rules`. See [API/UI integration](MODULE_C_API_AND_UI.md) for routes and Next.js
migration and [future work](MODULE_C_FUTURE_WORK.md) for model and validation gaps.

CUDA extraction and indexing are complete: 30,223 cached images and 24,163 development references.
The first completed study reports combined held-out AUROC 0.531910 versus title/category 0.527420,
with paired difference interval [-0.009148, 0.017295]. This does not establish useful added visual
prediction. Combined Brier 0.275438 is worse than the prior 0.250010; API predictions remain null.

## Trained research models

The offline study trained five classifiers to distinguish videos whose `y_rel_neighbors` value is above
zero (above the channel-relative neighboring-video baseline) from those at or below zero. The split was
by channel: 24,163 training videos from 242 channels and 5,989 held-out videos from 71 unseen channels.
Seventy-one development videos were purged because their near-duplicate groups also occurred in the
held-out fold. Logistic-regression regularization was selected from `C = 0.1, 1, 10` using folds 0–3;
fold 4 was held out for the reported results.

| Experiment | Inputs | Estimator | Held-out AUROC | Balanced accuracy | Brier score |
|---|---|---|---:|---:|---:|
| `prior` | Constant class-prior probability | scikit-learn `DummyClassifier` | 0.500000 | 0.500000 | 0.250010 |
| `visual` | Brightness, contrast, saturation, CRAFT text coverage/region counts/mobile text heights | Logistic regression | 0.508946 | 0.511161 | 0.250316 |
| `title_category` | Character n-gram title TF-IDF, category, title length/word/digit/question counts | Logistic regression | 0.527420 | 0.525274 | 0.250458 |
| `clip` | Frozen 512-dimensional CLIP image embeddings | Logistic regression | 0.523926 | 0.513264 | 0.256356 |
| `combined` | Visual + title/category + frozen CLIP features | Logistic regression | 0.531910 | 0.522669 | 0.275438 |

The combined model's AUROC was only 0.004490 above the title/category baseline. Its paired channel-bootstrap
95% interval was [-0.009148, 0.017295], and its Brier score was worse than the constant prior. The study
therefore does not support showing a performance prediction in the product. This is a retrospective
relative-public-views experiment, not CTR prediction or evidence that a design change causes more views.

The local `.joblib` files are research artifacts under
`creator-performance-backend/artifacts/module_c/research/y_rel_neighbors/` and are Git-ignored. The
trained estimators are not loaded by the upload API. CLIP (`openai/clip-vit-base-patch32`) and CRAFT
provide frozen/pretrained representations or geometry; neither was fine-tuned as part of this study.
The versioned metrics above are recorded here because generated artifacts are not committed to Git.

## Implemented behavior

- Safe JPEG/PNG/WebP uploads, measured luminance/contrast/saturation, optional CRAFT text-region geometry,
  title structure, and a full-frame mobile preview. Text geometry does not establish legibility.
- Frozen, versioned CLIP image embeddings with padding that preserves the full thumbnail; optional
  English title-image cosine. Local-script titles never silently use English semantic alignment.
- Same-category retrieval, cached comparison previews, source links, mixed historical outcomes,
  channel diversity, and duplicate/self-match exclusion. Reference data excludes final-test channels
  and their near-duplicate groups.
- Evidence-linked suggestions selected by backend rules. Optional Gemini wording uses Google's
  official SDK through an independent adapter, with a restricted outbound payload, schema validation,
  local budgets, timeouts, cooldowns, and complete rule-based fallback.
- Audit, resumable extraction, indexing, five logistic/prior experiments, held-out evaluation,
  channel-bootstrap intervals, and an eighteen-report human review queue.

The trend module's Anthropic implementation and all collector source outputs are unchanged.
The backend uses its existing Python 3.11 environment; generated artifacts and weights are ignored by Git.

## Verified corpus audit

The supplied training table contains 31,857 rows across 313 channels. Every image opened successfully.
The audit identified 1,634 exact-pixel duplicate copies, leaving 30,223 distinct images. Near-duplicate
groups are conservative candidates; they are kept apart across evaluation partitions.

The resulting planned split contains 24,163 training/reference images and 5,989 final-test images;
71 additional development images are purged because their near-duplicate group appears in the test fold.

Source labels remain observational. Category labels belong to channels and can include off-topic
individual videos. Age at collection ranges from roughly a month to thirteen years. Only 279 rows in
the original filtered table have Tamil-script titles; script is not verified language.

## Validation and remaining research work

The automated suite covers invalid uploads, missing models, local-language behavior, preprocessing/cache
consistency, split leakage, duplicate-independent retrieval, comparison previews, all five experiments,
and Gemini success/error/timeout/quota behavior. The official SDK is tested with a simulated HTTP
transport; no live Gemini key is required or used by the tests.

Read actual model metrics in `creator-performance-backend/artifacts/module_c/research/y_rel_neighbors/RESULTS.md`
after the offline run. Detailed metrics, configurations, script/category slices, and uncertainty are in
the adjacent `evaluation.json`. Extraction provenance and completeness are in `extraction.json`.

Human category/locality review remains pending in `channel_review.csv`. The generated
`review/human_review.csv` and `review/review.html` queue recommendation and retrieval judgments;
their creation does not establish expert-level usefulness.

Both API forecast fields remain `null`. Neither public relative views nor a successful visual ablation
establish actual CTR, causal design quality, or expected uplift from an edit. Fixed-horizon outcomes,
stronger topic controls, local-language review, and consenting creator experiments remain necessary
before stronger performance claims.

## Creator goal and remaining product gap

The intended product should analyze a creator's proposed thumbnail, title, and category; learn from
historical thumbnail/title patterns and relative view outcomes; provide useful, evidence-backed advice;
and eventually show a validated relative-performance estimate. The current upload API measures the new
image, retrieves historical examples, and selects advice through rules. The trained classifiers are
research artifacts and are not connected to upload scoring. A completed offline training run therefore
does not make this a creator-facing predictive model.

Before adding a score, evaluate whether visual inputs improve on the title/category baseline on held-out
channels, check calibration and category/language behavior, and confirm performance on newer or
prospective data. Then implement and validate versioned inference in the API. A score from this public
dataset would estimate above-baseline relative views, not virality or CTR; statements about what caused
success or which edit will raise views require controlled creator evidence.
