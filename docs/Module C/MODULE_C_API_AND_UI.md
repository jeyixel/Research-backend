# Module C API and UI integration

Updated 21 October 2026. This is the contract for the local FastAPI implementation, including the
browser UI at `/`. The same analysis API can be used by a future Next.js frontend.

## Run the local demonstration

From PowerShell in `creator-performance-backend`:

```powershell
$env:MODULE_C_DEVICE = "cuda"
$env:MODULE_C_WRITER = "rules"
$env:MODULE_C_OCR_ENABLED = "true"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000/**. Keep this terminal open. The default writer is now `rules`; an explicit
`.env` or shell setting can override it. No frontend build, Node server, API key, or internet connection
is needed when the reference artifacts and model weights are cached. Use one backend worker for this
local GPU demo. The first live request loads models and may take longer.

The UI supports file selection/drop, title/category/language inputs, loading and error feedback, measured
features and category percentiles, a mobile preview, evidence-linked suggestions, historical thumbnails
and source links, raw JSON download, and printing. The last two **live** reports in the same category
show measured changes. They are kept in tab memory; reloading clears them. No winning revision is inferred.
Saved examples display precomputed public-corpus reports and are labeled accordingly. They do not run
new inference. Generate them with `python -m app.modules.module_c.cli review` using the backend environment.

Sources: `creator-performance-backend/app/main.py`, `app/demo.py`, `app/web/`, and
`app/modules/module_c/schemas.py`. Assets are included as Python package data. The OpenAPI definition
at `/openapi.json` and interactive `/docs` describe the implemented request and response schemas.

## Routes

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Frame upload studio |
| GET | `/health` | Process health; does not verify loaded GPU models |
| GET | `/api/module-c/status` | Reference index readiness and configured wording provider |
| POST | `/api/module-c/analyze` | Analyze a new upload; returns a `Report` |
| GET | `/api/module-c/examples` | One saved example per category, or an empty list before review generation |
| GET | `/api/module-c/examples/{video_id}` | A saved `Report` from the validated review manifest |
| GET | `/review` | Eighteen-report HTML review queue |
| GET | `/review/human_review.csv` | Download the human review sheet |
| GET | `/docs`, `/openapi.json` | Interactive API documentation and machine-readable contract |
| GET | `/static/studio.css`, `/static/studio.js` | Local UI assets |

No user-supplied filesystem path is accepted by these routes. Example IDs must be present in the local
manifest; the manifest validates ID characters before any report file is read. `/review` and the CSV
route serve fixed files. The artifact directory is not exposed as a static directory.

## New-upload request

`POST /api/module-c/analyze` uses **multipart/form-data**, not JSON. Let the browser set its boundary.

| Field | Type | Rules |
|---|---|---|
| `thumbnail` | File, required | Static JPEG, PNG, or WebP; at most 10 MiB, 25 million pixels; each dimension at least 16 pixels |
| `title` | String, required | Nonblank, maximum 500 characters |
| `category` | String, required | `cooking`, `education`, or `gaming` |
| `title_language` | String, optional | `en`, `si`, `ta`, `mixed`, `unknown`; default `unknown` |

The supplied language is explicit user metadata. Latin script is not automatically treated as English.
Image-title cosine is attempted only for `en`. Reports and advice are currently in English.

```typescript
type Category = "cooking" | "education" | "gaming";
type TitleLanguage = "en" | "si" | "ta" | "mixed" | "unknown";

