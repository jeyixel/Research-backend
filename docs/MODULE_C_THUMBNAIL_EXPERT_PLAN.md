# Module C — Thumbnail Expert
## Research Notes, Architecture, Training Plan, and Implementation Roadmap

**Project:** AI-Powered Pre-Upload Performance Prediction for Sri Lankan YouTube Content Creators  
**Status:** Data collection in progress; Module C implementation is the next major step  
**Scope:** Gaming, Education, and Cooking; Sinhala, Tamil, English, and mixed-language creators  
**Document purpose:** A practical reference for implementation, experiments, AI coding agents, and panel discussions  
**Prepared:** 20 October 2026

> **Core decision:** Build an evidence-informed **Thumbnail Expert** that analyzes a proposed thumbnail and title, retrieves relevant examples, and learns patterns **associated with above- or below-baseline video views**. Do **not** claim that public view counts reveal true click-through rate (CTR), or that the model can establish why people clicked.

---

## 1. What we are trying to build

A creator provides a **proposed thumbnail**, **title**, and **video category** before publishing. Module C should:

1. Measure understandable visual properties of the thumbnail (e.g., contrast, text coverage, face count).
2. Represent its visual content with **pretrained CLIP image embeddings**.
3. Compare the image with the proposed title (semantic alignment) and with similar thumbnails in the collected corpus.
4. Learn whether thumbnail/title characteristics are **associated with relative video view performance** in historical public data.
5. Return **specific, appropriately cautious recommendations**, with comparable historical examples where available.
6. Eventually, if creators supply their private YouTube Analytics/Studio data, extend the module to **actual CTR prediction relative to a creator's historical CTR**.

**Product target:** The creator should receive a practical analysis of what the thumbnail communicates,
how it compares with relevant historical examples, what they could test or improve, and a model-based
relative-performance estimate only after the model proves reliable. Training classifiers offline is a
research step; connecting a validated model to the upload API is a separate implementation milestone.
Historical public views cannot establish why an individual thumbnail succeeded or supply a defensible
"virality score." If the evidence for a numeric estimate is weak, the product should say so and still
give useful, evidence-grounded design feedback.

**Recommended research question for the public-data MVP:**

> Can visual and semantic properties of thumbnails and titles help predict which videos outperform their channel's typical views, within comparable content domains?

**Not the MVP claim:** “We can calculate thumbnail CTR from public YouTube views.”

### What this module is — and is not

- **It is:** A thumbnail/title *packaging analysis* component, using pretrained representations, engineered features, historical evidence, and a small supervised model where justified.
- **It is not:** A guaranteed viral-thumbnail generator, a direct reconstruction of YouTube's recommendation algorithm, or a causal proof that a particular design feature caused extra clicks.
- **Relationship with other modules:** Module C analyzes **packaging**. Module A checks **honesty / content match**. Module B examines **trends**. Module E examines **channel-reach baselines**. Module F combines results; avoid conflating their responsibilities.

---

## 2. The most important correction: public views are not CTR

### Actual click-through rate

For the YouTube impression-based metric:

\[
\mathrm{Impressions\ CTR}(\%) =
\frac{\text{Views from registered thumbnail impressions}}{\text{Registered thumbnail impressions}}
\times 100
\]

**Note:** The numerator is *views originating from counted impressions*, **not necessarily all video views**. Not every view comes from a registered thumbnail impression; impressions themselves depend heavily on distribution by YouTube.

**Illustrative example:**

| Metric | Video A | Video B |
|---|---:|---:|
| Registered impressions | 1,000,000 | 20,000 |
| Views from registered impressions | 40,000 | 3,000 |
| Impression CTR | **4%** | **15%** |

Video A attracted **more views from impressions** but had **lower CTR**. Thus:

