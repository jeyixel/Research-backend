# PROJECT CONTEXT — AI-Powered YouTube Idea Discovery & Pre-Upload Performance Analysis for Sri Lankan Creators

> **Purpose of this file:** Persistent product and research context for an AI coding agent working on this project. Read this before planning, designing, generating, or modifying application code. It explains **what we are building, why, for whom, the six-module concept, and the important data/scientific limitations**. It is **not** proof that any feature, model, dataset, API integration, or technology stack has already been implemented.
>
> **Project status:** Planned/proposed student research project; implementation choices and model capabilities must be verified in the actual repository.
>
> **Primary source:** Uploaded document `My part.docx`, titled *AI-Powered Pre-Upload Performance Prediction for Sri Lankan YouTube Content Creators — System Architecture, Novelty Statement & Implementation Roadmap* (panel review report, August 2026).
>
> **Additional clarification from the project owner:** The product has **two equally important user-facing goals**: (1) recommending timely content ideas based on YouTube trends and (2) assessing a creator's prepared video before it is published. The owner also emphasizes that each user's YouTube Studio CSV is privately owned and should **not** be assumed available for pooled model training. These clarifications extend or refine the original report's emphasis.

---

## 1. The project in one paragraph

We want to build a Sri Lanka-focused, AI-assisted platform for YouTube content creators in **Gaming, Education, and Cooking**. A creator who does not know what to film next can explore **recent, locally relevant content trends**, discover promising topics, and get **original, actionable video ideas**. A creator who has already produced a video can submit a **pre-upload** video and its proposed title, description, thumbnail, and optional channel history to get an **approximate performance/readiness assessment**, reasons behind that assessment, and practical improvements to consider **before publishing**. The system is organized into **six cooperating modules (A–F)**. The platform should help people make better creative decisions; it must not pretend to know YouTube's proprietary recommendation algorithm or promise future views, CTR, or retention with unwarranted precision.

### One-sentence product description

**A multilingual, Sri Lanka-focused YouTube creator assistant that finds what to make next and explains how ready a planned video is to perform before upload.**

### Target outcome

Creators should leave the app with one or both of these:

1. **A concrete next-video concept**, grounded in actual recent trend evidence and adapted to the creator's category and audience.
2. **An explainable pre-publish report**, indicating likely strengths, potential weaknesses, a cautious overall score or assessment, and suggestions for improvement.

---

## 2. The two main goals — do not collapse them into one feature

### Goal 1 — Discover trends and generate video ideas

**Problem:** A Sri Lankan YouTube creator runs out of content ideas, or is unsure what is becoming popular in the local market.

**Product behavior:**

- Show **recent and relevant topics/videos** for the creator's chosen category: Gaming, Education, or Cooking.
- Prioritize **Sri Lanka relevance**, while recognizing that a global trend can also be relevant to Sri Lankan audiences.
- Let creators explore what seems to be gaining interest and **why the system considers it relevant**.
- Turn trend observations into suggested **video angles, titles, hooks, and formats**, not just a list of popular video links.
- Distinguish an actual recent trend backed by collected data from an evergreen topic or an AI-generated idea.
- Support ideas for creators who **have not uploaded a video yet**. A video file or YouTube Studio CSV must **not** be necessary to use this workflow.

**Illustrative ideas only, NOT live trend claims:**

- Gaming: a comparison or tutorial relating a newly popular game/update to low-end devices commonly used locally.
- Education: a Sinhala- or Tamil-friendly explainer on a difficult exam-related concept.
- Cooking: an accessible, budget-conscious take on a familiar Sri Lankan dish or technique.

These are examples of the kinds of suggestions the platform might produce. Real suggestions must use **fresh source data**, not invent current popularity.

### Goal 2 — Assess a prepared video before YouTube upload

**Problem:** A creator has made a video but does not know if its topic, packaging, opening, or pacing will likely attract and keep viewers.

**Product behavior:**

- Accept a **locally uploaded, finished video** or other supported pre-publish content, together with proposed **title, description, thumbnail, category, and language**.
- Optionally accept an **individually uploaded YouTube Studio / Analytics CSV export** containing the creator's own historical performance data.
- Analyze consistency between title and content, trend alignment, thumbnail/title attractiveness, hook/retention signals, and channel baseline where possible.
- Provide an **overall, approximate score or tier** and an understandable **breakdown of why**.
- Where truly validated outcome labels/models exist, provide approximate **CTR / 30-second retention / average watch percentage** estimates, with uncertainty and an explicit basis for comparison.
- Where such models do **not** exist, provide a clearly labeled **heuristic/content-readiness assessment**, **not fictional numerical CTR or retention forecasts**.
- Offer specific improvements the creator can try **before posting**.

**This is pre-upload analysis**. It is not a post-upload analytics dashboard, automatic YouTube uploader, or guaranteed view-count predictor.

---

## 3. Target users, market, and localization

### Primary audience

- Sri Lankan creators working primarily in **Gaming**, **Education**, and **Cooking**.
- Creators of different sizes, including **new or small channels** that lack substantial historical analytics.
- Creators producing content in **Sinhala, Tamil, and English**, including mixed-language titles/transcripts. The source report particularly calls out Sinhala NLP as an important localization problem; Tamil is part of the intended Sri Lankan multilingual audience, but the exact level of Tamil model support remains an implementation decision.

### Local context to account for

- Local audience interests may differ significantly from broad global YouTube trends.
- Category-specific behavior matters: fast entertainment in Gaming, trust and clarity in Education, and visual/demo appeal in Cooking.
- A recommendation must not assume a globally popular English video is automatically a strong Sinhala/Tamil video idea.
- Small channels should not automatically receive a poor grade because they have few subscribers or no CSV history.
- Creator relevance and usefulness matter at least as much as mathematical model complexity.

### Category boundaries

Initially support **only the three agreed project categories** in product flows and evaluation. YouTube's official category IDs and user-facing categories are **not necessarily a one-to-one mapping**; implement an explicit content-category taxonomy rather than assuming an official YouTube category alone identifies Gaming/Education/Cooking perfectly.

---

## 4. Expected user journeys

### Journey A — “I don't know what video to make”

