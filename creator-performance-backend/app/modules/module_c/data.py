import hashlib
import json
from pathlib import Path

import pandas as pd

from .config import Settings

CATEGORIES = ("cooking", "education", "gaming")
REQUIRED = {"video_id", "channel_id", "title", "category", "fold", "thumb_path", "y_rel_neighbors"}


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_table(settings: Settings) -> pd.DataFrame:
    path = settings.resolved(settings.training_table)
    frame = pd.read_csv(
        path,
        encoding="utf-8-sig",
        keep_default_na=False,
        dtype={"video_id": str, "channel_id": str, "title": str},
    )
    missing = REQUIRED - set(frame)
    if missing:
        raise ValueError(f"Training table is missing columns: {sorted(missing)}")
    if frame.video_id.duplicated().any():
        raise ValueError("Training table contains duplicate video IDs.")
    if not frame.category.isin(CATEGORIES).all():
        raise ValueError("Training table contains unsupported categories.")
    frame["fold"] = pd.to_numeric(frame["fold"], errors="raise").astype(int)
    if not frame.fold.isin(range(5)).all() or frame.groupby("channel_id").fold.nunique().max() > 1:
        raise ValueError("Invalid channel folds; every channel must belong to exactly one fold.")
    frame["y_rel_neighbors"] = pd.to_numeric(frame.y_rel_neighbors, errors="coerce")
    frame["title"] = frame.title.fillna("").astype(str)
    return frame


def thumbnail_path(settings: Settings, stored: str) -> Path:
    root = settings.resolved(settings.collector_root)
    # Collector paths use Windows separators; support Linux research notebooks too.
    path = (root / str(stored).replace("\\", "/")).resolve()
    if not path.is_relative_to(root / "data" / "thumbnails"):
        raise ValueError("Thumbnail path is outside the collector thumbnail directory.")
    return path


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    temporary.replace(path)


def audited_table(settings: Settings) -> pd.DataFrame:
    folder = settings.artifact_dir
    report = json.loads((folder / "audit.json").read_text(encoding="utf-8"))
    if report["table_sha256"] != file_hash(settings.resolved(settings.training_table)):
        raise ValueError("Training table changed since audit. Run the audit again.")
    manifest = pd.read_csv(
        folder / "manifest.csv",
        keep_default_na=False,
        dtype={"video_id": str, "duplicate_group": str, "dhash": str},
    )
    usable = manifest[manifest.status == "ok"]
    return read_table(settings).merge(usable, on="video_id", validate="one_to_one")