- `views` alone **cannot** recover actual CTR.
- `views / subscribers` is **not** CTR either.
- Views may come from search, recommendations, external sources, loyal viewers, topic demand, and time spent accumulating views.
- Public YouTube Data API metadata does **not** supply an arbitrary channel's CTR or thumbnail impression counts.
- Real CTR modeling needs creator-consented Analytics/Studio records and correctly paired thumbnails/titles.

**Wording for the panel:** “We use channel-normalized view performance as an *observational proxy*, not an estimate of the video's actual click-through rate.”

---

## 3. What the current data collector gives us

The repository's `data-collector/README.md` and `data-collector/build_training_table.py` describe a public-data corpus and an already-implemented training-table builder.

### Collection workflow documented in the repository

```text
Discover and approve channels
    -> Collect public channel/video metadata (YouTube Data API)
    -> Download thumbnails
    -> Check coverage
    -> Build data/training_table.csv
```

Existing file locations and scripts include:

- `data-collector/yt_collector.py` — candidate discovery, collection, thumbnail downloads, statistics.
- `data-collector/build_training_table.py` — video filtering, performance targets, historical channel features, and folds.
- `data-collector/data/yt.db` — local collected-data database once populated.
- `data-collector/data/thumbnails/<video_id>.jpg` — downloaded thumbnails (README indicates 640 × 360).
- `data-collector/data/training_table.csv` — generated model-ready table.

The README's **target** is approximately **20,000–30,000 videos** over **40–60 channels in each category**, with varied channel sizes and languages. **This is a collection target, not a claim that the dataset already contains that many examples.**

### Particularly important existing columns

| Column | Intended use |
|---|---|
| `thumb_path` | Locate the thumbnail image |
| `title` | Title text supplied to Module C |
| `category` | Gaming, education, or cooking |
| `title_script` | Helpful language/script diagnostic; Latin script can include romanized Sinhala |
| `y_rel_neighbors` | Existing relative-view-performance target for Module C |
| `y_rel_prev` | Alternative target using only earlier video comparisons |
| `y_rank_in_channel` | Channel-relative ranking target |
| `fold` | Predefined channel-level fold (0–4) for evaluation |
| `age_days`, `published_at`, `views` | Data auditing, target interpretation, and bias checks |
| `channel_id` | Grouping, target construction, and leakage-safe validation **only**, not a Module C input |
| `subscribers`, `prev_*` | Intended for Module E and/or auditing; **exclude as Module C predictive inputs** |

### Filters currently in the builder

- Video at least **30 days old** by default.
- Duration greater than **180 seconds** by default.
- At least **15 videos per channel** by default.
- Neighborhood window parameter of **10 videos** on each side where available.

These filters help, but **do not** make views directly comparable across video ages, topics, or periods.

> **Respect the existing design rule:** Module C predictive inputs should be thumbnail, title, and category (plus features extracted from them). Do not feed channel ID, subscribers, channel history, raw views, labels, or post-publication engagement metrics into Module C. Channel IDs can still be used *offline* to construct labels and splits.

---

## 4. The proposed public-data target: relative view performance

A raw count of 100,000 views means something different for a small cooking channel and a huge gaming channel. Comparing a video against its channel's usual outcomes is more meaningful than comparing raw views across all channels.

The existing script defines:

```text
log_views_i = log(1 + views_i)

y_rel_neighbors_i = log_views_i
    - median(log_views of up to 10 neighboring uploads before/after video i)
```

Higher `y_rel_neighbors` means the video earned more views relative to neighboring uploads on that channel; lower means fewer. The logarithm limits the domination of massive view-count outliers.

**Illustrative example:** If one video's views are 65,000 and its neighboring baseline is around 15,000, it substantially exceeds that baseline. That makes its thumbnail/title an interesting case to analyze; it does **not** establish that its thumbnail caused the success.

### Two workable learning targets

**Option A — regression:** Predict the continuous `y_rel_neighbors` value. Evaluate using MAE or RMSE and compare against always predicting zero.