1. Creator chooses category, preferred language, and optionally audience/topic preferences.
2. App reads the latest **cached and timestamped trend observations**.
3. App shows topics, momentum/freshness indicators, representative examples, and source links where permitted.
4. App proposes several **distinct, adaptable video ideas** derived from the evidence.
5. For a selected idea, show potential title angles, suggested hook, outline/format, and why it suits the creator's category.
6. Clearly show **when trend data was refreshed** and avoid pretending a stale trend is live.

**Result:** A creator can proceed from an empty idea to an actionable content plan without having prepared a video, shared a CSV, or connected a channel.

### Journey B — “I've made a video; should I publish it?”

1. Creator selects Gaming, Education, or Cooking; states language.
2. Creator supplies video file, proposed title, description, thumbnail, and optional transcript if available.
3. Creator may optionally upload their own YouTube Studio CSV for **personalized comparison**.
4. Modules A–E analyze applicable inputs; unavailable inputs trigger **honest degradation**, not made-up features.
5. Module F combines validated/available outputs into a readable report.
6. User sees approximate overall score/tier, strengths, concerns, suggestions, evidence, and reliability/limitations.
7. Creator can revise packaging/content and rerun the assessment.

**Result:** A grounded, actionable pre-publish review — not a guarantee of actual performance.

### Journey C — “I'm new and have no historical analytics”

1. Creator uses both workflows without a CSV.
2. App produces trend ideas and available **content-derived heuristic analysis**.
3. Channel-specific CTR deltas or precise retention estimates are shown as **unavailable** unless a legitimate, validated alternative model exists.
4. If defensible local/category benchmarks exist, use them as explicitly labeled **population references**, not as fake creator history.

### Journey D — “I have private CSV data but don't want to train someone else's AI”

1. Creator can optionally supply a supported CSV export **for the current analysis**.
2. The app parses available metrics and computes personal baselines if the export is sufficient.
3. Their data is used **only for the consented purpose** and according to a declared retention/deletion policy.
4. **Uploading a CSV does not equal agreeing to include it in a global training set.**
5. The product continues to work in a reduced mode if the creator opts out or uploads no file.

---

## 5. High-level six-module architecture

The source report's architecture has **six modules, labeled A–F**. Conceptually, A–E supply signals; F combines them for an explanation. **Module B additionally operates independently** to power the standalone idea-discovery goal requested by the project owner.

```text
                               ┌───────────────────────────────┐
                               │ Sri Lankan YouTube Creator   │
                               └──────────────┬────────────────┘
                                              │
                         ┌────────────────────┴────────────────────┐
                         │                                         │
              PATH 1: NEED NEW IDEAS                  PATH 2: HAVE A FINISHED VIDEO
                         │                                         │
              Creator preferences                         Video + metadata + thumbnail
                         │                                + optional transcript/CSV
                         ▼                                         │
             ┌──────────────────────┐       ┌───────────────────────┼──────────────┐
             │ B — Trend            │       ▼                       ▼              ▼
             │ Intelligence         │    A — Integrity          C — Packaging   D — Hook/
             │ + Idea Suggestions   │    & Honesty              & CTR signals   Retention
             └──────────┬───────────┘       │                       │              │
                        │                   └───────────────────────┼──────────────┤
                 Trend-led ideas                                   │              │
                 + freshness evidence                  B — Trend alignment    E — Channel
                                                               │       baseline/history
                                                               └──────────┬───────┘
                                                                          ▼
                                                              F — Fusion + Explainability
                                                                          │
                                                                  Pre-upload report
```

*Diagram expresses responsibility and data flow, not a mandatory runtime deployment layout. Modules can execute conditionally and in parallel where dependencies allow.*

| Module | Name | Key responsibility | Expected output |
|---|---|---|---|
| **A** | Integrity & Packaging Pre-Check | Compare title/description/transcript with video content | Content-match / misleading-packaging flags |
| **B** | Trend Intelligence | Collect category trends, suggest ideas, check video topic freshness | Recent trends, idea suggestions, trend relevance/freshness |
| **C** | Packaging / CTR | Analyze title and thumbnail for click appeal | Packaging diagnostics; CTR delta **only when valid** |
| **D** | Hook & Retention | Analyze first 30 seconds and full-video pacing/content signals | Hook/retention diagnostics; ECR@30s / NAWP **only when valid** |
| **E** | Channel History / All-Rounder | Estimate context and baselines from available channel history | Personal channel baseline or missing-data/cold-start status |
| **F** | Fusion + XAI + LLM Explanation | Combine A–E; produce final, comprehensible report | Overall assessment, reasons, priorities, confidence |

**Important:** Six modules describe the **intended functional architecture**, not six fully trained neural networks. Some MVP components can and should use deterministic rules, pretrained feature extractors, embeddings, and carefully bounded heuristics until supervised data becomes available.

---

## 6. Detailed module responsibilities and boundaries

### Module A — Integrity & Packaging Pre-Check

**Question:** *Does the proposed title/description honestly represent the video?*

- **Inputs:** title, description, transcript if accessible (Sinhala/English in the original design, extend as viable to Tamil), video duration and relevant extracted content cues.
- **MVP technique from source:** rules plus lightweight NLP / multilingual text similarity; a separately developed Sinhala-capable analysis path.
- **Responsibilities:** detect mismatches, unsupported claims, possible overpromising, and consistency of promised topic with actual content.
- **Outputs:** content-match/honesty indicators, flagged phrases, evidence, improvement guidance.
- **Category context:** trust issues are particularly important for Education and Cooking.
- **Critical distinction:** An honest title can be dull; a highly clickable title can be honest. **Do not combine honesty and curiosity into one undifferentiated “clickbait” judgment.** Module A assesses truthful alignment; Module C assesses appeal.
- **Interpretation caution:** The original document uses a clickbait/honesty score with *lower being better*. To prevent user confusion, explicitly name each direction (e.g., `misleading_risk: 0..100, lower_is_better` versus `content_alignment: 0..100, higher_is_better`). Do not silently reverse the original metric.
- **Without transcript:** Run only checks supported by metadata/content available; mark full content-match analysis partial/unavailable.

### Module B — Trend Intelligence **and Idea Discovery**

