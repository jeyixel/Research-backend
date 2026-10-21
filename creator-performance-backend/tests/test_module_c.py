import asyncio
import io
import json

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app, get_service
from app.modules.module_c.audit import BKTree, UnionFind
from app.modules.module_c.config import Settings
from app.modules.module_c.data import read_table, thumbnail_path
from app.modules.module_c.evaluation import model_pipeline, predictive_inputs, purged_split
from app.modules.module_c.features import VISUAL_COLUMNS, title_features, visual_features
from app.modules.module_c.images import difference_hash, image_hash, load_image, square_image
from app.modules.module_c.recommendations import make_recommendations
from app.modules.module_c.retrieval import ReferenceIndex
from app.modules.module_c.service import ThumbnailService
from app.modules.module_c.store import FeatureStore
from app.modules.module_c.writers import GeminiWriter, LocalBudget, safe_context, validate_rewrite


def image_bytes(color=(80, 120, 160), size=(640, 360)):
    output = io.BytesIO()
    Image.new("RGB", size, color).save(output, format="PNG")
    return output.getvalue()


@pytest.fixture
def settings(tmp_path):
    return Settings(
        _env_file=None,
        artifacts=tmp_path / "artifacts",
        collector_root=tmp_path / "collector",
        training_table=tmp_path / "table.csv",
        writer="rules",
        ocr_enabled=False,
        GEMINI_API_KEY="",
    )


def test_safe_images_and_full_frame():
    original = load_image(image_bytes())
    padded = square_image(original)
    assert padded.size == (640, 640)
    assert padded.getpixel((0, 140)) == original.getpixel((0, 0))
    assert padded.getpixel((639, 499)) == original.getpixel((639, 359))
    assert image_hash(original) == image_hash(load_image(image_bytes()))
    assert difference_hash(original) == difference_hash(original.copy())
    with pytest.raises(ValueError):
        load_image(b"not an image")
    with pytest.raises(ValueError):
        load_image(image_bytes(size=(8, 8)))
    with pytest.raises(ValueError):
        load_image(image_bytes(), max_pixels=100)
    gif = io.BytesIO()
    original.save(gif, format="GIF")
    with pytest.raises(ValueError):
        load_image(gif.getvalue())


def test_alpha_and_exif():
    buffer = io.BytesIO()
    Image.new("RGBA", (32, 32), (0, 0, 0, 0)).save(buffer, format="PNG")
    assert load_image(buffer.getvalue()).getpixel((0, 0)) == (127, 127, 127)
    source = Image.new("RGB", (40, 20))
    exif = source.getexif()
    exif[274] = 6
    buffer = io.BytesIO()
    source.save(buffer, "JPEG", exif=exif)
    assert load_image(buffer.getvalue()).size == (20, 40)


def test_text_missing_is_not_zero_and_union_area():
    image = load_image(image_bytes())
    missing = visual_features(image)
    assert missing["text_coverage"] is None

    class Detector:
        def boxes(self, _):
            return [(0, 0, 64, 36), (0, 0, 64, 36)]

    measured = visual_features(image, Detector())
    assert measured["text_coverage"] == 0.01
    assert measured["min_text_height_mobile"] == 18
    assert measured["text_regions"] == 2
    assert title_features("සිංහල Tamil? 12")["title_digits"] == 2


def test_hash_radius_index_matches_brute_force():
    generator = np.random.default_rng(123)
    values = [int(x) for x in generator.integers(0, 2**63, 300)]
    values.extend([values[0] ^ 1, values[0] ^ 3, values[0]])
    tree = BKTree()
    for value in values:
        tree.insert(value)
    for value in values[:20]:
        assert set(tree.query(value, 4)) == {x for x in values if (x ^ value).bit_count() <= 4}
    groups = UnionFind(4)
    groups.union(0, 1)
    groups.union(1, 3)
    assert groups.find(0) == groups.find(3)


def test_path_and_channel_fold_guards(settings):
    assert thumbnail_path(settings, "data\\thumbnails\\example.jpg").is_relative_to(
        settings.resolved(settings.collector_root)
    )
    with pytest.raises(ValueError):
        thumbnail_path(settings, "../../secret.jpg")
    pd.DataFrame(
        {
            "video_id": ["a", "b"],
            "channel_id": ["same", "same"],
            "title": ["t", "t"],
            "category": ["cooking", "cooking"],
            "fold": [0, 4],
            "thumb_path": ["", ""],
            "y_rel_neighbors": [1.0, 0.0],
        }
    ).to_csv(settings.training_table, index=False)
    with pytest.raises(ValueError, match="fold"):
        read_table(settings)


