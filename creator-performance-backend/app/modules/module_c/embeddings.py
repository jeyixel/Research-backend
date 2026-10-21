import threading

import numpy as np

from .config import Settings
from .images import square_image


class ClipEncoder:
    def __init__(self, settings: Settings, allow_download: bool = False):
        import torch
        from transformers import CLIPModel, CLIPProcessor

        self.torch = torch
        self.lock = threading.Lock()
        self.device = (
            ("cuda" if torch.cuda.is_available() else "cpu") if settings.device == "auto" else settings.device
        )
        kwargs = {
            "revision": settings.clip_revision,
            "local_files_only": not allow_download,
            "cache_dir": str(settings.artifact_dir / ".cache" / "huggingface"),
        }
        self.processor = CLIPProcessor.from_pretrained(settings.clip_model, **kwargs)
        self.model = CLIPModel.from_pretrained(settings.clip_model, **kwargs).eval().to(self.device)
        self.model.requires_grad_(False)
        self.revision = getattr(self.model.config, "_commit_hash", None) or settings.clip_revision
        self.model_id = settings.clip_model

    def _normalize(self, values):
        values = values.float()
        values = values / values.norm(dim=-1, keepdim=True).clamp_min(1e-12)
        return values.cpu().numpy().astype(np.float32)

    def images(self, images) -> np.ndarray:
        with self.lock, self.torch.inference_mode():
            inputs = self.processor(images=[square_image(image) for image in images], return_tensors="pt")
            inputs = {key: value.to(self.device) for key, value in inputs.items()}
            return self._normalize(self.model.get_image_features(**inputs))

    def english_title(self, title: str) -> np.ndarray:
        with self.lock, self.torch.inference_mode():
            inputs = self.processor(text=[title], return_tensors="pt", truncation=True, padding=True)
            inputs = {key: value.to(self.device) for key, value in inputs.items()}
            return self._normalize(self.model.get_text_features(**inputs))[0]

    def is_memory_error(self, error: Exception) -> bool:
        return isinstance(error, self.torch.cuda.OutOfMemoryError)

    def clear_memory(self):
        if self.device == "cuda":
            self.torch.cuda.empty_cache()
