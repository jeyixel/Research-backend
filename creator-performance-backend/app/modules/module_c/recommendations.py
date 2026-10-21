import numpy as np

from .schemas import Finding, Recommendation


def make_recommendations(measurements: dict, category: str, references=None):
    findings, recommendations = [], []
    for metric in ["brightness", "contrast", "saturation", "text_coverage"]:
        observed = measurements.get(metric)
        if observed is None:
            continue
        distribution = references.distribution(category, metric) if references else np.array([])
        percentile = (
            round(
                float(
                    (np.sum(distribution < observed) + 0.5 * np.sum(distribution == observed))
                    / len(distribution)
                    * 100
                ),
                1,
            )
            if len(distribution)
            else None
        )
        if percentile is None:
            statement = (
                f"Measured {metric.replace('_', ' ')}: {observed:.3f}; category reference unavailable."
            )
        else:
            statement = (
                f"Measured {metric.replace('_', ' ')}: {observed:.3f}, approximately the "
                f"{percentile:g} percentile among {len(distribution)} {category} reference thumbnails."
            )
        findings.append(
            Finding(
                id=f"measure_{metric}",
                metric=metric,
                observed=observed,
                percentile=percentile,
                reference_count=len(distribution),
                statement=statement,
                basis="category_comparison" if percentile is not None else "measurement",
            )
        )

    def suggest(key, action, test, finding, explanation):
        recommendations.append(
            Recommendation(
                id=key,
                priority=len(recommendations) + 1,
                action=action,
                how_to_test=test,
                evidence_ids=[finding.id],
                explanation=explanation,
            )
        )

    for finding in findings:
        if finding.reference_count < 30 or finding.percentile is None:
            continue
        if finding.metric == "brightness" and finding.percentile <= 10:
            suggest(
                "test_brightness",
                "Compare a version with more visible midtones.",
                "Compare both versions at mobile size and check that important details remain visible.",
                finding,
                "This image has relatively low average luminance in the selected category. "
                "A brighter version is a design experiment; the measurement does not establish poor readability.",
            )
        elif finding.metric == "contrast" and finding.percentile <= 10:
            suggest(
                "test_contrast",
                "Test stronger separation between the main elements and background.",
                "Compare the original and edited version at mobile size; avoid losing highlight or shadow details.",
                finding,
                "Global contrast is relatively low in this reference set. Inspect the actual subject "
                "and text before deciding whether extra contrast helps.",
            )
        elif finding.metric == "text_coverage" and finding.percentile >= 90:
            suggest(
                "test_text_density",
                "Try a version with fewer or shorter text blocks.",
                "Keep the core promise unchanged and compare how quickly a viewer can identify it at mobile size.",
                finding,
                "The detector estimates a relatively large text-region area. This does not establish "
                "that the text is unreadable or that less text will improve views.",
            )

    height = measurements.get("min_text_height_mobile")
    if height is not None:
        finding = Finding(
            id="mobile_text_geometry",
            metric="min_text_height_mobile",
            observed=height,
            statement=f"The smallest detected text region is about {height:g} pixels high "
            "in the mobile preview; this measures a region, not character legibility.",
            basis="measurement",
        )
        findings.append(finding)
        if height < 8:
            suggest(
                "test_larger_text",
                "Inspect the smallest text and test enlarging or removing it.",
                "View the mobile preview without zooming and ask someone to read the intended words.",
                finding,
                "A detected text region becomes small at mobile size. The size flag is a heuristic "
                "that needs a human readability check, especially for local scripts.",
            )

    preview = Finding(
        id="mobile_preview",
        metric="preview_width",
        observed=320,
        statement="A full-frame mobile preview is provided at 320 by 180 pixels.",
        basis="measurement",
    )
    findings.append(preview)
    suggest(
        "review_mobile",
        "Check the thumbnail at mobile size before publishing.",
        "Ask someone unfamiliar with the video what the thumbnail promises and what they notice first.",
        preview,
        "The preview supports a practical visual check. Automated statistics cannot establish "
        "subject clarity, visual appeal, or whether viewers will click.",
    )
    return findings, recommendations
