import argparse
import asyncio
import html
import json
from pathlib import Path

from .config import Settings
from .data import read_table, thumbnail_path, write_json


def main():
    parser = argparse.ArgumentParser(description="Module C offline research and local demo tools")
    parser.add_argument(
        "--artifacts", type=Path, help="Artifact directory, relative to backend unless absolute"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    audit = commands.add_parser("audit", help="Validate images and identify duplicate candidates")
    audit.add_argument("--workers", type=int, default=4)
    extraction = commands.add_parser("extract", help="Resume frozen features/embeddings and text detection")
    extraction.add_argument("--limit", type=int, help="Maximum new images, e.g. 500 for a benchmark")
    extraction.add_argument("--offline", action="store_true", help="Do not download model weights")
    commands.add_parser("index", help="Build development-only retrieval/reference artifacts")
    train = commands.add_parser("train", help="Tune on folds 0–3; evaluate once on untouched fold 4")
    train.add_argument("--target", choices=["y_rel_neighbors", "y_rel_prev"], default="y_rel_neighbors")
    train.add_argument("--bootstrap", type=int, default=200)
    analysis = commands.add_parser(
        "analyze", help="Analyze one image; write a report only at the requested path"
    )
    analysis.add_argument("--image", type=Path, required=True)
    analysis.add_argument("--title", required=True)
    analysis.add_argument("--category", choices=["cooking", "education", "gaming"], required=True)
    analysis.add_argument(
        "--title-language", choices=["en", "si", "ta", "mixed", "unknown"], default="unknown"
    )
    analysis.add_argument("--out", type=Path, required=True)
    commands.add_parser("review", help="Generate 18 public-corpus reports and a human review form")
    commands.add_parser("status", help="Inspect reference readiness without calling Gemini")
    args = parser.parse_args()
    settings = Settings()
    if args.artifacts:
        settings = settings.model_copy(update={"artifacts": args.artifacts})
    if args.command == "audit":
        from .audit import run_audit

        run_audit(settings, workers=args.workers)
    elif args.command == "extract":
        from .pipeline import extract

        extract(settings, limit=args.limit, allow_download=not args.offline)
    elif args.command == "index":
        from .pipeline import build_index

        build_index(settings)
    elif args.command == "train":
        from .evaluation import run_evaluation

        run_evaluation(settings, args.target, args.bootstrap)
    elif args.command == "review":
        generate_review(settings)
    else:
        from .service import ThumbnailService

        service = ThumbnailService(settings)
        if args.command == "status":
            print(json.dumps(service.status(), indent=2))
        else:
            report = service.analyze(args.image.read_bytes(), args.title, args.category, args.title_language)
            report = asyncio.run(service.word_report(report))
            write_json(args.out, report.model_dump())
            print(f"Wrote {args.out}")


def generate_review(settings):
    import pandas as pd

    from .service import ThumbnailService

    service = ThumbnailService(settings.model_copy(update={"writer": "rules"}))
    frame = read_table(settings)
    folder = settings.artifact_dir / "review"
    folder.mkdir(parents=True, exist_ok=True)
    items, cards = [], []
    for category in ("cooking", "education", "gaming"):
        part = frame[(frame.category == category) & (frame.fold == 4)]
        # Prefer script variety, then fill deterministically to six per category.
        selected = part.groupby("title_script", group_keys=False).head(1)
        selected = (
            pd.concat([selected, part.sample(frac=1, random_state=42)]).drop_duplicates("video_id").head(6)
        )
        for row in selected.itertuples(index=False):
            language = {"sinhala": "si", "tamil": "ta", "mixed": "mixed"}.get(row.title_script, "unknown")
            report = service.analyze(
                thumbnail_path(settings, row.thumb_path).read_bytes(), row.title, category, language
            )
            write_json(folder / f"{row.video_id}.json", report.model_dump())
            known = {f.id for f in report.findings}
            evidence_valid = all(set(r.evidence_ids) <= known for r in report.recommendations)
            items.append(
                {
                    "video_id": row.video_id,
                    "category": category,
                    "title_script": row.title_script,
                    "evidence_ids_valid": evidence_valid,
                    "human_findings_supported": "",
                    "human_advice_specific": "",
                    "human_no_unsupported_claims": "",
                    "human_neighbors_relevant": "",
                    "notes": "",
                }
            )
            cards.append(
                f"<article><h2>{html.escape(category)} / {html.escape(row.title_script)}</h2>"
                f"<p>{html.escape(row.title)}</p><img src='{report.mobile_preview}' width='320' height='180'>"
                f"<p>{html.escape(row.video_id)}</p><h3>Measured observations</h3><ul>"
                + "".join(f"<li>{html.escape(f.statement)}</li>" for f in report.findings)
                + "</ul><h3>Suggestions to test</h3><ul>"
                + "".join(
                    f"<li>{html.escape(r.action)} {html.escape(r.explanation)} "
                    f"<em>Test: {html.escape(r.how_to_test)}</em></li>"
                    for r in report.recommendations
                )
                + "</ul><h3>Similar historical examples</h3><p>Relative log views are not CTR. "
                "Similarity does not establish that a design caused performance.</p><div class='neighbors'>"
                + "".join(
                    "<figure>"
                    + (
                        f"<img src='{c.thumbnail_preview}' width='320' height='180'>"
                        if c.thumbnail_preview
                        else ""
                    )
                    + f"<figcaption><a href='{html.escape(c.source_url)}'>{html.escape(c.video_id)}</a>: "
                    f"cosine {c.visual_similarity:.3f}; relative log views {c.relative_view_performance:.3f}"
                    "</figcaption></figure>"
                    for c in report.historical_comparisons
                )
                + "</div></article>"
            )
    pd.DataFrame(items).to_csv(folder / "human_review.csv", index=False)
    page = (
        "<!doctype html><html lang='en'><meta charset='utf-8'><title>Module C human review</title>"
        "<style>body{font:16px system-ui;max-width:1000px;margin:2rem auto}"
        "article{border-bottom:1px solid #aaa;padding:1rem}.neighbors{display:flex;flex-wrap:wrap;gap:1rem}"
        "figure{margin:0;width:320px}figcaption{font-size:14px}li{margin-bottom:.6rem}</style>"
        "<h1>Module C review queue</h1><p>Human review is pending. Record judgments in human_review.csv. "
        "These are public corpus examples, not unpublished creator uploads.</p>" + "".join(cards) + "</html>"
    )
    (folder / "review.html").write_text(page, encoding="utf-8")
    print(f"Generated {len(items)} reports and a human review queue in {folder}")


if __name__ == "__main__":
    main()