**Option B — classification (recommended first MVP):** Define `outperformed = 1` when `y_rel_neighbors > 0` and `0` otherwise. Predict whether the video is above or below its local baseline. Evaluate with ROC-AUC, balanced accuracy, calibration, and a majority-class baseline. If the threshold produces noisy near-zero labels, experiment with a neutral/uncertain band, e.g. discard or separately report outcomes close to zero; state the threshold and how many rows are excluded.

**Important nuances:**

- `y_rel_neighbors` uses **future neighboring uploads to construct a retrospective label**. That is acceptable for an offline descriptive comparison, but not an input available when a new video is being published. Never show a new creator's *true* future-relative outcome as if known at upload time.
- `y_rel_prev` (provided by the existing code) compares against **past uploads only** and may be more appropriate for future prospective evaluation. Compare both definitions experimentally.
- Both targets currently use view counts **as of collection time**. Videos of different ages have unequal accumulation windows. A much better later target is **views measured at a fixed horizon** (e.g., 30 days after upload), relative to a fair past-channel baseline available by that date.
- Current downloadable thumbnails and titles may differ from those that were shown when historical views were accumulated. This creates **historical image/title mismatch** that cannot reliably be corrected with a single present-day snapshot.
- A predicted *relative performance* score must be labeled as such, **not CTR, causal thumbnail quality, or expected view uplift from a redesign**.

---

## 5. Why CLIP is useful — and where it stops

**CLIP (Contrastive Language–Image Pretraining)** is a pretrained image/text representation model. It maps images and text into comparable numerical embedding spaces.

In straightforward terms:

- **Image encoder:** Converts a thumbnail into a vector of numbers representing visual-semantic content.
- **Text encoder:** Converts the title into a vector, where the model supports the title's language well.
- **Similarity calculation:** Measures how semantically aligned the image and title appear (often cosine similarity after normalization).
- **Nearest-neighbor retrieval:** Finds visually/semantically related historical thumbnails by comparing image embeddings.

**CLIP does not directly predict CTR.** Neither a CLIP similarity score nor a visually attractive embedding is, by itself, evidence that viewers were more likely to click.

### A useful separation of responsibilities

| Component | Question it can help answer | What it cannot establish |
|---|---|---|
| CLIP image embeddings | What kinds of scenes/objects/topics does the thumbnail resemble? | Whether that composition caused extra clicks |
| Image-title similarity | Does the thumbnail look broadly relevant to the title? | Whether the title is fully honest about the video's contents |
| Handcrafted features | How bright, saturated, text-heavy, or face-heavy is it? | Whether high contrast universally improves outcomes |
| Historical neighbor retrieval | Which similar cases were above/below their channel baselines? | That similar visuals had the same exposure or audience |
| Supervised model | Are thumbnail/title features statistically associated with relative views? | Causality or guaranteed performance for a new upload |

### Language caution

Your creators may use **Sinhala, Tamil, English, or romanized Sinhala**. A standard English-oriented CLIP text encoder may be unreliable for the local-language titles. Evaluate by language/script. Possible future alternatives include a validated multilingual CLIP/text embedding pipeline or careful title translation, but do **not** assume it works without testing. CLIP image-only embeddings remain useful for retrieval even when title embeddings are weak.

---

## 6. Proposed Module C architecture

```text
                      HISTORICAL TRAINING / INDEXING

data/training_table.csv + thumbnail files
                |
      [Data checks + image loading]
                |
       +--------+---------+-----------------+
       |                  |                 |
 [CLIP image encoder] [Visual features] [Title features]
       |                  |                 |
  image embedding    contrast/brightness    length/script
  (normalized)       saturation/OCR        optional text embedding
                     face count/etc.       image-title similarity
       |                  |                 |
       +------------------+-----------------+
                          |
                 [Feature table / cache]
                          |
           +--------------+---------------+
           |                              |
 [Similarity index]             [Supervised baseline model]
 (same-category examples)       (relative-performance label)
           |                              |
           +---------------+--------------+
                           |
                 [Evidence / diagnostics]
                           |
                 [Module C API/report]

                          INFERENCE

    User thumbnail + title + category
                 |
       Same frozen preprocessing
                 |
       CLIP + visual + title features
                 |
     Similarity retrieval + trained model
                 |
     Diagnostic report and suggestions
```