**Questions:** *What topics are recently attracting attention? What could this creator make next? How fresh is this video's topic?*

This module has **two product roles**:

**B1: Standalone discovery (Goal 1)**

- Regularly collect permitted **public** YouTube metadata and video/topic evidence relevant to Sri Lanka and the three project categories.
- Capture `observed_at`, `published_at`, locality/language cues, and sources so trends can be traced and freshness evaluated.
- Group overlapping videos/keywords into understandable **topics**, not only individual videos.
- Estimate trend momentum/freshness **only from actually observed time-series or defined snapshot-based proxy signals**.
- Generate original idea suggestions with creator-specific category and language context; avoid simply copying a trending creator's title or video concept word for word.
- Show links to representative public videos/data observations where appropriate.
- Distinguish **“popular now,” “recently rising,” and “evergreen”**; these are different claims requiring different evidence.

**B2: Pre-upload trend alignment (Goal 2)**

- Match the proposed title, transcript, or topic keywords to recent category trends.
- Explain whether the creator's planned topic appears timely, oversaturated, evergreen, or unsupported by current evidence.
- Return an alignment/freshness indicator and links or supporting observations.

**MVP technique from source:** scheduled YouTube Data API collection, stored small reference table, recency-weighted keyword or multilingual embedding similarity; Google Trends can be supplementary if appropriate. The document calls this a “scheduled scraper,” but **prefer compliant official APIs and respect usage terms, quotas, and attribution**. An API's `mostPopular` result should not be described as a comprehensive niche-specific trend ranking; classification, additional sampling, and transparent limitations are needed.

**Do not require:** user CSV, a fully uploaded video, massive vector database, real-time scraping, or GPU-heavy multimodal trend embeddings for the first version.

### Module C — Thumbnail + Title Packaging / CTR Signals

**Question:** *Would the proposed thumbnail and title attract appropriate clicks?*

- **Inputs:** thumbnail, title, content category, language, optional creator's historical median impression CTR from a compatible export.
- **MVP techniques proposed in report:** image features such as contrast, color, thumbnail text amount/density, faces/expressions, and title curiosity/hook features. Pretrained CV/NLP models can help extract these.
- **Outputs in all supported modes:** packaging evaluation and practical observations (e.g., hard-to-read thumbnail text, weak title clarity, potentially confusing promise).
- **Outputs only with scientifically adequate model/labels:** predicted **CTR change relative to a channel baseline**, rather than pretending an absolute click rate can be inferred from public views alone.
- **Category awareness:** what makes an effective Gaming thumbnail is not necessarily the same as what builds trust for an Education or Cooking channel.
- **Critical limitation:** CTR is measured from YouTube impressions and clicks and is generally **not exposed by public YouTube Data API metadata**. A view count or like count is **not** a CTR training label. An individual's CSV history can give a baseline if the correct metric is included; it does **not**, by itself, create a trained cross-channel CTR prediction model.

### Module D — Video Hook & Retention / ECR / NAWP

**Question:** *Is the opening likely to hold attention, and does the video maintain engagement through its runtime?*

- **Inputs:** video, the first ~30 seconds, sampled frames across the full video, duration, optional transcript and audio cues.
- **MVP technique proposed in report:** ~1–2 frames/second sampled from video; pretrained ResNet feature extraction followed by GRU/LSTM modeling of the sequence, with stronger multimodal models deferred.
- **MVP product outputs when no labels are available:** practical diagnostics on hook clarity, time to value, pacing, topic consistency, pauses, and structural changes — insofar as implemented analyzers can genuinely support those claims.
- **Research targets:** `ECR@30s` (share/continuation at the 30-second mark, definition to be finalized) and `NAWP` (normalized average watch percentage, definition to be finalized).
- **Data reality:** A pretrained ResNet extracts features; it does **not** independently predict retention. Training a reliable sequence-to-retention regressor requires usable, aligned retention labels from consenting creators.
- **Cold-start fallback:** descriptive hook/pacing guidance without fabricating numeric ECR/NAWP outcomes.
- **Important:** Audio/speech and transcript features are useful future enrichments, but the source's explicit MVP baseline is frame-based.

### Module E — Channel History / All-Rounder

**Question:** *What performance context can we fairly establish for this particular creator?*

- **Inputs:** optional creator-supplied Studio CSV; potentially subscriber count, previous video performance, category, historical CTR/watch time where available, release day/time, title length, and other legitimate metadata.
- **MVP technique proposed in report:** XGBoost/tabular baseline using compatible channel-level history and metadata, if an appropriate training set exists.
- **Outputs:** available historical medians/ranges, baseline reach context, and personalized comparison reference; prediction tier only if actually validated.
- **Key objective:** do not misread content quality purely from channel size. A small creator may have excellent material without historical reach.
- **If no CSV:** emit `channel_history_available: false`, treat history as missing, and use permitted transparent category references **only if such references were actually collected**.
- **If CSV is present:** recognize differences in Studio export format, column naming, periods, metric availability, aggregation, and units. Validate before computing medians.
- **Hard rule:** no private data should silently become shared training data.

### Module F — Fusion + Explainable AI (XAI) + Natural-Language Summary

**Question:** *Given the evidence we have, what should the creator know and improve before publishing?*

- **Inputs:** structured A–E module outputs; applicability status, evidence, uncertainty, and channel context.
- **MVP direction from report:** a lightweight late-fusion/regression layer **when reliable training labels exist**, paired with an LLM-generated plain-language narrative; a complex MMoE architecture is future work.
- **Core output:** one creator-facing report with an overall indicative score/tier, factor-level breakdown, strengths, potential weaknesses, recommended fixes, and uncertainty/limitations.
- **Example cross-signal insight:** “The title and thumbnail have strong curiosity features, but the opening takes too long to deliver on the promise.” This is a **potential expectation/retention mismatch**, not proof of a YouTube ranking penalty.
- **Explainability requirement:** the narrative must be based on **actual A–E results**, not invented observations. Prefer a structured findings object and use the LLM **to explain it**, not to manufacture unsupported metrics.
- **Missing information behavior:** combine only available supported signals; identify missing modules rather than assigning them arbitrary average scores.
- **Scoring nuance:** a 0–100 **pre-publish readiness score** can be implemented earlier than a genuine **predicted performance score**. Label these differently and never imply calibration if none exists.

