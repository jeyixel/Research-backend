"""Local versioned extraction cache. Public corpus only, never creator uploads."""

import json
import sqlite3
from pathlib import Path

import numpy as np


class FeatureStore:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.execute("""CREATE TABLE IF NOT EXISTS features (
            cache_key TEXT NOT NULL, video_id TEXT NOT NULL, image_sha256 TEXT NOT NULL,
            features_json TEXT NOT NULL, embedding BLOB NOT NULL,
            PRIMARY KEY(cache_key, video_id))""")

    def contains(self, key: str, video_id: str, image_sha: str) -> bool:
        return (
            self.connection.execute(
                "SELECT 1 FROM features WHERE cache_key=? AND video_id=? AND image_sha256=?",
                (key, video_id, image_sha),
            ).fetchone()
            is not None
        )

    def save(self, key: str, video_id: str, image_sha: str, features: dict, embedding: np.ndarray):
        self.connection.execute(
            "INSERT OR REPLACE INTO features VALUES (?,?,?,?,?)",
            (
                key,
                video_id,
                image_sha,
                json.dumps(features, allow_nan=False),
                embedding.astype("float32").tobytes(),
            ),
        )

    def arrays(self, key: str, video_ids: list[str]):
        rows = {
            row[0]: row
            for row in self.connection.execute(
                "SELECT video_id, features_json, embedding FROM features WHERE cache_key=?", (key,)
            )
        }
        missing = set(video_ids) - set(rows)
        if missing:
            raise ValueError(f"Feature cache is incomplete: {len(missing)} missing videos. Resume extract.")
        return (
            [json.loads(rows[vid][1]) for vid in video_ids],
            np.stack([np.frombuffer(rows[vid][2], dtype=np.float32) for vid in video_ids]),
        )

    def commit(self):
        self.connection.commit()

    def close(self):
        self.connection.close()