**Practical design choice:** Extract CLIP embeddings with a **pretrained frozen encoder** to begin with. There is no need to train CLIP from scratch or fine-tune it before you know whether your dataset and evaluation show a benefit.

### 6.1 Handcrafted thumbnail features (transparent, cheap)

Start with:

- **Brightness:** Mean perceived luminance; too dark or washed out may affect legibility.
- **Contrast:** Variation in luminance; compare within domain rather than applying a universal threshold.
- **Saturation/colorfulness:** Color intensity and distribution.
- **Text amount:** OCR bounding-box area divided by thumbnail area, number of text regions, approximate text size; optionally OCR confidence. Distinguish *text coverage* from *legibility*.
- **Faces:** Estimated number of faces; optionally their relative sizes/positions. Face-expression detection is optional and noisy, so do not assign simplistic universal emotion scores.
- **Composition:** Approximate location/scale of dominant subject, spatial clutter, use of foreground/background separation if feasible.
- **Title structure:** Character/word count, numbers/question framing (language-aware), script and optional topical tokens.

Use simple tools first: **OpenCV** for image statistics, an **OCR** system for text boxes, and a pretrained face detector when available. Apply consistent resizing and preprocessing. Keep missing detections separate from true zero counts.

### 6.2 CLIP feature path

1. Load each thumbnail; validate the file and dimensions.
2. Apply the selected CLIP model's own preprocessing.
3. Run its image encoder; save an embedding once per thumbnail.
4. Normalize embeddings if using cosine similarity.
5. Optionally encode the title; evaluate the language limitations explicitly.
6. Compute image-title similarity when meaningful.
7. Index image embeddings for approximate or exact nearest-neighbor search; filter or compare results by category.
8. Cache the model version, preprocessing version, and embedding ID so results are reproducible.

Avoid recomputing image embeddings on every API call; historical embeddings can be precomputed. A simple nearest-neighbor index is sufficient before adopting complex vector-database infrastructure.

### 6.3 Supervised prediction path

Possible first experiments:

- **Baseline 0:** Predict the training-set majority class (classification) or zero (regression).
- **Model 1:** Handcrafted visual features only (logistic regression or small XGBoost).
- **Model 2:** Title and category features only.
- **Model 3:** CLIP image embeddings only (regularized linear model, potentially with dimensionality reduction).
- **Model 4:** CLIP + handcrafted image features + title/category features.

**Compare these experiments rather than assuming the largest feature set wins.** If dataset size is limited, avoid feeding hundreds of raw CLIP dimensions into a high-capacity model without regularization; overfitting may easily beat training metrics while hurting new-channel generalization.

**Why compare ablations?** A thumbnail model might simply infer *video topic* from CLIP. If title/topic features alone predict just as well, you haven't shown the visual packaging features contribute anything extra. Model 4 should be justified by a real held-out improvement and clear limitations.

---

## 7. Training and validation rules (critical for a credible panel result)

### Prevent leakage

- Use the repository's **channel-level `fold`** for held-out-channel evaluation. All videos from a held-out channel must stay outside training and model selection for that evaluation fold.
- Do **not** include `channel_id`, `subscribers`, `views`, `likes`, `comments`, `y_*` labels, `prev_*` channel-history values, or post-upload engagement as Module C input features.
- Fit scalers, imputers, dimensionality reduction, and model parameters on **training folds only**; apply the fitted transforms to validation/test folds.
- Deduplicate thumbnails, check near-duplicates, and avoid copy/reupload patterns that unintentionally cross splits.
- Report per-category results and, when sample size permits, per-language/script and channel-size slices.
- For a stronger test of pre-upload behavior, add a **later-period holdout** or a truly prospective creator pilot. A random training/test split of videos is not enough.