---

## 7. Measurement definitions and uncertainty

The source document names three major pre-upload performance targets, but the project must agree on precise operational definitions before training or implementing numerical forecasts.

| Term | Intended meaning | Data required to validate | Important caution |
|---|---|---|---|
| **CTR** | Impressions click-through rate for the published video | Actual impression CTR from a properly matched YouTube Studio / Analytics export | Public views/likes are **not** CTR; forecast must define horizon and comparison baseline. |
| **ECR@30s** | Engagement continuation/retention at 30 seconds | Appropriately exported audience-retention data including 30-second observation or derivable curve | The exact name and operational definition must be frozen; not every CSV includes a retention curve. |
| **NAWP** | Normalized average watch percentage across the video | Reliable average percentage viewed or watch-time/duration data with matching definitions | Define normalization/clipping and handling of replays before computing. |
| **CTR delta** | Difference between forecast CTR and creator's historical median | Reliable personalized baseline **and** trained/validated method to estimate a change | A median is a baseline, not a predictive estimator by itself. |
| **Overall score** | User-friendly summary of observed pre-publish strengths/risks | Explicit score rubric and available module outputs | Decide whether it is a **readiness score** or empirically calibrated **outcome forecast**; these must not be conflated. |
| **Trend freshness** | How recent/relevant a topic is relative to cached observations | Time-stamped, category-relevant public trend snapshots | Not a forecast of future virality or a guarantee of audience demand. |

### Principles for any score

1. Explain its **meaning**, **scale**, and **direction** (higher/lower is better).
2. Show which modules contributed and whether any were unavailable.
3. Identify whether the score is **rule-based/heuristic**, **benchmark-informed**, or **supervised/model-validated**.
4. For true predictions, state the forecast window/target and use realistic uncertainty estimates derived from validation. **Never invent confidence percentages.**
5. Do not promise a specific view count, rankings, earnings, or YouTube recommendations.
6. An LLM response is an explanation mechanism, not evidence that a numerical prediction is accurate.
7. The app's scoring rubric, weights, thresholds, and calibration are **design decisions not finalized in the source document**. Keep them configurable and documented.

---

## 8. Data sources: what they can and cannot tell us

| Data source | Can help with | Does **not** reliably provide |
|---|---|---|
| **YouTube Data API v3 (public)** | Public titles/descriptions, published time, channel/category metadata, video statistics where accessible, thumbnails, certain popular/search results | Private impressions CTR, per-video audience-retention curves, individual creator Studio reports |
| **Scheduled local trend observations** | Topic groups, reference examples, observed freshness, category/geographic relevance and snapshot-based patterns | Definitive proof of tomorrow's trends; private engagement metrics |
| **Google Trends or similar permitted public signals** | Supplementary public search-topic interest | YouTube-specific CTR/retention labels or direct proof of YouTube recommendation behavior |
| **Public YouTube datasets (e.g., Kaggle)** | Public metadata experiments, engagement/visibility proxies, tabular baselines for views/popularity, pipeline development | Generally, authenticated creator CTR or audience-retention ground truth; guaranteed Sri Lankan category coverage |
| **Pretrained image/video/language models** | Extract visual/text features, embeddings, and some generic detections | Directly calibrated, Sri Lanka-specific CTR/ECR/NAWP predictions without valid outcome-label training |
| **BanClickThumb or similar research resources** | Potential support for title/thumbnail alignment or clickbait-related tasks; check dataset coverage, permissions, and task suitability | Automatically representative Sinhala/Tamil click behavior or private video-level CTR |
| **User-uploaded Studio CSV** | That consenting user's historical baselines and potentially validation labels if metrics/format support them | Automatic permission to train a global model; uniform presence of all performance columns |
| **Explicitly consented creator research pilot** | Potential local outcome labels for training/evaluating performance models | A large representative population unless size/selection bias are addressed |
| **Creator-uploaded video/thumbnail** | Pre-publish content and packaging features | How an actual audience will behave absent validated outcomes |

### Data privacy vs. model training — non-negotiable distinction

**There are three separate activities:**

1. **Single-user inference:** Creator uploads CSV to personalize **their report**. This does not require pooled model training.
2. **Local/personal baseline computation:** Use historic video medians/percentiles from that same creator, provided metrics and sample size are valid. This is personalization, not proof of a predictive learned model.
3. **Cross-user supervised training:** Aggregate aligned input videos/features with real post-publication CTR/retention outcomes **only if participation, collection, storage, and training usage are explicitly authorized** and the data quality is adequate.

Keep these activities distinct in the code, UX, consent rules, retention policy, and documentation. A creator's private CSV must **not** be automatically uploaded to a central training repository or included in other creators' model fitting.

### Is a Kaggle YouTube dataset enough?

**For the complete intended system: no, not by itself.** Public YouTube datasets may be useful for initial metadata analysis, code prototyping, popularity proxies, and possibly Module E experiments. They often contain views, likes, comments, titles, upload dates, and categories — **not** the private impression/retention labels required to supervise CTR, ECR@30s, and NAWP. Even a large global dataset may mismatch Sri Lankan **Sinhala/Tamil/English content in Gaming, Education, and Cooking**.

Before using any public dataset, check **license/allowed use**, collection method/date, represented countries/languages/categories, sample selection, missing fields, label meaning, and whether a comparable evaluation set exists locally. A large number of rows does not make labels suitable for the target task. Kaggle is a possible **supporting** resource, not proof of an accurate local predictor.

### Feasible training strategy given private CSV limitations

**Stage 0 — Meaningful app without custom outcome training**

- Build trend collection, categorization, freshness ranking, and evidence-backed idea recommendation.
- Build basic module A/C/D content checks with rules and permitted pretrained models.
- Parse optional CSV exports for **creator-specific benchmarks**, not for shared training.
- Produce transparent diagnostics and a **heuristic readiness score**. Leave metric-level performance forecasts unavailable if not validated.

**Stage 1 — Research baselines and local validation**

