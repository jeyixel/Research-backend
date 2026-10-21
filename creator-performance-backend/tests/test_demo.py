import json

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.module_c.cli import generate_review
from app.modules.module_c.config import Settings, get_settings
from app.modules.module_c.schemas import Report


def saved_report(category="cooking", language="unknown"):
    return Report(
        category=category,
        title_language=language,
        measurements={"brightness": 0.25},
        title_features={},
        capabilities={},
        findings=[],
        recommendations=[],
        mobile_preview="data:image/jpeg;base64,AA==",
        provenance={},
        limitations=[],
    )


@pytest.fixture
def demo(tmp_path):
    settings = Settings(_env_file=None, artifacts=tmp_path, writer="rules")
    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_settings] = lambda: settings
    with TestClient(app) as client:
        yield client, tmp_path
    app.dependency_overrides.clear()
    app.dependency_overrides.update(previous)


def write_example(folder, video_id="example-id", category="cooking"):
    folder.mkdir(exist_ok=True)
    example = {"video_id": video_id, "title": "A public example", "category": category, "title_language": "unknown"}
    (folder / f"{video_id}.json").write_text(saved_report(category).model_dump_json(), encoding="utf-8")
    return example


def test_studio_and_static_assets_are_served_without_models(demo):
    client, _ = demo
    page = client.get("/")
    assert page.status_code == 200
    assert "script-src 'self'" in page.headers["content-security-policy"]
    assert 'id="analyze-form"' in page.text
    for asset in ("studio.css", "studio.js"):
        assert client.get(f"/static/{asset}").status_code == 200
    assert client.get("/static/../.env").status_code == 404


def test_example_catalog_and_allowlist(demo):
    client, root = demo
    assert client.get("/api/module-c/examples").json() == {"examples": []}
    assert client.get("/review").status_code == 404
    folder = root / "review"
    examples = [write_example(folder, "first"), write_example(folder, "second")]
    (folder / "examples.json").write_text(json.dumps({"examples": examples}), encoding="utf-8")
    catalog = client.get("/api/module-c/examples").json()["examples"]
    assert len(catalog) == 1  # One card per category, deterministic order.
    assert catalog[0]["video_id"] == "first"
    assert client.get(catalog[0]["report_url"]).json()["relative_performance_prediction"] is None
    write_example(folder, "not-listed")
    assert client.get("/api/module-c/examples/not-listed").status_code == 404
    (folder / "first.json").write_text("broken", encoding="utf-8")
    assert client.get("/api/module-c/examples/first").status_code == 503


def test_example_manifest_cannot_escape_review_directory(demo):
    client, root = demo
    folder = root / "review"
    folder.mkdir()
    manifest = {"examples": [{"video_id": "../private", "title": "Bad", "category": "cooking", "title_language": "en"}]}
    (folder / "examples.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert client.get("/api/module-c/examples").status_code == 503


def test_review_rerun_preserves_human_judgments_and_exports_manifest(tmp_path, monkeypatch):
    rows = [
        {"video_id": f"{category}-{i}", "title": "A <test> title", "title_script": "latin", "fold": 4,
         "category": category, "thumb_path": "unused"}
        for category in ("cooking", "education", "gaming") for i in range(6)
    ]
    source = tmp_path / "source.jpg"
    source.write_bytes(b"mock image")
    monkeypatch.setattr("app.modules.module_c.cli.read_table", lambda _: pd.DataFrame(rows))
    monkeypatch.setattr("app.modules.module_c.cli.thumbnail_path", lambda *_: source)

    class FakeService:
        def __init__(self, _):
            pass

        def analyze(self, data, title, category, language):
            return saved_report(category, language)

    monkeypatch.setattr("app.modules.module_c.service.ThumbnailService", FakeService)
    settings = Settings(_env_file=None, artifacts=tmp_path / "artifacts")
    generate_review(settings)
    folder = settings.artifact_dir / "review"
    manifest = json.loads((folder / "examples.json").read_text(encoding="utf-8"))
    assert len(manifest["examples"]) == 18
    assert "A &lt;test&gt; title" in (folder / "review.html").read_text(encoding="utf-8")
    sheet = pd.read_csv(folder / "human_review.csv", keep_default_na=False)
    sheet.loc[0, "human_findings_supported"] = "partial"
    sheet.loc[0, "notes"] = "Keep this expert judgment."
    sheet.to_csv(folder / "human_review.csv", index=False)
    # Simulate a selection change; retain judgments for the old example too.
    rows[0] = {**rows[0], "video_id": "new-cooking"}
    generate_review(settings)
    repeated = pd.read_csv(folder / "human_review.csv", keep_default_na=False).set_index("video_id")
    assert repeated.loc["cooking-0", "human_findings_supported"] == "partial"
    assert repeated.loc["cooking-0", "notes"] == "Keep this expert judgment."
    assert len(repeated) == 19