def test_leakage_safe_split_and_inputs():
    frame = pd.DataFrame(
        {
            "fold": [0, 1, 4, 4],
            "channel_id": ["a", "b", "c", "c"],
            "duplicate_group": ["shared", "unique", "shared", "other"],
            "category": ["cooking"] * 4,
            "title": ["Title"] * 4,
            "views": [999999] * 4,
            "subscribers": [888] * 4,
            "y_rel_neighbors": [1.0] * 4,
            "prev_median_log_views": [999] * 4,
        }
    )
    train, test = purged_split(frame, 4)
    assert train.tolist() == [1]
    assert test.tolist() == [2, 3]
    features = pd.DataFrame({key: [None] * 4 for key in VISUAL_COLUMNS})
    inputs = predictive_inputs(frame, features, np.ones((4, 3)))
    assert not {
        "views",
        "subscribers",
        "y_rel_neighbors",
        "fold",
        "channel_id",
        "prev_median_log_views",
    } & set(inputs)


def test_transformers_fit_training_only():
    frame = pd.DataFrame(
        {
            "title": ["training alpha", "training beta", "training gamma", "training delta"],
            "category": ["cooking"] * 4,
        }
    )
    for key in ("title_length", "title_words", "title_digits", "title_questions"):
        frame[key] = [10, 20, 30, 40]
    estimator = model_pipeline("title_category", 1.0, 2)
    estimator.fit(frame, [0, 1, 0, 1])
    vocabulary = dict(estimator.named_steps["features"].named_transformers_["title"].vocabulary_)
    held = frame.iloc[:1].copy()
    held["title"] = "UNSEEN_HELDOUT_MARKER"
    estimator.predict_proba(held)
    assert estimator.named_steps["features"].named_transformers_["title"].vocabulary_ == vocabulary


def test_research_study_end_to_end_keeps_test_predictions_separate(settings, monkeypatch):
    from app.modules.module_c import evaluation

    generator = np.random.default_rng(5)
    frame = pd.DataFrame(
        [
            {
                "video_id": f"v_{channel}_{video}",
                "channel_id": f"channel_{channel}",
                "fold": channel % 5,
                "duplicate_group": f"g_{channel}_{video}",
                "title": f"Tutorial lesson sample {channel} part {video}",
                "category": ["cooking", "education", "gaming"][channel % 3],
                "title_script": "latin",
                "y_rel_neighbors": 1.0 if video % 2 else -1.0,
                "views": 999999,
            }
            for channel in range(25)
            for video in range(4)
        ]
    )
    features = pd.DataFrame({key: generator.random(len(frame)) for key in VISUAL_COLUMNS})
    embeddings = generator.normal(size=(len(frame), 4)).astype(np.float32)
    monkeypatch.setattr(
        evaluation,
        "load_features",
        lambda _: (frame, features, embeddings, {"table_sha256": "synthetic", "cache_key": "test-features"}),
    )
    report = evaluation.run_evaluation(settings, repetitions=5)
    assert report["research_only"] and report["train_rows"] == 80 and report["test_rows"] == 20
    assert set(report["results"]) == set(evaluation.EXPERIMENTS)
    assert report["results"]["prior"]["test"]["auroc"] == 0.5
    folder = settings.artifact_dir / "research" / "y_rel_neighbors"
    test_predictions = pd.read_csv(folder / "test_predictions.csv")
    development = pd.read_csv(folder / "development_predictions.csv")
    assert not set(test_predictions.video_id) & set(development.video_id)
    assert len(test_predictions) == 20
    assert json.loads((folder / "evaluation.json").read_text())["research_only"] is True


def test_cache_resume_and_fingerprint(tmp_path):
    store = FeatureStore(tmp_path / "features.sqlite")
    store.save("v1", "a", "sha", {"brightness": 0.2}, np.array([1.0, 0.0], dtype=np.float32))
    store.commit()
    assert store.contains("v1", "a", "sha")
    assert not store.contains("v2", "a", "sha")
    assert not store.contains("v1", "a", "changed")
    features, vectors = store.arrays("v1", ["a"])
    assert features == [{"brightness": 0.2}]
    np.testing.assert_array_equal(vectors, [[1, 0]])
    with pytest.raises(ValueError, match="incomplete"):
        store.arrays("v1", ["missing"])
    store.close()