- Investigate relevant public datasets for **tasks they actually label** (e.g., view-related baseline or thumbnail-title consistency).
- Recruit a **small, explicitly consented** group of Sri Lankan Gaming/Education/Cooking creators for evaluation, carefully defining upload periods, sample sizes, and data handling.
- Create hand-labeled evaluation items for misleading title/content pairs (particularly Sinhala) and relevance of idea recommendations.

**Stage 2 — Optional supervised prediction**

- Only if enough suitable labeled creator data is legally and practically available: train simple category-conditioned CTR/retention baselines and compare against naive baselines.
- Use a **time-appropriate** split and preferably creator-disjoint evaluations to avoid misleading accuracy from leakage.
- Calibrate uncertainty, validate on local held-out creators/videos, and expose forecasts only for metrics with adequate evidence.
- If this stage is not feasible, **do not misrepresent the Stage 0 heuristic product as an empirically trained CTR/ECR/NAWP predictor**.

**Private individual CSVs remain useful** even if the team can never collect a pooled training corpus. They help explain the creator's own normal performance and give more personalized recommendations.

---

## 9. Data and analysis flows

### Trend discovery flow

```text
Permitted public YouTube/topic data
        ↓
Scheduled fetch and quota-aware cache
        ↓
Validate timestamps + language/region/category relevance
        ↓
Normalize and deduplicate videos/topics
        ↓
Topic grouping + recorded momentum/freshness signals
        ↓
Generate evidence-grounded idea candidates
        ↓
Rank/filter for creator category, audience, language
        ↓
Show ideas + reasons + representative links + data timestamp
```

### Pre-upload flow

```text
User video + title + description + thumbnail + category + language
                                 │
                        Optional transcript
                        Optional private CSV
                                 │
                  Parse / validate / extract features
                                 │
         ┌───────────────┬────────┴────────┬───────────────┐
         A               B                 C               D               E
    Content match    Trend alignment  Thumbnail/title  Hook/retention  Personal baseline
         └───────────────┴────────┬────────┴───────────────┴───────────────┘
                                  ↓
                        F — evidence-aware fusion
                                  ↓
                Scores/tiers + diagnostic flags + explanations
                                  ↓
                       Improvement recommendations
```

### Example canonical per-module result shape (suggested interface, not implemented)

```json
{
  "module": "C",
  "status": "completed",
  "analysis_mode": "heuristic",
  "category": "Gaming",
  "signals": [
    {
      "name": "thumbnail_text_readability",
      "assessment": "needs_improvement",
      "reason": "Small thumbnail text may be difficult to read on mobile",
      "evidence": "Detected densely packed small text in the image"
    }
  ],
  "predictions": {
    "ctr_delta": null
  },
  "missing_requirements": [
    "No validated CTR-delta prediction model available"
  ],
  "model_or_ruleset_version": "to_be_defined"
}
```

This illustrative response makes a **critical distinction**: the module can provide useful feedback while correctly returning `null` for a metric it cannot validly predict.

### Example combined report shape (suggested interface, not implemented)

```json
{
  "project_category": "Education",
  "localization": { "audience_region": "LK", "content_language": "si" },
  "analysis_type": "pre_upload_readiness",
  "overall": {
    "score": null,
    "label": "Assessment in progress / score rubric not yet defined",
    "calibrated_future_performance_prediction": false
  },
  "metrics": {
    "predicted_ctr": null,
    "predicted_ecr_at_30_seconds": null,
    "predicted_nawp": null
  },
  "module_status": {
    "A": "completed",
    "B": "completed",
    "C": "completed",
    "D": "partial",
    "E": "not_available_without_valid_history"
  },
  "findings": [
    { "severity": "medium", "finding": "Title promise may not appear in the opening", "source_module": "A" }
  ],
  "recommendations": [
    { "priority": 1, "action": "Make the promised lesson objective explicit in the opening", "source_modules": ["A", "D"] }
  ],
  "limitations": [
    "No validated numeric retention forecasting model",
    "No compatible creator history was provided"
  ]
}
```

When the team defines a readiness scoring rubric, a numeric `overall.score` may be populated and explicitly labeled **heuristic**, even if forecast metrics remain `null`. Do not display this illustrative JSON as measured results or claim that these endpoints/data contracts already exist.

---

## 10. What makes trend recommendations useful

For each recommended video idea, aim to show the following where evidence supports it:

- **Idea title / topic:** brief and understandable.
- **Why now:** timestamped data or signals showing recent relevance, with a source link or summary.
- **Category / local fit:** why it may resonate with Sri Lankan Gaming, Education, or Cooking audiences.
- **Suggested angle:** how to make the idea original instead of merely copying the source video.
- **Opening hook:** a possible first 10–30 seconds or viewer promise.
- **Format:** explain/tutorial, comparison, challenge, demonstration, recipe walkthrough, etc.
- **Language suitability:** Sinhala/Tamil/English framing where supported.
- **Freshness classification:** observed new/rising/steady/evergreen with a last-refreshed timestamp.
- **Evidence limitations:** small sample, global-only signals, stale data, or unverified category inference.

**Never present an LLM-invented idea as a measured “latest trend.”** The idea generation may be creative, but the *trend evidence* must come from fetched/recorded sources.

Ideas should remain useful if no reliable “rising” metric can be calculated: the app can still present recently popular observations, relevant public examples, and well-labeled exploratory concepts.

---

## 11. What makes a pre-upload report useful

A report should answer, in plain language:

1. **What is the overall assessment?** What does the score mean, and how reliable is it?
2. **Is the topic timely?** Relevant recent trend evidence or honest absence of evidence.
3. **Does the packaging communicate an attractive but accurate promise?** Keep A (truthfulness) separate from C (click appeal).
4. **Will the opening likely establish value quickly?** Ground recommendations in visible/supported content signals, not speculative viewer psychology stated as fact.
5. **What is the channel context?** If a valid private CSV was supplied, make the personal baseline clear.
6. **What should change first?** Prioritized, concrete edits to title, thumbnail, opening, structure, or topic positioning.
7. **What could not be evaluated?** State unavailable modules/metrics, sparse history, unsupported language, or stale trends.

**Example report tone (illustrative, not a real prediction):**