### Biases you must explicitly discuss

1. **Exposure confounding:** More impressions can yield more views even if CTR is low.
2. **Topic/trend confounding:** A popular topic may drive views independent of packaging.
3. **Creator/channel factors:** Existing audience, reputation, recommendation history, upload frequency.
4. **Video-content factors:** Retention, quality, duration, and viewer satisfaction.
5. **View-count age:** Older uploads have had longer to accumulate views.
6. **Thumbnail/title edits:** The downloaded snapshot may not be the design viewers originally saw.
7. **Language differences:** Some pretrained encoders/OCR systems may perform much worse on Sinhala and Tamil.
8. **Dataset selection:** Only channels passing filters and videos with downloaded thumbnails are represented.

### Evaluation checklist

For **classification**: class balance, majority-class baseline, ROC-AUC, balanced accuracy, precision/recall or F1 as appropriate, and probability calibration.  
For **regression**: MAE/RMSE versus zero-prediction or basic feature baselines.  
For **retrieval**: manually inspect a sample of nearest neighbors for semantic relevance, category agreement, and false matches.  
For **explanations**: have people judge whether recommendations are understandable, faithful to the observed evidence, and actually actionable.

Do not present high training accuracy as a result. Report **held-out performance** and the dataset size used for it.

---

## 8. Explainability: what the expert should actually say

The product should offer **observations** and **testable suggestions**, not invented causal diagnoses.

Good:

- “This thumbnail has a relatively large OCR-detected text area, compared with the cooking-category thumbnails in the current dataset.”
- “Its image embedding is close to these historically collected cooking thumbnails. Their videos had mixed relative-view performance.”
- “The title refers to chicken curry, and the visible dish appears broadly consistent with that theme.”
- “Consider testing a tighter crop or simpler text treatment; this is a design hypothesis, not an established CTR uplift.”

Avoid:

- “Your thumbnail will get 15% CTR.”
- “Adding a face will increase views by 30%.”
- “CLIP proves this thumbnail is more clickable.”
- “This historical video went viral because of its contrast.”

**Explainability levels:**

1. **Measured facts:** Contrast, text area, image/title similarity, detected faces.
2. **Descriptive comparisons:** Percentiles or distributions within a relevant category, based on the actual dataset.
3. **Model associations:** Features associated with predicted relative performance; explain with feature importance/SHAP only if validated and interpreted cautiously.
4. **Suggestions:** Changes the creator can test, clearly distinguished from guaranteed outcome improvements.

For retrieved examples, include both **better- and worse-performing similar thumbnails** where possible; only showing high performers introduces cherry-picking.

---

## 9. Suggested user-facing output

### Demo user flow

1. User selects **Cooking**, **Education**, or **Gaming**.
2. User uploads a thumbnail and enters a title.
3. The backend extracts handcrafted features and CLIP embeddings.
4. The backend compares features with category-level norms and retrieves similar historical examples.
5. If the held-out model is sufficiently reliable, show a **relative-performance assessment** with uncertainty/limitations; otherwise omit the predictive number.
6. Return clear observations and suggested thumbnail/title experiments.

### Example report structure (illustrative, not a real scored result)

```json
{
  "module": "C_thumbnail_expert",
  "category": "cooking",
  "analysis": {
    "thumbnail_text_density": "high relative to selected cooking examples",
    "subject_visibility": "clear",
    "image_title_alignment": "appears relevant; language support must be checked"
  },
  "historical_comparisons": [
    {
      "video_id": "example_only",
      "visual_similarity": "high",
      "relative_view_performance": "above local channel baseline"
    }
  ],
  "predicted_ctr": null,
  "relative_performance_prediction": null,
  "recommendations": [
    "Try a version with less text and check readability at mobile size",
    "Compare tighter and wider crops in a controlled creator experiment"
  ],
  "limitations": [
    "Public views do not reveal actual CTR",
    "Historical associations do not establish why a thumbnail succeeded",
    "Illustrative output; prediction unavailable until validated"
  ]
}
```

