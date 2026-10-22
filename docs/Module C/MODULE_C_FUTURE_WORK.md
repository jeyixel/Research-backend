# Module C future work

Updated 21 October 2026. The deliverable is a working local thumbnail-analysis and retrieval demo.
Creator performance scoring remains a research goal.

## Current evidence

- 30,223 distinct images after excluding 1,634 exact duplicate copies.
- Frozen CLIP embeddings and CRAFT geometry extracted on CUDA; 24,163 development references indexed.
- Five experiments evaluated on 5,989 videos from 71 held-out channels.
- Combined AUROC: **0.531910**; title/category: **0.527420**.
- Paired combined-minus-title AUROC interval: **[-0.009148, 0.017295]**. Added visual benefit is uncertain.
- Combined Brier score: **0.275438**, worse than the prior's **0.250010**.
- Sinhala-script combined AUROC: **0.506968**. Tamil-script AUROC **0.675981** is based on only 177
  examples and is not evidence of reliable Tamil-language support. Scripts are not verified languages.

Do not turn these probabilities into a thumbnail quality, CTR, or virality score. Do not repeatedly
retune on final fold 4. Preserve this completed study as the initial result.

## Required human work

1. Complete `artifacts/module_c/review/human_review.csv` using independent creator/designer judgments
   (`yes`, `partial`, `no`): image-supported findings, specific advice, absence of unsupported claims,
   and useful retrieved examples. Record Sinhala/Tamil text-detection errors in notes. Automated checks
   cannot provide these judgments. Regenerating review artifacts preserves existing judgments.
2. Complete `artifacts/module_c/channel_review.csv` for category and Sri Lankan relevance. Channel
   labels can include off-topic individual videos. Version substantive dataset corrections separately.
3. Test new creator-made or generated thumbnails, record input/version and outputs, and assess whether
   advice is correct and useful. Synthetic examples test functionality and sensitivity to edits; they do
   not measure predictive accuracy without independent outcomes or expert labels.

## Improving the research model

- Collect paired original thumbnails/titles with outcomes at consistent ages. Current snapshots range
  greatly in age, and historical thumbnail/title edits are unknown.
- Improve topic controls, label quality, category balance, and local-language coverage before trying
  larger models. Inspect training/development failures and keep a new untouched validation set.
- Compare stronger multilingual/visual representations only in a separately versioned experiment.
  Fine-tuning is an option after evidence about data quality and generalization; it is not the next
  automatic response to weak held-out results.
- Validate probability calibration, category/language behavior, and channel-balanced metrics on new or
  prospective data. Use uncertainty and an abstain/unavailable state for unsupported cases.
- Investigate model explanations for faithfulness. Changing a measured feature or model output does
  not establish which edit will improve real-world outcomes.

## Connecting a defensible score to the product

Only after validation gates pass, load a trusted, versioned model and its training preprocessing in the
API, define a meaningful relative-performance estimate, and update `relative_performance_prediction`
with uncertainty and model/data provenance. Add integration tests for missing/incompatible models and
out-of-domain uploads. The current upload API deliberately does not load research joblib models.

Actual CTR needs creator-consented impressions/CTR data with correctly paired packaging. Controlled
creator experiments are needed to test whether suggested edits cause improvements. Public relative
views cannot establish why a thumbnail went viral.

## UI and deployment

- Migrate the interface to Next.js using [the API contract](MODULE_C_API_AND_UI.md); keep inference in
  the Python service. Add durable report history only with explicit storage/retention requirements.
- Add authentication, request limits, GPU job queuing, model readiness/warmup, cancellation semantics,
  observability, and HTTPS for a hosted service. The current server is intended for localhost.
- Improve scene-specific observations and Sinhala/Tamil reading only after selecting and evaluating
  appropriate models. Current CRAFT geometry is not text recognition, and there is no face/emotion model.
- Keep generated-thumbnails and before/after demos labeled. The current revision comparison describes
  measured changes and does not choose a predicted winner.

## Presentation wording

“The working prototype analyzes a proposed thumbnail, measures its visual properties, compares it with
historical thumbnails, and proposes design experiments linked to evidence. We evaluated five prediction
baselines on unseen channels. The first results are weak, so a performance score remains future work.”