> “The tutorial topic matches some recent Education interest, and the title communicates the subject clearly. However, the opening does not explain what viewers will learn until later in the video. Consider showing the final learning outcome earlier. This assessment is based on available content signals; we cannot reliably estimate your CTR or 30-second retention without validated prediction models and appropriate outcome labels.”

Avoid false certainty such as “YouTube will penalize this video,” “This will get 50,000 views,” or “CTR will be 9.2%” without documented, evaluated prediction capability.

---

## 12. Sensible product areas (conceptual, not fixed UI/stack)

The anticipated application will likely need:

- **Home/dashboard** — two clearly visible starting actions: “Find Video Ideas” and “Analyze My Video.”
- **Trend explorer** — category, audience/language filters, evidence-backed recent topic cards, recency and relevance explanations.
- **Idea detail** — suggested concept, title directions, format, opening hook, evidence, and potential creator-specific customization.
- **Pre-upload form** — metadata, video, thumbnail, optional transcript, optional private CSV.
- **Analysis state** — upload/validation errors, progress or individual module status, and graceful cancellation/retry policies.
- **Report view** — overall assessment, module breakdown, diagnostic flags, ranked actions, limitations, optional personal benchmark.
- **Privacy controls** — simple explanation of why CSV/video is requested, how it is processed, and available deletion/retention controls.

Keep trend exploration available **without forcing account creation, channel access, CSV upload, or video upload** unless a separately agreed product/security requirement demands it.

### Logical services — not mandatory microservices

- Public trend ingestion and cache.
- Trend/topic processing and idea suggestion.
- Creator input/upload validation and transient media processing.
- Optional YouTube Studio CSV parser and private baseline calculator.
- Module analyzers A–E.
- Evidence-aware fusion/report generator F.
- Privacy/security, provenance, logging, and evaluation support.

**Do not invent a mandatory frontend, backend, database, vector store, hosted AI provider, or cloud platform.** Choose/confirm the technology stack after inspecting the real repository and the team's constraints.

---

## 13. Practical constraints and safe fallbacks

| Situation | Expected behavior |
|---|---|
| No private CSV | Analyze public/content signals; do not invent channel medians or metric forecasts. |
| New/small channel | Explain cold-start limitation; avoid treating subscriber count as content quality. |
| Studio export lacks CTR | Do not treat view count/likes as CTR; mark CTR baseline unavailable. |
| Studio export lacks retention series | Do not derive ECR@30s from unrelated aggregate fields. |
| Unsupported CSV format | Show requested fields/example accepted export; do not silently misparse. |
| No transcript | Run reduced checks where possible; state unsupported checks. |
| Sinhala/Tamil text poorly supported by a chosen model | State language support limits; evaluate separately or fall back to conservative behavior. |
| YouTube quota/access failure | Use clearly timestamped last-known trends if permitted; indicate staleness. |
| No trend evidence for a niche | Present exploratory/evergreen ideas separately, not counterfeit trends. |
| Slow/large uploaded video | Enforce configurable limits, responsible asynchronous processing, and informative status. |
| No trained outcome models | Offer heuristic readiness feedback; leave quantitative future-performance fields unset. |
| Conflicting module signals | Explain the conflict and evidence instead of forcing a confident, one-line verdict. |
| A model is added later | Record model version, training labels, evaluation scope, applicability, and uncertainty. |

---

## 14. Data governance and responsible handling

This app processes **unpublished creator material** and may process **private commercial analytics**. Treat both as sensitive project data.

- Obtain **explicit user permission** for access to uploaded videos, thumbnails, transcripts, and analytics files, with clear purpose statements.
- Do not assume that a CSV upload permits retaining raw data indefinitely or training global models.
- Prefer **on-demand, isolated creator-level processing**, minimal collected fields, and a documented retention/deletion policy.
- Avoid exposing filenames, video contents, analytics values, or creator identifiers in logs, prompts, public dashboards, or shared caches.
- Segregate **public trend caches** from **private creator data**.
- Validate media type, file size, CSV schema, and untrusted content. Handle errors gracefully.
- Verify rights/licenses/API terms before storing, replicating, or using third-party public media to build training datasets.
- If the team runs a pilot for ML training/evaluation, document what creators consented to share, for what purpose, and how they can withdraw where applicable.
- Prevent data leakage: no use of the target video's post-publication views, CTR, watch time, or audience-retention curve as **pre-upload features**.

These are design requirements/guardrails, not a statement that a compliance or security system is already implemented.

---

## 15. What is realistic for an MVP

The report explicitly scopes the project to what a **four-person student team** can demonstrate. Favor an end-to-end, honest system over a sophisticated model with nonexistent labels.

### Strong MVP deliverables

- Working **Sri Lanka-focused trend ingestion** for the three categories, with a refresh schedule and recorded provenance.
- Usable **idea discovery** with creative suggestions linked to observed trend evidence.
- Pre-upload input flow accepting core video/metadata/thumbnail and optional creator CSV.
- Basic **A: title/transcript/content consistency** checks where supported.
- Basic **C: thumbnail/title packaging feedback** using feature extraction/heuristics.
- Basic **D: hook/pacing analysis** (do not claim calibrated retention without labels).
- **E: creator history summaries** from compatible, individually supplied exports.
- **F: clear, user-friendly, evidence-grounded final report** combining supported signals and identifying unsupported ones.
- A defined **heuristic readiness score** (if the team agrees its meaning and rubric) or descriptive performance tier, plus explanations.
- Basic local evaluation: recommendations quality and content assessment usefulness with Sri Lankan test users; metric prediction accuracy only where suitable ground truth exists.

### Advanced components mentioned by the report but **not prerequisites**

- Temporal retrieval-augmented trend intelligence with full live multimodal vector database (M3TR-style).
- High-compute multimodal video models such as VideoLLaMA2 / Qwen2.5-VL.
- Full Multi-gate Mixture-of-Experts architecture for fusion.
- Continuous production-scale retraining and concept-drift response.
- Highly accurate numeric CTR/ECR/NAWP forecasting without a substantial validated labeled local dataset.