The production output should carry **measured numeric features**, retrieval scores, model version, and uncertainty where appropriate. The example above is deliberately schematic and not a claim that those observations were measured.

---

## 10. Recommended implementation roadmap (after collection)

### Phase 0 — Finish and audit the corpus

- [ ] Run the collector's coverage/stats check.
- [ ] Build `data/training_table.csv` from the finalized metadata snapshot.
- [ ] Verify every `thumb_path` can be opened; count missing/corrupt images.
- [ ] Count videos/channels by category, language/script, age, and approximate channel size.
- [ ] Inspect `y_rel_neighbors`, `y_rel_prev`, missing labels, and class imbalance.
- [ ] Record collection dates and model/data version; do not assume the README target was reached.

**Exit criterion:** A documented usable dataset and an honest description of what its labels represent.

### Phase 1 — Handcrafted visual analysis

- [ ] Implement consistent thumbnail preprocessing.
- [ ] Extract brightness, contrast, saturation, text coverage, and face count.
- [ ] Save a feature table keyed by `video_id`.
- [ ] Visualize feature distributions for high/low relative performers in each category.
- [ ] Inspect examples manually to catch broken OCR/face-detection outputs.

**Exit criterion:** An explainable, functioning thumbnail feature extractor with real-data plots.

### Phase 2 — CLIP embeddings and retrieval

- [ ] Select a pretrained CLIP model and freeze it.
- [ ] Extract/cache embeddings for the entire valid corpus.
- [ ] Implement cosine similarity and same-category nearest-neighbor retrieval.
- [ ] Add title embeddings/image-title similarity only where language tests justify it.
- [ ] Inspect retrieval examples and keep both strong and weak outcomes in comparisons.

**Exit criterion:** Upload a thumbnail and retrieve genuinely similar collected thumbnails, with their relative-performance labels.

### Phase 3 — Small supervised model and ablation study

- [ ] Establish majority-class/zero-prediction baselines.
- [ ] Train handcrafted-only, title/category-only, CLIP-only, and combined experiments.
- [ ] Use held-out channel folds and train-only preprocessing.
- [ ] Compare `y_rel_neighbors` against `y_rel_prev` as a target.
- [ ] Report per-category metrics, calibration, and generalization failures.

**Exit criterion:** Evidence for whether visual/CLIP features actually improve prediction over simpler baselines—or an honest finding that they do not yet.

### Phase 4 — Creator-facing Thumbnail Expert API/demo

- [ ] Accept `image`, `title`, and `category`.
- [ ] Return visual measurements, title-image assessment, and similar examples.
- [ ] Generate cautious, category-conditioned, actionable feedback.
- [ ] Include predicted relative-performance output **only if** measured reliability is adequate.
- [ ] Add latency/error handling for bad images, missing text, and unsupported languages.

**Exit criterion:** End-to-end creator demo without fabricated CTR estimates.

### Phase 5 — Optional stronger validation / later research

- [ ] Collect fixed-age view snapshots prospectively to improve labels.
- [ ] Recruit consenting creators for actual **impressions**, **impressions CTR**, historical titles/thumbnails, and other Studio/Analytics metrics.
- [ ] Evaluate creator-specific CTR deltas rather than pretending public views are CTR.
- [ ] Where possible, evaluate thumbnail suggestions through controlled creator experiments/A-B tests, looking at the experiment's actual chosen outcome metric.
- [ ] Document limitations and update the model as trends change.

**Exit criterion:** Better-grounded, potentially causal evidence beyond the public-data proxy.

---

## 11. Recommended tools and boundaries

