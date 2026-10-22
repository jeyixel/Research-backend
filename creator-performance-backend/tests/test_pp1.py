"""PP1 module failures must not disguise missing evidence or erase Module C values."""

import asyncio
import io

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app, get_service
from app.modules.module_c.config import Settings
from app.modules.module_c.schemas import Finding, Report
from app.pp1 import explain_c


def upload():
    out = io.BytesIO()
    Image.new("RGB", (640, 360), (100, 130, 160)).save(out, "PNG")
    return {"thumbnail": ("example.png", out.getvalue(), "image/png")}


class StubService:
    def __init__(self, settings, fail=False):
        self.settings = settings
        self.fail = fail

    def analyze(self, data, title, category, title_language):
        if self.fail:
            raise RuntimeError("module C unavailable")
        return Report(
            category=category, title_language=title_language,
            measurements={"brightness": 0.345678, "contrast": 0.12}, title_features={}, capabilities={},
            findings=[Finding(id="measure_brightness", metric="brightness", observed=0.345678,
                              statement="Measured brightness is 0.345678.", basis="measurement")],
            recommendations=[], mobile_preview="data:image/jpeg;base64,AA==",
            provenance={}, limitations=["Experimental diagnostic measurement."],
        )


def test_missing_transcript_and_gemini_key_preserve_module_c(tmp_path, monkeypatch):
    settings = Settings(_env_file=None, artifacts=tmp_path, writer="gemini", GEMINI_API_KEY="")
    app.dependency_overrides[get_service] = lambda: StubService(settings)
    monkeypatch.setattr("app.main.analyze_b", lambda title, category: {
        "status": "unavailable", "maturity": "experimental", "matches": [], "suggestions": [],
        "limitations": ["No stored topics."]})
    try:
        with TestClient(app) as client:
            response = client.post("/api/pp1/analyze", data={
                "title": "A real idea", "category": "education", "consent_to_gemini": "true",
            }, files=upload())
        assert response.status_code == 200
        result = response.json()
        assert result["modules"]["C"]["measurements"]["brightness"] == 0.345678
        assert result["modules"]["C"]["explanations"][0]["source"] == "rules"
        assert result["modules"]["C"]["explanation_writer"]["reason"] == "missing_api_key"
        assert result["modules"]["A"]["status"] == "unavailable"
        assert result["modules"]["B"]["status"] == "unavailable"
        assert result["modules"]["D"]["status"] == "unavailable"
        assert result["modules"]["E"]["status"] == "unavailable"
    finally:
        app.dependency_overrides.clear()


def test_module_failure_isolated_and_transcript_is_limited(tmp_path, monkeypatch):
    settings = Settings(_env_file=None, artifacts=tmp_path, writer="rules")
    app.dependency_overrides[get_service] = lambda: StubService(settings, fail=True)
    monkeypatch.setattr("app.main.analyze_b", lambda title, category: {
        "status": "completed", "maturity": "experimental",
        "matches": [{"topic": "An example", "evidence_type": "sample"}],
        "suggestions": [{"text": "Consider an example angle."}], "limitations": []})
    try:
        with TestClient(app) as client:
            response = client.post("/api/pp1/analyze", data={
                "title": "An example", "category": "education", "thumbnail_text": "An example",
                "transcript": "An example is mentioned here.", "transcript_complete": "false",
            }, files=upload())
        assert response.status_code == 200
        result = response.json()
        assert result["modules"]["C"]["status"] == "failed"
        assert result["modules"]["B"]["status"] == "completed"
        assert result["modules"]["A"]["status"] == "limited"
        assert result["modules"]["A"]["thumbnail_text_source"] == "user_supplied"
        assert result["status"] == "partial"
    finally:
        app.dependency_overrides.clear()


def test_bad_image_is_a_request_error(tmp_path):
    settings = Settings(_env_file=None, artifacts=tmp_path, writer="rules")
    app.dependency_overrides[get_service] = lambda: StubService(settings)
    try:
        with TestClient(app) as client:
            response = client.post("/api/pp1/analyze", data={"title": "An example", "category": "education"},
                                   files={"thumbnail": ("broken.png", b"not an image", "image/png")})
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_other_module_exceptions_leave_c_available(tmp_path, monkeypatch):
    settings = Settings(_env_file=None, artifacts=tmp_path, writer="rules")
    app.dependency_overrides[get_service] = lambda: StubService(settings)

    def fail_b(title, category):
        raise RuntimeError("topic database failed")

    async def fail_a(*args):
        raise RuntimeError("text comparator failed")

    monkeypatch.setattr("app.main.analyze_b", fail_b)
    monkeypatch.setattr("app.main.analyze_a", fail_a)
    try:
        with TestClient(app) as client:
            response = client.post("/api/pp1/analyze", data={"title": "An example", "category": "education"},
                                   files=upload())
        assert response.status_code == 200
        result = response.json()
        assert result["modules"]["C"]["status"] == "completed"
        assert result["modules"]["C"]["measurements"]["brightness"] == 0.345678
        assert result["modules"]["B"]["status"] == "failed"
        assert result["modules"]["A"]["status"] == "failed"
    finally:
        app.dependency_overrides.clear()


def test_c_explanations_are_separate_and_consent_gated(tmp_path, monkeypatch):
    settings = Settings(_env_file=None, artifacts=tmp_path, writer="gemini", GEMINI_API_KEY="fake-key")
    report = StubService(settings).analyze(b"image", "Example", "education", "unknown")
    calls = []

    class FakeWriter:
        def __init__(self, settings):
            calls.append("created")

        async def write(self, category, findings, recommendations):
            calls.append("called")
            rewrites = [r.model_copy(update={"explanation": "Consider inspecting the preview for useful adjustments."})
                        for r in recommendations]
            from app.modules.module_c.schemas import WriterStatus
            return rewrites, WriterStatus(provider="gemini", status="available")

    monkeypatch.setattr("app.pp1.GeminiWriter", FakeWriter)
    local = asyncio.run(explain_c(report, settings, False))
    assert local["items"][0]["source"] == "rules"
    assert calls == []
    generated = asyncio.run(explain_c(report, settings, True))
    assert generated["items"][0]["source"] == "gemini"
    assert calls == ["created", "called"]
    assert report.measurements["brightness"] == 0.345678
    assert report.findings[0].statement == "Measured brightness is 0.345678."
