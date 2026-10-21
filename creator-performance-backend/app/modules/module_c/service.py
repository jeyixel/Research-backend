import json
import threading

import numpy as np
import pandas as pd

from .config import Settings
from .data import file_hash, thumbnail_path
from .embeddings import ClipEncoder
from .features import TextDetector, title_features, visual_features
from .images import PREPROCESSING_VERSION, difference_hash, image_hash, load_image, mobile_preview
from .recommendations import make_recommendations
from .retrieval import ReferenceIndex
from .schemas import Report
from .writers import make_writer


class ThumbnailService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.writer = make_writer(settings)
        self.lock = threading.Lock()
        self.encoder = None
        self.detector = None
        self.references = None
        self.metadata = {}
        self.reference_status = "not_built"
        self.encoder_attempted = False
        path = settings.artifact_dir
        try:
            metadata = json.loads((path / "index.json").read_text(encoding="utf-8"))
            if metadata["preprocessing"] != PREPROCESSING_VERSION:
                raise ValueError("Incompatible reference preprocessing.")
            if metadata["index_sha256"] != file_hash(path / "index.csv"):
                raise ValueError("Reference index changed.")
            if metadata["reference_features_sha256"] != file_hash(path / "reference_features.json"):
                raise ValueError("Reference features changed.")
            if metadata["embeddings_sha256"] != file_hash(path / "index_embeddings.npy"):
                raise ValueError("Reference embeddings changed.")
            rows = pd.read_csv(
                path / "index.csv",
                dtype={"video_id": str, "channel_id": str, "duplicate_group": str, "dhash": str},
                keep_default_na=False,
            )
            features = pd.read_json(path / "reference_features.json", orient="records")
            embeddings = np.load(path / "index_embeddings.npy", allow_pickle=False)
            self.references = ReferenceIndex(rows, features, embeddings)
            self.metadata = metadata
            self.reference_status = "available"
        except FileNotFoundError:
            pass
        except (ValueError, KeyError, OSError):
            self.reference_status = "incompatible_or_corrupt"

    def _load_models(self):
        if self.detector is None:
            self.detector = TextDetector(self.settings, allow_download=False)
        if not self.encoder_attempted:
            self.encoder_attempted = True
            try:
                # Follow the exact resolved encoder revision used by the reference index.
                settings = self.settings
                if self.metadata:
                    settings = settings.model_copy(
                        update={
                            "clip_model": self.metadata["model"],
                            "clip_revision": self.metadata["revision"],
                        }
                    )
                self.encoder = ClipEncoder(settings, allow_download=False)
            except (ImportError, OSError, RuntimeError, ValueError):
                self.encoder = None

    def status(self):
        return {
            "module": "C_thumbnail_expert",
            "reference_index": self.reference_status,
            "reference_rows": len(self.references.rows) if self.references else 0,
            "prediction_mode": "research_only",
            "report_language": "en",
            "writer_configured": self.settings.writer,
            "gemini_key_configured": bool(self.settings.gemini_api_key),
            "data_version": self.metadata.get("table_sha256"),
        }

    def analyze(self, data: bytes, title: str, category: str, title_language: str = "unknown") -> Report:
        if len(data) > self.settings.max_upload_bytes:
            raise ValueError("Image exceeds the upload size limit.")
        image = load_image(data, self.settings.max_image_pixels)
        # GPU models are shared; serialize inference to bound memory and avoid unsafe concurrent detector calls.
        with self.lock:
            self._load_models()
            measurements = visual_features(image, self.detector)
            detection_status = measurements.pop("text_detection_status")
            references = self.references
            detector_matches = not self.metadata or self.detector.version == self.metadata["detector"]
            # Never compare live detector geometry with a corpus extracted by a different detector.
            if not detector_matches:
                for metric in (
                    "text_coverage",
                    "text_regions",
                    "min_text_height_mobile",
                    "median_text_height_mobile",
                ):
                    measurements[metric] = None
                detection_status = "reference_detector_mismatch"
            findings, recommendations = make_recommendations(measurements, category, references)
            comparisons, alignment = [], None
            embedding_status = "unavailable"
            alignment_status = "not_assessed_language"
            if self.encoder:
                try:
                    vector = self.encoder.images([image])[0]
                    embedding_status = "available"
                    if references is not None:
                        comparisons = references.neighbors(
                            vector, category, image_hash(image), difference_hash(image)
                        )
                        for comparison in comparisons:
                            stored = references.rows.loc[
                                references.rows.video_id == comparison.video_id
                            ].iloc[0]
                            try:
                                historical = load_image(
                                    thumbnail_path(self.settings, stored["thumb_path"]).read_bytes(),
                                    self.settings.max_image_pixels,
                                )
                                if image_hash(historical) == stored.image_sha256:
                                    comparison.thumbnail_preview = mobile_preview(historical)
                            except (KeyError, ValueError, OSError):
                                # The evidence record remains valid if its source image was removed.
                                pass
                    if title_language == "en":
                        alignment = round(float(vector @ self.encoder.english_title(title)), 6)
                        alignment_status = "experimental_english_similarity"
                except (RuntimeError, ValueError):
                    embedding_status = "inference_failed"
                    alignment_status = "unavailable"
            elif title_language == "en":
                alignment_status = "unavailable"
        limitations = [
            "Public relative views are not CTR, thumbnail quality, or evidence of redesign uplift.",
            "Historical outcomes reflect exposure, topic, video content, age, and possible packaging changes.",
            "Category percentiles are descriptive references, not optimal design targets.",
            "Text boxes do not establish legibility; text recognition and face/emotion analysis are not performed.",
            "Local-script text detection and English CLIP similarity require in-domain human validation.",
            "Recommendations are design hypotheses; the predictive models remain research-only.",
        ]
        if not references:
            limitations.append(
                "Historical comparison/reference artifacts are unavailable; this report uses local measurements."
            )
        if detection_status != "available":
            limitations.append("Text-region measurements are unavailable; no absence of text is inferred.")
        if alignment is not None:
            limitations.append(
                "Image/title cosine similarity is uncalibrated and is not a factual-content or honesty check."
            )
        return Report(
            category=category,
            title_language=title_language,
            measurements=measurements,
            title_features=title_features(title),
            findings=findings,
            recommendations=recommendations,
            capabilities={
                "image_embeddings": embedding_status,
                "text_detection": detection_status,
                "text_recognition": "not_performed",
                "historical_comparison": self.reference_status,
                "image_title_alignment": alignment_status,
                "outcome_prediction": "research_only",
            },
            historical_comparisons=comparisons,
            image_title_alignment=alignment,
            mobile_preview=mobile_preview(image),
            limitations=limitations,
            provenance={
                "data_version": self.metadata.get("table_sha256"),
                "embedding_model": self.encoder.model_id if self.encoder else None,
                "embedding_revision": self.encoder.revision if self.encoder else None,
                "preprocessing_version": PREPROCESSING_VERSION,
                "reference_rows": len(references.rows) if references else 0,
                "reference_folds": "0,1,2,3; final-test duplicate groups excluded",
            },
        )

    async def word_report(self, report: Report):
        recommendations, wording = await self.writer.write(
            report.category, report.findings, report.recommendations
        )
        return report.model_copy(update={"recommendations": recommendations, "wording": wording})
