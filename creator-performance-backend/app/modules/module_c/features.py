"""Measured image properties; text boxes do not establish human readability."""

import importlib.metadata
import threading

import numpy as np
from PIL import Image, ImageOps

from .config import Settings

VISUAL_COLUMNS = [
    "brightness",
    "contrast",
    "saturation",
    "text_coverage",
    "text_regions",
    "min_text_height_mobile",
    "median_text_height_mobile",
]
TITLE_COLUMNS = ["title_length", "title_words", "title_digits", "title_questions"]


def title_features(title: str) -> dict:
    return {
        "title_length": len(title),
        "title_words": len(title.split()),
        "title_digits": sum(char.isdigit() for char in title),
        "title_questions": title.count("?"),
    }


class TextDetector:
    def __init__(self, settings: Settings, allow_download: bool = False):
        self.reader = None
        self.status = "disabled" if not settings.ocr_enabled else "unavailable"
        self.lock = threading.Lock()
        if not settings.ocr_enabled:
            return
        try:
            import easyocr
            import torch

            directory = settings.artifact_dir / ".cache" / "easyocr"
            if allow_download:
                directory.mkdir(parents=True, exist_ok=True)
            device = torch.cuda.is_available() if settings.device == "auto" else settings.device == "cuda"
            self.reader = easyocr.Reader(
                ["en"],
                gpu=device,
                recognizer=False,
                detector=True,
                download_enabled=allow_download,
                model_storage_directory=str(directory),
                user_network_directory=str(directory / "user_network"),
                verbose=False,
            )
            self.status = "available"
        except (ImportError, OSError, RuntimeError, ValueError, FileNotFoundError):
            self.reader = None

    @property
    def version(self):
        if self.reader is None:
            return "no-text-detector-v1"
        return "craft-" + importlib.metadata.version("easyocr") + "-geometry-v1"

    def boxes(self, image: Image.Image) -> list[tuple[int, int, int, int]] | None:
        if self.reader is None:
            return None
        try:
            with self.lock:
                horizontal, free = self.reader.detect(np.asarray(image))
            boxes = [(int(x0), int(y0), int(x1), int(y1)) for x0, x1, y0, y1 in horizontal[0]]
            for polygon in free[0]:
                points = np.asarray(polygon)
                boxes.append(
                    (
                        int(points[:, 0].min()),
                        int(points[:, 1].min()),
                        int(points[:, 0].max()),
                        int(points[:, 1].max()),
                    )
                )
            return boxes
        except (RuntimeError, ValueError):
            return None


def visual_features(image: Image.Image, detector: TextDetector | None = None) -> dict:
    image = ImageOps.contain(image, (640, 640), method=Image.Resampling.LANCZOS)
    rgb = np.asarray(image, dtype=np.float32) / 255.0
    luminance = rgb @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    saturation = np.asarray(image.convert("HSV"), dtype=np.float32)[:, :, 1] / 255.0
    result = {
        "brightness": round(float(luminance.mean()), 6),
        "contrast": round(float(luminance.std()), 6),
        "saturation": round(float(saturation.mean()), 6),
        "text_coverage": None,
        "text_regions": None,
        "min_text_height_mobile": None,
        "median_text_height_mobile": None,
        "text_detection_status": "unavailable",
    }
    boxes = detector.boxes(image) if detector else None
    if boxes is not None:
        mask = np.zeros((image.height, image.width), dtype=bool)
        heights = []
        mobile_scale = min(320 / image.width, 180 / image.height)
        for x0, y0, x1, y1 in boxes:
            x0, x1 = max(0, x0), min(image.width, x1)
            y0, y1 = max(0, y0), min(image.height, y1)
            if x1 > x0 and y1 > y0:
                mask[y0:y1, x0:x1] = True
                heights.append((y1 - y0) * mobile_scale)
        result.update(
            text_coverage=round(float(mask.mean()), 6),
            text_regions=len(heights),
            min_text_height_mobile=round(min(heights), 2) if heights else None,
            median_text_height_mobile=round(float(np.median(heights)), 2) if heights else None,
            text_detection_status="available",
        )
    return result