def test_audit_extract_resume_and_index(settings, monkeypatch):
    from app.modules.module_c import pipeline
    from app.modules.module_c.audit import run_audit

    root = settings.resolved(settings.collector_root) / "data" / "thumbnails"
    root.mkdir(parents=True)
    generator = np.random.default_rng(9)
    rows = []
    for i in range(12):
        image = Image.fromarray(generator.integers(0, 255, (36, 64, 3), dtype=np.uint8))
        image.save(root / f"{i}.png")
        rows.append(
            {
                "video_id": str(i),
                "channel_id": f"channel_{i}",
                "title": "test title",
                "category": "cooking",
                "fold": i % 5,
                "title_script": "latin",
                "thumb_path": f"data/thumbnails/{i}.png",
                "y_rel_neighbors": float((-1) ** i),
            }
        )
    # IDs are deliberately alphanumeric; real YouTube IDs can also be all digits.
    for row in rows:
        row["video_id"] = "video_" + row["video_id"]
    pd.DataFrame(rows).to_csv(settings.training_table, index=False)
    before = settings.training_table.read_bytes()
    report = run_audit(settings, workers=1)
    assert report["rows"] == 12 and settings.training_table.read_bytes() == before

    class Encoder:
        model_id = "fake-test-encoder"
        revision = "test-revision"
        device = "cpu"

        def __init__(self, *args, **kwargs):
            pass

        def images(self, images):
            return np.tile(np.array([[1.0, 0.0, 0.0]], dtype=np.float32), (len(images), 1))

    class Detector:
        version = "no-text-detector-v1"

        def __init__(self, *args, **kwargs):
            pass

        def boxes(self, _):
            return None

    monkeypatch.setattr(pipeline, "ClipEncoder", Encoder)
    monkeypatch.setattr(pipeline, "TextDetector", Detector)
    first = pipeline.extract(settings, limit=3, allow_download=False)
    assert not first["complete"] and first["processed_this_run"] == 3
    second = pipeline.extract(settings, allow_download=False)
    assert second["complete"] and second["processed_this_run"] == 9
    assert pipeline.extract(settings, allow_download=False)["processed_this_run"] == 0
    pipeline.build_index(settings)
    service = ThumbnailService(settings)
    assert service.reference_status == "available"
    assert service.metadata["held_out_fold"] == 4
    service.encoder = Encoder()
    service.detector = Detector()
    monkeypatch.setattr(service, "_load_models", lambda: None)
    analyzed = service.analyze((root / "4.png").read_bytes(), "Test title", "cooking")
    assert analyzed.historical_comparisons
    assert all(item.thumbnail_preview for item in analyzed.historical_comparisons)
    assert "video_4" not in [item.video_id for item in analyzed.historical_comparisons]
    # Corrupt artifacts must degrade honestly rather than silently pairing wrong features and IDs.
    (settings.artifact_dir / "reference_features.json").write_text("[]")
    assert ThumbnailService(settings).reference_status == "incompatible_or_corrupt"