**Rationale:** the scientific claims and privacy assumptions need to be compatible with the data the team can realistically obtain. Simpler, testable methods are preferable to unsupported labels such as “trained AI predicts your CTR.”

---

## 16. Suggested build roadmap (aligned to source, with clearer emphasis on Goal 1)

### Milestone 1 — Foundation and data reality

- Confirm product definitions for both workflows and module responsibilities.
- Choose actual stack according to available code/team resources.
- Establish permitted public trend data pipeline and caching.
- Prototype metadata, CSV format validation, private baseline extraction, and Module A.
- Define precise measurement labels and dataset feasibility **before** planning supervised training.
- Start ethical recruitment/consent conversations early if pilot data is needed.

**Exit:** real, timestamped public trend data; basic A/E output on supported test inputs; explicit missing-data behavior.

### Milestone 2 — Useful standalone idea discovery + content analyzers

- Implement trend explorer and original idea recommendations.
- Develop B's topical freshness check for prepared video metadata.
- Implement basic C thumbnail/title features and D sampled-video/hook features.
- Validate Sinhala content processing early; establish realistic Tamil support status.

**Exit:** users can get relevant content suggestions and observable, useful pre-upload diagnostics even without CSV data.

### Milestone 3 — Integration and explainable report

- Join A–E outputs through module F; trace every claim to evidence.
- Implement status/confidence/missing-input logic and any agreed heuristic score rubric.
- Add prioritized actionable suggestions and useful report UX.
- Only add trained outcome predictions for metrics that have passed evaluation.

**Exit:** complete demo of **both** user workflows; no fabricated accuracy claims.

### Milestone 4 — Evaluation and polish

- Assess whether recommended ideas are relevant, original, and useful to local creators.
- Evaluate A against manually labeled honest/misleading examples.
- If consented labels exist, evaluate CTR-delta, ECR@30s, and NAWP on held-out data using MAE/RMSE and simple baselines.
- Collect creator feedback on explanation clarity and actionability.
- Polish accessibility, error handling, privacy, performance, and reliability.

**Exit:** reproducible demo, candid limitations section, and evaluation evidence suited to actual implemented features.

---

## 17. Evaluation questions and research contribution

### Goal 1 — Idea discovery

- Are the suggested ideas **relevant** to Sri Lanka and the chosen category?
- Do they feel **fresh** when the system calls them fresh, according to timestamped observations?
- Are ideas original/adaptable rather than mere copied titles?
- Do creators report that recommendations helped them overcome idea blocks?
- Are locality and language inference errors tracked?

### Goal 2 — Pre-upload analysis

- Are misleading packaging flags reasonably accurate on manually reviewed examples?
- Do thumbnail/title/hook recommendations match observable content and help creators make specific changes?
- If trained metrics exist: how do they perform relative to naive category/channel medians, using held-out creators/videos and appropriate temporal validation?
- Can users distinguish **observed quality signals** from **learned predictions**?
- Do creators understand why they received a score, and can they act on it?

### Intended novelty (as argued in the source document; not an externally verified priority claim)

- Sri Lanka/local-language adaptation, especially Sinhala text/transcript checks.
- Category-conditioned analysis across Gaming, Education, Cooking.
- Honest-content alignment separate from click appeal.
- Cold-start-aware personalization relative to real history when available.
- Explainable pre-publish guidance rather than opaque score alone.
- Operationally manageable recency-sensitive trend intelligence.
- With the project owner's clarification: **standalone trend-led idea discovery** integrated with pre-upload video guidance.

---

## 18. Key risks to remember

1. **Outcome-label scarcity:** private CTR and retention data are not in ordinary public YouTube datasets. This is the most serious risk to performance prediction claims.
2. **Domain shift:** global or English-only data may not generalize to Sri Lankan Sinhala/Tamil/English audiences.
3. **Missing/heterogeneous CSV fields:** user exports may be incomplete or incompatible, especially for 30-second audience retention.
4. **YouTube API quotas/terms:** scheduled pulls, caching, and transparent freshness are necessary.
5. **Compute constraints:** frame extraction and video models can be costly for student infrastructure.
6. **Trend ambiguity:** popularity, recently rising interest, and creator-topic relevance must not be equated.
7. **XAI hallucination:** generated reports must never invent measurements or unsupported content observations.
8. **Privacy:** unpublished media and private Studio data require careful handling.
9. **Scope creep:** do not silently turn an MVP into a full production recommender or large-scale ML research platform.
10. **Score interpretation:** a rule-based readiness score is not a validated forecast of YouTube performance.

---

## 19. Product and coding-agent guardrails

When acting as the coding agent for this repository:

1. **Protect the product's two goals.** Always support both idea discovery and pre-upload assessment in plans and architecture; do not relegate trend discovery solely to video scoring.
2. **Preserve the six-module mental model** (A, B, C, D, E, F), even if the implementation starts with stubs, simpler logic, or fewer deployable services.
3. **Use real repository evidence.** This file describes intent; inspect code, project configuration, dependencies, tests, environment variables, and current feature status before assuming something exists.
4. **Do not make up models, datasets, test metrics, API keys, endpoints, scores, or measurements.** Mark proposed and unavailable pieces explicitly.
5. **Do not treat creator CSV upload as global training consent.** Default to creator-specific inference/baselining.
6. **Do not pretend Kaggle public views/likes train private CTR or retention prediction.** Verify actual outcome labels before choosing a loss function or claiming supervised accuracy.
7. **Keep useful fallbacks.** A user should get value from trends and available content checks even if they have no CSV or channel history.
8. **Every explanation must be traceable to module outputs.** Add provenance/status fields where useful and avoid unsupported causal claims about YouTube's algorithm.
9. **Be precise about local relevance and language support.** Never assume all videos with `regionCode=LK` are actually Sri Lankan-language or locally targeted, nor that a multilingual encoder is already reliable in Sinhala/Tamil.
10. **Prefer manageable MVP methods first.** Scheduled API data, caches, rules, pretrained encoders, and optional validated tabular baselines are favored over mandatory high-compute architectures.
11. **Do not hardcode unresolved decisions.** Expose/configure scoring semantics, metric horizons, category mappings, data retention choices, and language support after team agreement.
12. **Ask before changing fundamental scope.** Examples: removing an entire module, turning the project into post-upload analytics only, making user CSV compulsory, or claiming quantitative forecast accuracy absent validation.
13. **Keep user-facing labels scientifically honest.** Prefer “estimated readiness,” “trend evidence,” “channel benchmark,” “observed signal,” or “experimental prediction” as appropriate.
14. **Protect private user inputs and abide by permitted data-source terms.**
15. **Avoid claiming full product completion from a demo.** Track implemented, partially implemented, proposed, and future features separately.

