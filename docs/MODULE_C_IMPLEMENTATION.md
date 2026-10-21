# Module C implementation — 21 October 2026

Module C now lives in `creator-performance-backend/app/modules/module_c`. The shared FastAPI entrypoint
provides `POST /api/module-c/analyze`, `GET /api/module-c/status`, and `GET /health`.
See [the backend guide](../creator-performance-backend/README.md) for setup and exact commands.

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