def reference_fixture():
    n = 12
    rows = pd.DataFrame(
        {
            "video_id": [str(i) for i in range(n)],
            "channel_id": [str(i // 4) for i in range(n)],
            "category": ["cooking"] * 11 + ["gaming"],
            "image_sha256": [str(i) for i in range(n)],
            "dhash": [f"{(2**i - 1) << 30:016x}" for i in range(n)],
            "duplicate_group": [str(i) for i in range(n)],
            "y_rel_neighbors": [(-1) ** i for i in range(n)],
        }
    )
    embeddings = np.array([[1, i / 20] for i in range(n)], dtype=np.float32)
    return ReferenceIndex(rows, pd.DataFrame({"brightness": [0.5] * n}), embeddings)


def test_retrieval_outcome_independent_diverse_and_excludes_self():
    index = reference_fixture()
    first = index.neighbors(np.array([1.0, 0]), "cooking", "0", 2**64 - 1)
    assert "0" not in [item.video_id for item in first]
    assert "11" not in [item.video_id for item in first]
    channels = [int(item.video_id) // 4 for item in first]
    assert max(channels.count(channel) for channel in channels) <= 2
    index.rows["y_rel_neighbors"] *= -1
    second = index.neighbors(np.array([1.0, 0]), "cooking", "0", 2**64 - 1)
    assert [item.video_id for item in first] == [item.video_id for item in second]


def rule_evidence():
    findings, recommendations = make_recommendations(
        {
            "brightness": 0.1,
            "contrast": 0.2,
            "saturation": 0.4,
            "text_coverage": None,
            "min_text_height_mobile": None,
        },
        "cooking",
    )
    assert all(set(r.evidence_ids) <= {f.id for f in findings} for r in recommendations)
    context = safe_context("cooking", findings, recommendations)
    assert set(context) == {"category", "findings", "approved_recommendations"}
    assert not any(
        word in json.dumps(context) for word in ["api_key", "image_sha256", "channel_id", "title", "csv"]
    )
    return findings, recommendations


def test_rule_evidence_and_safe_context():
    rule_evidence()


def valid_rewrite(recommendations):
    return json.dumps(
        {
            "recommendations": [
                {
                    "recommendation_id": r.id,
                    "evidence_ids": r.evidence_ids,
                    "explanation": "Consider inspecting the preview to decide whether an adjustment is useful.",
                }
                for r in recommendations
            ]
        }
    )


def test_writer_output_validation():
    _, recommendations = rule_evidence()
    result = validate_rewrite(valid_rewrite(recommendations), recommendations)
    assert result[0].action == recommendations[0].action
    for bad in [
        "This will increase CTR by 20%.",
        "Add a face and your views increase.",
        "A chicken dish is visible.",
    ]:
        raw = json.loads(valid_rewrite(recommendations))
        raw["recommendations"][0]["explanation"] = bad
        with pytest.raises(ValueError):
            validate_rewrite(json.dumps(raw), recommendations)
    raw = json.loads(valid_rewrite(recommendations))
    raw["recommendations"][0]["evidence_ids"] = ["invented"]
    with pytest.raises(ValueError):
        validate_rewrite(json.dumps(raw), recommendations)


def test_writer_success_missing_key_failure_timeout_and_quota(settings):
    findings, recommendations = rule_evidence()
    calls = []

    async def good(context):
        calls.append(context)
        return valid_rewrite(recommendations)

    result, status = asyncio.run(GeminiWriter(settings, good).write("cooking", findings, recommendations))
    assert result == recommendations and status.reason == "missing_api_key" and not calls
    enabled = settings.model_copy(
        update={
            "gemini_api_key": "dummy-not-real",
            "gemini_requests_per_minute": 20,
            "gemini_requests_per_day": 100,
        }
    )
    _, status = asyncio.run(GeminiWriter(enabled, good).write("cooking", findings, recommendations))
    assert status.provider == "gemini" and len(calls) == 1

    async def invalid(_):
        return "not JSON"

    _, status = asyncio.run(GeminiWriter(enabled, invalid).write("cooking", findings, recommendations))
    assert status.reason == "invalid_output"

    async def slow(_):
        await asyncio.sleep(0.2)

    short = enabled.model_copy(update={"writer_timeout_seconds": 0.01})
    _, status = asyncio.run(GeminiWriter(short, slow).write("cooking", findings, recommendations))
    assert status.reason == "timeout"

    class RateLimited(Exception):
        code = 429

    async def limited(_):
        raise RateLimited()

    writer = GeminiWriter(enabled, limited)
    _, status = asyncio.run(writer.write("cooking", findings, recommendations))
    assert status.reason == "quota_or_rate_limit"
    _, status = asyncio.run(writer.write("cooking", findings, recommendations))
    assert status.reason == "local_budget_or_cooldown"


def test_minimal_retries_and_persistent_budget(settings):
    findings, recommendations = rule_evidence()
    enabled = settings.model_copy(update={"gemini_api_key": "dummy-not-real"})
    calls = []

    class Unavailable(Exception):
        code = 503

    async def transient(_):
        calls.append(1)
        if len(calls) == 1:
            raise Unavailable()
        return valid_rewrite(recommendations)

    _, status = asyncio.run(GeminiWriter(enabled, transient).write("cooking", findings, recommendations))
    assert status.provider == "gemini" and len(calls) == 2
    assert not LocalBudget(enabled).reserve()


def test_authentication_failure_does_not_retry(settings):
    findings, recommendations = rule_evidence()
    enabled = settings.model_copy(update={"gemini_api_key": "dummy-not-real"})
    calls = []

    class Unauthorized(Exception):
        code = 401

    async def denied(_):
        calls.append(1)
        raise Unauthorized()

    original, status = asyncio.run(GeminiWriter(enabled, denied).write("cooking", findings, recommendations))
    assert len(calls) == 1 and original == recommendations and status.status == "fallback"


def test_official_gemini_sdk_request_and_response_without_network(settings, monkeypatch):
    genai = pytest.importorskip("google.genai")
    import httpx

    findings, recommendations = rule_evidence()
    captured = []

    def handle(request):
        body = json.loads(request.content)
        context = json.loads(body["contents"][0]["parts"][0]["text"])
        captured.append(context)
        assert context == safe_context("cooking", findings, recommendations)
        assert "gemini-3.5-flash-lite" in str(request.url)
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {"role": "model", "parts": [{"text": valid_rewrite(recommendations)}]},
                        "finishReason": "STOP",
                    }
                ]
            },
        )

    real_client = genai.Client

    def isolated_client(**kwargs):
        assert kwargs["vertexai"] is False
        kwargs["http_options"] = kwargs["http_options"].model_copy(
            update={"httpx_async_client": httpx.AsyncClient(transport=httpx.MockTransport(handle))}
        )
        return real_client(**kwargs)

    monkeypatch.setattr(genai, "Client", isolated_client)
    enabled = settings.model_copy(update={"gemini_api_key": "dummy-not-real"})
    result, status = asyncio.run(GeminiWriter(enabled).write("cooking", findings, recommendations))
    assert status.provider == "gemini", status
    assert len(captured) == 1 and result[0].action == recommendations[0].action