### Interpretive priority when project materials differ

1. The **most recent explicit instructions from the project owner** determine product goals and scope.
2. This `PROJECT_CONTEXT.md` summarizes those goals and the uploaded source report, including identified caveats.
3. The source report documents the original research architecture and suggested techniques; it is **not** proof of implementation or labeled-data availability.
4. The actual repository reveals what has really been built. If code and context conflict, inspect and ask rather than silently rewriting the goal.

---

## 20. Open decisions — do not secretly assume answers

The following need team discussion or empirical validation:

- [ ] Official project name/branding and final public description.
- [ ] First release languages and exact Sinhala/Tamil support quality targets.
- [ ] Definition of “Sri Lankan trend” (region signal, channel location, language, target audience, topic relevance, or weighted combination).
- [ ] Trend collection frequency, age cutoff, momentum proxy, API quota allocation, and data-usage permissions.
- [ ] Whether to support shorts, long-form videos, or both for MVP; video size/length constraints.
- [ ] Precise operational definitions and measurement windows for CTR, ECR@30s, and NAWP.
- [ ] Which types of YouTube Studio CSV exports are acceptable and which analytics fields are truly present.
- [ ] Overall score: readiness vs calibrated forecast, score formula, module weights, category-specific weighting, minimum inputs, and confidence display.
- [ ] Whether and how to collect a research pilot dataset with separate training consent.
- [ ] Privacy, storage location, retention periods, deletion controls, and third-party AI service usage.
- [ ] Model selection based on local validation, compute budget, available labeled outcomes, and language performance.
- [ ] Exact UI/backend/database/hosting architecture and integration milestones.
- [ ] How to distinguish videos/topics from actual trending data versus exploratory evergreen suggestions.
- [ ] Acceptance thresholds for meaningful trend quality and prediction accuracy.

These are questions to **resolve**, not gaps to fill with confident guesses.

---

## 21. Minimum acceptance criteria for the intended concept

A solution represents this project well if all of the following are true:

- A Sri Lankan creator can browse **Gaming, Education, or Cooking** ideas without needing to upload anything.
- Recommended ideas connect to **actual collected and timestamped trend observations** or are clearly labeled as creative/evergreen suggestions.
- The creator can supply a **prepared video + title/description/thumbnail** and get a meaningful pre-publish assessment.
- The design preserves the **A–F six-module breakdown** and F's evidence-backed explainability.
- An optional private CSV can enhance channel-level context, but the product is not broken without it.
- Public data and Kaggle datasets are **not mislabeled** as ground truth for private CTR/retention outcomes.
- The report explains both **what to improve** and **why**, including uncertainty and missing evidence.
- Performance numbers appear **only if their basis and evaluation justify them**; otherwise the product uses properly labeled heuristic guidance.
- No feature relies on the false assumption that YouTube's internal ranking rules are fully known or reproducible.

---

## 22. Source notes and terminology

**Source:** `My part.docx`, *AI-Powered Pre-Upload Performance Prediction for Sri Lankan YouTube Content Creators*, August 2026.

Relevant source sections:

- §§1–3 — Sri Lankan creator need, pre-upload cold start, Gaming/Education/Cooking focus, languages.
- §§5–8 — six-module architecture, per-module responsibilities/inputs/outputs, explanation-centered approach.
- §§9–10 — proposed resources, critical consented CTR/retention label gap, YouTube API/CSV/public dataset sources.
- §§11–13 — future research extensions, quantitative/human evaluation, four-stage roadmap.
- §§14–15 — four-person student-team planning and key implementation risks.

**What this file adds or adjusts based on the owner's message:**

- Elevates **standalone trend-to-idea recommendations** to a first-class goal, rather than treating trends mostly as a score for an already-made video.
- Explicitly treats separately uploaded creator-owned CSVs as **private personalization inputs by default**, not assumed shared training data.
- Clarifies that public Kaggle datasets are unlikely to provide the **private label variables** required for CTR, 30-second retention, or average watch percentage supervision.
- Adds a cautious MVP path centered on honest, useful **heuristic guidance** until models are supported by consented labeled data.
- Treats **future performance predictions** and **readiness assessments** as different output types to avoid misleading users.

### Glossary

- **Pre-upload / pre-publish:** Analysis before a video's publication; the system has no early post-publish engagement signal for that specific video.
- **CTR:** YouTube impressions click-through rate, not simply views divided by followers or impressions invented from view counts.
- **ECR@30s:** Source report's 30-second engagement continuation/retention target; exact export and definition need confirmation.
- **NAWP:** Source report's normalized average watch percentage; exact formula and required observed label need confirmation.
- **XAI:** Explainable AI — structured reasons that support the product's guidance.
- **Cold start:** No previous creator/video performance data usable for personalization.
- **Domain-conditioned:** Analysis/scoring adapted to Gaming, Education, or Cooking rather than a single universal threshold.
- **Late fusion:** Combining outputs from separate analyzers/models into a final assessment/report.
- **Ground truth:** Measured creator performance outcome used for legitimate model evaluation/training, not a proxy merely correlated with it.
- **MVP:** Minimum viable product, with scope deliberately compatible with a student team's time, data, and compute limits.

---

## Final instruction to any AI coding agent

**We are building a tool to help Sri Lankan Gaming, Education, and Cooking creators answer two questions: “What should I create next?” and “How prepared is my finished video to perform, and what should I improve before posting?”**

Preserve both goals and the six-module concept. Start with grounded trend evidence and useful explainable analysis. Treat creator CSVs as optional private inputs. Treat numeric performance prediction as an **empirical research capability that must be earned by valid data and evaluation**, not as something an LLM, generic pretrained model, or Kaggle views dataset automatically solves.