async function analyzeThumbnail(
  thumbnail: File, title: string, category: Category, language: TitleLanguage,
) {
  const form = new FormData();
  form.append("thumbnail", thumbnail);
  form.append("title", title);
  form.append("category", category);
  form.append("title_language", language);

  const response = await fetch("/api/module-c/analyze", { method: "POST", body: form });
  const data = await response.json();
  if (!response.ok) {
    // FastAPI validation errors use a detail array; other errors use a detail string.
    const detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    throw new Error(detail || `Analysis failed (${response.status})`);
  }
  return data; // Generate Report types from /openapi.json in the migrated frontend.
}
```

The static UI allows five minutes before timing out a live request. A browser timeout/disconnect does
not cancel GPU work already executing in the backend. Shared GPU inference is serialized; this version
has no task queue or progress endpoint.

## Report fields and their meaning

| Field | Meaning and UI treatment |
|---|---|
| `module`, `version`, `category`, `title_language`, `report_language` | Report identity and context; the raw title is not repeated in the response |
| `measurements` | Brightness = mean normalized luminance; contrast = luminance standard deviation; saturation = mean normalized HSV saturation; text coverage = union of estimated text boxes divided by image area; text-region counts/heights may be null |
| `title_features` | Character/word/digit/question-mark counts, not a semantic quality assessment |
| `findings[]` | `id`, `metric`, `observed`, `percentile`, `reference_count`, `statement`, and `basis`; percentile describes a category distribution, not a success score |
| `recommendations[]` | `id`, `priority`, `action`, `how_to_test`, `explanation`, `evidence_ids`; evidence IDs resolve to findings |
| `historical_comparisons[]` | Up to six same-category examples with `video_id`, `source_url`, uncalibrated `visual_similarity`, historical `relative_view_performance`, `outcome`, and optional JPEG data-URI `thumbnail_preview` |
| `image_title_alignment` | Experimental English CLIP cosine or null; not CTR, factual correctness, or clickability |
| `mobile_preview` | Full-frame 320 × 180 JPEG data URI; aspect ratio is preserved with padding |
| `capabilities` | Actual availability/status for embeddings, text detection, recognition, retrieval, alignment, and outcome prediction |
| `predicted_ctr`, `relative_performance_prediction` | Always null in this version; do not replace with invented scores |
| `provenance` | Data hash, model ID/revision, preprocessing version, reference rows/folds |
| `wording` | `provider`, `status`, optional `reason` and `model`; Gemini can fall back to rules |
| `limitations[]` | Constraints that should remain visible in a creator-facing interface |

Unavailable measurements are **null**, not zero. Text detection estimates geometry; recognition,
face detection, emotion classification, and scene-specific diagnoses are not implemented. The UI safely
renders response strings as text, accepts only raster data-image previews, and builds source links from
video IDs. Uploaded titles must never be injected as HTML in a replacement frontend.

Historical relative views compare a video's log views with neighboring uploads on its own channel.
They are observed outcomes, not predicted outcomes for the uploaded image. Index retrieval uses
development folds 0–3, excluding duplicate groups present in final fold 4. Similarity ranks examples
before outcomes are read; there is no guarantee every returned set contains both outcome classes.

## Status, examples, and errors

Status includes `reference_index`, `reference_rows`, `prediction_mode: "research_only"`, `report_language`,
`writer_configured`, `gemini_key_configured` (boolean only), and `data_version`. It does not load models;
check a live report's capabilities to verify actual inference availability.

The example catalog is `{ "examples": [...] }`. Each item contains `video_id`, `title`, `category`,
`title_language`, `thumbnail_preview`, and `report_url`. The saved-report endpoint returns the same
`Report` schema as a live request, but its source is precomputed. Keep that distinction visible.

| Status | Meaning |
|---|---|
| 200 | Successful response; some capabilities may still be unavailable |
| 413 | Upload exceeds the byte limit |
| 415 | Unsupported declared MIME type |
| 422 | Invalid form values, blank title, corrupt/unsupported image, animation, or unsafe dimensions |
| 404 | Unknown saved example, missing review page/sheet, or unknown route |
| 503 | Saved-example manifest/report is invalid or missing after being listed; regenerate review artifacts |
| 500 | Unexpected server error; inspect the backend terminal |

Missing embeddings or text detection generally produce a reduced-capability **200** report. They are
not silently represented as successful zero-valued measurements. Network/client timeouts are separate
from the HTTP statuses above.

## Next.js migration

Keep FastAPI responsible for models, features, retrieval, and evidence selection. Replace `app/web/`
with Next.js components calling the same contract. For local development, proxy through Next.js so
browser requests remain on one origin, using its documented [external rewrites](https://nextjs.org/docs/app/api-reference/config/next-config-js/rewrites):

```typescript
// next.config.ts — server configuration, not client code
import type { NextConfig } from "next";
const backend = process.env.CREATOR_BACKEND_URL || "http://127.0.0.1:8000";
const nextConfig: NextConfig = {
  async rewrites() {
    return [{ source: "/api/module-c/:path*", destination: `${backend}/api/module-c/:path*` }];
  },
};
export default nextConfig;
```

Configure proxy upload limits and timeouts for 10 MiB files and cold model loading. If direct browser
cross-origin calls are required, add an explicit frontend-origin allowlist using
[FastAPI CORS middleware](https://fastapi.tiangolo.com/tutorial/cors/); CORS is not
enabled in this local version. Review-gallery HTML, CSV downloads, `/health`, and `/docs` need their
own proxy rules or direct backend links. A deployed Next.js server cannot reach a developer's laptop
through its own `127.0.0.1`; host the backend on a reachable GPU service and set the URL there.

Use generated OpenAPI TypeScript types, preserve nulls and capability states, show source/evidence,
and keep Gemini keys server-side. Add authentication, limits, transport security, and concurrency control
before public hosting. No public deployment was created for this local demo.

## Local models and external services

| Component | Current use | External request during analysis? |
|---|---|---|
| FastAPI/PyTorch/CLIP | Local API and frozen `openai/clip-vit-base-patch32` embeddings | No; requests use cached model weights |
| EasyOCR/CRAFT | Local text-region detector, recognizer disabled | No; cached weights |
| Google Gemini Developer API (`google-genai`) | Optional rewriting of approved explanations only | Only when configured; allowlisted category/measurement/advice payload, no uploads/raw titles/OCR text/full dataset |
| YouTube links | Open the historical video's public page | Only when a user follows a source link |
| YouTube Data API in the collector | Prior dataset acquisition | Separate from this upload API; not called to analyze a thumbnail |

Gemini does not train the local model or independently select advice. Rules remain available without
a key. Provider model availability, free quotas, and data terms must be checked before opting in; the
local demo uses rules. See [future work](MODULE_C_FUTURE_WORK.md) for validation and product gaps.
