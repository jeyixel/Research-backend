"""Local UI and allowlisted, precomputed public-corpus examples."""

import json
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import Field, ValidationError

from app.modules.module_c.config import Settings, get_settings
from app.modules.module_c.schemas import Category, Report, StrictModel, TitleLanguage

WEB_ROOT = Path(__file__).resolve().parent / "web"
router = APIRouter()
SettingsDependency = Annotated[Settings, Depends(get_settings)]


class ReviewExample(StrictModel):
    video_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,32}$")
    title: str
    category: Category
    title_language: TitleLanguage


class ExampleSummary(ReviewExample):
    thumbnail_preview: str
    report_url: str


class ExampleCatalog(StrictModel):
    examples: list[ExampleSummary]


def review_folder(settings: Settings) -> Path:
    return settings.artifact_dir / "review"


def review_manifest(settings: Settings) -> list[ReviewExample]:
    try:
        data = json.loads((review_folder(settings) / "examples.json").read_text(encoding="utf-8"))
        return [ReviewExample.model_validate(item) for item in data["examples"]]
    except FileNotFoundError:
        return []
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise HTTPException(503, "Saved examples are unavailable. Regenerate the review queue.") from exc


def example_report(settings: Settings, example: ReviewExample) -> Report:
    try:
        report = Report.model_validate_json(
            (review_folder(settings) / f"{example.video_id}.json").read_text(encoding="utf-8")
        )
        if report.category != example.category or report.title_language != example.title_language:
            raise ValueError("Saved example metadata does not match its report.")
        return report
    except (OSError, ValidationError, ValueError) as exc:
        raise HTTPException(503, "Saved example is unavailable. Regenerate the review queue.") from exc


@router.get("/", include_in_schema=False)
def studio():
    return FileResponse(
        WEB_ROOT / "index.html",
        headers={
            "Cache-Control": "no-cache",
            "Content-Security-Policy": "default-src 'self'; img-src 'self' data: blob:; "
            "script-src 'self'; style-src 'self'; connect-src 'self'; "
            "base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
        },
    )


@router.get("/api/module-c/examples", response_model=ExampleCatalog)
def examples(settings: SettingsDependency):
    """One saved example per category; empty until the review command has run."""
    selected, categories = [], set()
    for example in review_manifest(settings):
        if example.category in categories:
            continue
        report = example_report(settings, example)
        selected.append(
            ExampleSummary(
                **example.model_dump(),
                thumbnail_preview=report.mobile_preview,
                report_url=f"/api/module-c/examples/{example.video_id}",
            )
        )
        categories.add(example.category)
    return ExampleCatalog(examples=selected)


@router.get("/api/module-c/examples/{video_id}", response_model=Report)
def saved_example(video_id: str, settings: SettingsDependency):
    """Return only reports whose IDs are present in the validated local manifest."""
    for example in review_manifest(settings):
        if example.video_id == video_id:
            return example_report(settings, example)
    raise HTTPException(404, "Saved example not found.")


@router.get("/review", include_in_schema=False)
def review_page(settings: SettingsDependency):
    path = review_folder(settings) / "review.html"
    if not path.is_file():
        raise HTTPException(404, "Run the Module C review command to generate this page.")
    return FileResponse(path, media_type="text/html", headers={"Cache-Control": "no-cache"})


@router.get("/review/human_review.csv", include_in_schema=False)
def review_sheet(settings: SettingsDependency):
    path = review_folder(settings) / "human_review.csv"
    if not path.is_file():
        raise HTTPException(404, "Human review sheet has not been generated.")
    return FileResponse(path, media_type="text/csv", filename="human_review.csv")