def test_alignment_requires_explicit_english(settings, monkeypatch):
    class Detector:
        version = "no-text-detector-v1"

        def boxes(self, _):
            return None

    class Encoder:
        model_id = "test-encoder"
        revision = "test-revision"

        def images(self, images):
            return np.array([[1.0, 0.0]], dtype=np.float32)

        def english_title(self, title):
            return np.array([1.0, 0.0], dtype=np.float32)

    service = ThumbnailService(settings)
    service.detector = Detector()
    service.encoder = Encoder()
    monkeypatch.setattr(service, "_load_models", lambda: None)
    assert service.analyze(image_bytes(), "romanized sinhala", "education").image_title_alignment is None
    assert service.analyze(image_bytes(), "English title", "education", "en").image_title_alignment == 1


@pytest.fixture
def client(settings, monkeypatch):
    service = ThumbnailService(settings)

    # Tests never download models or depend on optional detector/encoder packages.
    class Detector:
        version = "no-text-detector-v1"

        def boxes(self, _):
            return None

    service.detector = Detector()
    service.encoder_attempted = True
    monkeypatch.setattr(service, "_load_models", lambda: None)
    app.dependency_overrides[get_service] = lambda: service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_api_honest_fallback_and_local_language(client):
    response = client.post(
        "/api/module-c/analyze",
        data={"title": "සිංහල පාඩම", "category": "education", "title_language": "si"},
        files={"thumbnail": ("test.png", image_bytes(), "image/png")},
    )
    assert response.status_code == 200
    report = response.json()
    assert report["predicted_ctr"] is None and report["relative_performance_prediction"] is None
    assert report["image_title_alignment"] is None
    assert report["measurements"]["text_coverage"] is None
    assert report["historical_comparisons"] == []
    assert report["mobile_preview"].startswith("data:image/jpeg;base64,")
    assert client.get("/health").status_code == 200
    assert client.get("/api/module-c/status").json()["reference_index"] == "not_built"


@pytest.mark.parametrize(
    "title,category,payload,mime,expected",
    [
        ("title", "cooking", b"bad", "image/png", 422),
        ("title", "sports", image_bytes(), "image/png", 422),
        ("   ", "cooking", image_bytes(), "image/png", 422),
        ("title", "cooking", b"fake", "text/plain", 415),
        ("title", "cooking", b"a" * (10 * 1024 * 1024 + 1), "image/png", 413),
    ],
    ids=["corrupt-image", "unsupported-category", "blank-title", "unsupported-type", "oversized-image"],
)
def test_api_errors(client, title, category, payload, mime, expected):
    response = client.post(
        "/api/module-c/analyze",
        data={"title": title, "category": category},
        files={"thumbnail": ("file", payload, mime)},
    )
    assert response.status_code == expected