| Need | Practical starting point |
|---|---|
| Image reading and color statistics | OpenCV, NumPy |
| Data tables and validation | pandas, NumPy |
| Thumbnail text regions | OCR library validated on your languages |
| Faces | Pretrained face detector; measure detection quality |
| Semantic image embeddings | Pretrained CLIP image encoder |
| Similarity search | Cosine similarity + simple nearest-neighbor index first |
| Small tabular/embedding baseline | scikit-learn logistic/ridge regression; optionally XGBoost |
| Model experiment metrics | scikit-learn |
| Model explanations | Simple feature comparisons first; SHAP only where appropriate |

Do not train a vision foundation model from scratch for this MVP. Keep the pipeline reproducible, cache embeddings, version preprocessing and labels, and prefer small experiments that the panel can understand.

### Handoff contract for an AI coding agent

**Inputs:** `thumbnail_image`, `title`, `category`.  
**Offline research data:** `data/training_table.csv` and the downloaded thumbnails.  
**Offline labels/splits:** `y_rel_neighbors` (and/or `y_rel_prev`), `fold`, `channel_id` strictly for grouping/labeling.  
**No-leakage Module C model inputs:** thumbnail-derived features, title-derived features, and category.  
**Outputs:** measured visual features, CLIP vector or cached vector ID, image/title alignment where valid, retrieved examples, and optional validated relative-performance score + cautionary notes.

**Agent implementation guardrails:**

- Do not rename or overwrite existing collector outputs without coordinating schema changes.
- Do not rename relative-view labels as `ctr`.
- Do not sneak channel history or post-publication outcomes into predictive inputs.
- Do not show made-up model confidence values or fabricated demo measurements.
- Do not claim positive causal effects from correlations/SHAP.
- Keep multilingual text performance and error cases visible.
- Add tests for corrupt images, missing thumbnail paths, duplicates, split leakage, and deterministic embeddings.

---

## 12. What to tell the panel

> We are developing an explainable Thumbnail Expert for Sri Lankan YouTube creators. Using a corpus of public thumbnails, titles, and video metadata, we compare each video's view performance against similar uploads from its own channel rather than comparing raw view counts between channels. This relative-view label is **not actual CTR**, because the public API does not provide thumbnail impression data. Our vision pipeline combines pretrained CLIP embeddings with interpretable thumbnail features such as contrast and text coverage. We evaluate whether those features add predictive value on **unseen channels**, and we use similar historical examples to provide actionable, clearly qualified packaging feedback. Actual CTR prediction is a future, creator-consented extension.

### Deliverables worth prioritizing for a near-term review

1. Real dataset quality/coverage summary, including known limitations.
2. Working thumbnail feature extraction from collected examples.
3. CLIP similarity/retrieval demo with category-relevant historical examples.
4. Feature-versus-relative-performance plots and at least one honest held-out baseline.
5. A simple end-to-end analysis report with suggestions that do not overclaim causality.

### Final design judgment

**Recommended order:** **collect → audit → handcrafted features → pretrained CLIP + retrieval → small supervised model → creator-facing explanations → private CTR data/controlled evaluation later**.

This order makes the module demonstrable before chasing uncertain CTR accuracy. It also turns the limitation of public data into an explicit research design choice instead of hiding it.

---

## 13. Source notes (internal project context)

This document consolidates the project discussion and the following internal sources; these are **file paths**, not video tutorials or external resource links:

- `data-collector/README.md` — data collection goals, schema notes, split rules, and explicit target limitations.
- `data-collector/build_training_table.py` — exact definitions of `y_rel_neighbors`, `y_rel_prev`, filtering, and channel folds.
- Project architecture document, sections on Module C, data requirements, and evaluation — initial CTR-delta vision and creator-consented Analytics requirements.

**Classification of statements:** Existing file names, columns, formulas, and collection settings above are based on the repository documentation/code. The proposed CLIP integration, ablation tests, API response, phased roadmap, and evaluation improvements are **recommendations for the next development stage**, not assertions that those components are implemented.
