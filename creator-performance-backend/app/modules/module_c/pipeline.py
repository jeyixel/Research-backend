import hashlib
import json
import time
from datetime import UTC, datetime

import numpy as np
import pandas as pd

from .config import Settings
from .data import audited_table, file_hash, thumbnail_path, write_json
from .embeddings import ClipEncoder
from .features import TextDetector, visual_features
from .images import PREPROCESSING_VERSION, image_hash, load_image
from .store import FeatureStore


def extract(settings: Settings, limit: int | None = None, allow_download: bool = True):
    frame = audited_table(settings).sort_values("video_id").reset_index(drop=True)
    encoder = ClipEncoder(settings, allow_download=allow_download)
    detector = TextDetector(settings, allow_download=allow_download)
    config = {
        "model": encoder.model_id,
        "revision": encoder.revision,
        "preprocessing": PREPROCESSING_VERSION,
        "detector": detector.version,
        "visual_features": "luma-hsv-boxes-v1",
    }
    key = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    store = FeatureStore(settings.artifact_dir / "features.sqlite")
    table_sha = file_hash(settings.resolved(settings.training_table))
    todo = [
        row
        for row in frame.itertuples(index=False)
        if not store.contains(key, row.video_id, row.image_sha256)
    ]
    if limit:
        todo = todo[:limit]
    started = time.monotonic()
    processed = 0
    batch_size = settings.batch_size
    try:
        while processed < len(todo):
            batch = todo[processed : processed + batch_size]
            images = [
                load_image(thumbnail_path(settings, row.thumb_path).read_bytes(), settings.max_image_pixels)
                for row in batch
            ]
            if any(image_hash(image) != row.image_sha256 for row, image in zip(batch, images)):
                raise ValueError("A thumbnail changed after audit. Re-run audit before extraction.")
            try:
                embeddings = encoder.images(images)
            except RuntimeError as exc:
                if not encoder.is_memory_error(exc) or batch_size == 1:
                    raise
                batch_size = max(1, batch_size // 2)
                encoder.clear_memory()
                print(f"GPU memory limit; retrying with batch size {batch_size}", flush=True)
                continue
            for row, image, embedding in zip(batch, images, embeddings):
                features = visual_features(image, detector)
                store.save(key, row.video_id, row.image_sha256, features, embedding)
            store.commit()
            processed += len(batch)
            if processed % 128 < batch_size or processed == len(todo):
                elapsed = max(time.monotonic() - started, 0.001)
                print(f"Extracted {processed}/{len(todo)} at {processed / elapsed:.1f} images/s", flush=True)
        complete = all(
            store.contains(key, row.video_id, row.image_sha256) for row in frame.itertuples(index=False)
        )
        manifest = {
            **config,
            "cache_key": key,
            "table_sha256": table_sha,
            "audit_manifest_sha256": file_hash(settings.artifact_dir / "manifest.csv"),
            "complete": complete,
            "corpus_rows": len(frame),
            "processed_this_run": processed,
            "seconds": round(time.monotonic() - started, 2),
            "device": encoder.device,
            "batch_size": batch_size,
            "created_at": datetime.now(UTC).isoformat(),
        }
        write_json(settings.artifact_dir / "extraction.json", manifest)
        print(json.dumps(manifest, indent=2), flush=True)
        return manifest
    finally:
        store.close()


def load_features(settings: Settings):
    metadata = json.loads((settings.artifact_dir / "extraction.json").read_text(encoding="utf-8"))
    if not metadata["complete"]:
        raise ValueError("Extraction is incomplete; resume extract without --limit.")
    if metadata["table_sha256"] != file_hash(settings.resolved(settings.training_table)):
        raise ValueError("Training table changed since extraction.")
    if metadata["audit_manifest_sha256"] != file_hash(settings.artifact_dir / "manifest.csv"):
        raise ValueError("Audit changed since extraction. Run extract again.")
    frame = audited_table(settings).sort_values("video_id").reset_index(drop=True)
    store = FeatureStore(settings.artifact_dir / "features.sqlite")
    try:
        features, embeddings = store.arrays(metadata["cache_key"], frame.video_id.tolist())
    finally:
        store.close()
    return frame, pd.DataFrame(features), embeddings, metadata


def build_index(settings: Settings):
    frame, features, embeddings, metadata = load_features(settings)
    # Final-test images and their near-duplicate groups never enter the reference corpus.
    held_out_groups = set(frame.loc[frame.fold == 4, "duplicate_group"])
    keep = (frame.fold != 4) & ~frame.duplicate_group.isin(held_out_groups)
    if not keep.any():
        raise ValueError("No reference data remains after holdout/duplicate purging.")
    selected = frame.loc[keep].reset_index(drop=True)
    safe_columns = [
        "video_id",
        "channel_id",
        "category",
        "title_script",
        "image_sha256",
        "dhash",
        "duplicate_group",
        "y_rel_neighbors",
        "thumb_path",
    ]
    selected[safe_columns].to_csv(settings.artifact_dir / "index.csv", index=False)
    features.loc[keep].reset_index(drop=True).to_json(
        settings.artifact_dir / "reference_features.json", orient="records"
    )
    np.save(settings.artifact_dir / "index_embeddings.npy", embeddings[keep.to_numpy()], allow_pickle=False)
    write_json(
        settings.artifact_dir / "index.json",
        {
            **metadata,
            "reference_rows": int(keep.sum()),
            "reference_folds": [0, 1, 2, 3],
            "held_out_fold": 4,
            "index_sha256": file_hash(settings.artifact_dir / "index.csv"),
            "reference_features_sha256": file_hash(settings.artifact_dir / "reference_features.json"),
            "embeddings_sha256": file_hash(settings.artifact_dir / "index_embeddings.npy"),
        },
    )
    print(f"Indexed {keep.sum()} development thumbnails; fold 4 and matching duplicate groups excluded.")
