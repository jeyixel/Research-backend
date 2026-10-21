from collections import Counter

import numpy as np
import pandas as pd

from .schemas import HistoricalComparison


class ReferenceIndex:
    def __init__(self, rows: pd.DataFrame, features: pd.DataFrame, embeddings: np.ndarray):
        if not (len(rows) == len(features) == len(embeddings)):
            raise ValueError("Reference index arrays disagree.")
        if not np.isfinite(embeddings).all():
            raise ValueError("Invalid reference embeddings.")
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        if (norms < 1e-8).any():
            raise ValueError("Zero reference embeddings.")
        self.rows = rows.reset_index(drop=True)
        self.features = features.reset_index(drop=True)
        self.embeddings = embeddings / norms

    def distribution(self, category: str, metric: str) -> np.ndarray:
        if metric not in self.features:
            return np.array([])
        values = pd.to_numeric(self.features.loc[self.rows.category == category, metric], errors="coerce")
        return values.dropna().to_numpy(dtype=float)

    def neighbors(self, vector: np.ndarray, category: str, image_sha: str, dhash: int, n: int = 6):
        positions = np.flatnonzero((self.rows.category == category).to_numpy())
        if not len(positions):
            return []
        norm = np.linalg.norm(vector)
        if not np.isfinite(vector).all() or norm < 1e-8:
            raise ValueError("Invalid query embedding.")
        similarities = self.embeddings[positions] @ (vector / norm)
        order = np.argsort(-similarities, kind="stable")
        channels, seen_groups = Counter(), set()
        selected = []
        for local_index in order:
            position = positions[local_index]
            row = self.rows.iloc[position]
            # Avoid known self matches and close pixel-layout copies, irrespective of outcome.
            if row.image_sha256 == image_sha or (int(str(row.dhash), 16) ^ dhash).bit_count() <= 4:
                continue
            if channels[row.channel_id] >= 2 or row.duplicate_group in seen_groups:
                continue
            score = float(row.y_rel_neighbors)
            if not np.isfinite(score):
                continue
            selected.append(
                HistoricalComparison(
                    video_id=row.video_id,
                    source_url=f"https://www.youtube.com/watch?v={row.video_id}",
                    visual_similarity=round(float(similarities[local_index]), 6),
                    relative_view_performance=round(score, 6),
                    outcome="above_neighbor_baseline" if score > 0 else "at_or_below_neighbor_baseline",
                )
            )
            channels[row.channel_id] += 1
            seen_groups.add(row.duplicate_group)
            if len(selected) == n:
                break
        return selected
