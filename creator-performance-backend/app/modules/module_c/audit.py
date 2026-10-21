"""Audit source data without rewriting it; near matches are candidates, not proven copies."""

import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

import pandas as pd

from .config import Settings
from .data import file_hash, read_table, thumbnail_path, write_json
from .images import difference_hash, image_hash, load_image


class BKTree:
    """Exact Hamming-radius lookup for 64-bit dHashes."""

    def __init__(self):
        self.root = None

    def insert(self, value: int):
        if self.root is None:
            self.root = (value, {})
            return
        node = self.root
        while True:
            distance = (node[0] ^ value).bit_count()
            if distance == 0:
                return
            if distance not in node[1]:
                node[1][distance] = (value, {})
                return
            node = node[1][distance]

    def query(self, value: int, radius: int):
        stack = [self.root] if self.root else []
        while stack:
            key, children = stack.pop()
            distance = (key ^ value).bit_count()
            if distance <= radius:
                yield key
            stack.extend(child for gap, child in children.items() if abs(gap - distance) <= radius)


class UnionFind:
    def __init__(self, size):
        self.parents = list(range(size))

    def find(self, value):
        while self.parents[value] != value:
            self.parents[value] = self.parents[self.parents[value]]
            value = self.parents[value]
        return value

    def union(self, left, right):
        a, b = self.find(left), self.find(right)
        self.parents[max(a, b)] = min(a, b)


def run_audit(settings: Settings, workers: int = 4, radius: int = 4) -> dict:
    started = time.monotonic()
    source = settings.resolved(settings.training_table)
    original_hash = file_hash(source)
    frame = read_table(settings).sort_values("video_id").reset_index(drop=True)

    def inspect(row):
        result = {"video_id": row.video_id, "status": "ok", "image_sha256": "", "dhash": ""}
        try:
            path = thumbnail_path(settings, row.thumb_path)
            image = load_image(path.read_bytes(), settings.max_image_pixels)
            result.update(
                image_sha256=image_hash(image),
                dhash=f"{difference_hash(image):016x}",
                width=image.width,
                height=image.height,
            )
        except (OSError, ValueError):
            result["status"] = "invalid_image"
        return result

    records = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for index, record in enumerate(pool.map(inspect, frame.itertuples(index=False))):
            records.append(record)
            if (index + 1) % 2000 == 0:
                print(f"Audited {index + 1}/{len(frame)} images", flush=True)
    manifest = pd.DataFrame(records)
    groups = UnionFind(len(manifest))
    tree, representatives, exact = BKTree(), {}, {}
    pairs = []
    for i, record in enumerate(records):
        if record["status"] != "ok":
            continue
        sha = record["image_sha256"]
        if sha in exact:
            groups.union(i, exact[sha])
            # Keep a single exact-pixel copy in the research corpus.
            manifest.at[i, "status"] = "exact_duplicate"
        else:
            exact[sha] = i
        value = int(record["dhash"], 16)
        for match in tree.query(value, radius):
            j = representatives[match]
            groups.union(i, j)
            if len(pairs) < 100_000:
                pairs.append(
                    {
                        "video_id_a": record["video_id"],
                        "video_id_b": records[j]["video_id"],
                        "hamming_distance": (value ^ match).bit_count(),
                    }
                )
        tree.insert(value)
        representatives.setdefault(value, i)
    manifest["duplicate_group"] = [records[groups.find(i)]["video_id"] for i in range(len(records))]
    label_missing = frame.y_rel_neighbors.isna()
    manifest.loc[label_missing & (manifest.status == "ok"), "status"] = "missing_label"
    folder = settings.artifact_dir
    folder.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(folder / "manifest.csv", index=False)
    pd.DataFrame(pairs).to_csv(folder / "near_duplicate_candidates.csv", index=False)
    frame.merge(manifest[["video_id", "status"]], on="video_id").query("status != 'ok'").to_csv(
        folder / "exclusions.csv", index=False
    )
    review = []
    for _, part in frame.groupby("category"):
        channels = (
            part[["channel_id"]]
            .drop_duplicates()
            .sample(n=min(10, part.channel_id.nunique()), random_state=42)
        )
        selection = part[part.channel_id.isin(channels.channel_id)].groupby("channel_id").head(3).copy()
        selection["category_correct"] = ""
        selection["sri_lanka_relevant"] = ""
        selection["review_notes"] = ""
        review.append(selection)
    pd.concat(review).to_csv(folder / "channel_review.csv", index=False, encoding="utf-8-sig")
    distributions = {}
    for column in ["category", "title_script", "fold", "thumb_quality"]:
        if column in frame:
            distributions[column] = {str(k): int(v) for k, v in frame[column].value_counts().items()}
    for column in ["age_days", "subscribers"]:
        if column in frame:
            distributions[column] = json.loads(
                pd.to_numeric(frame[column], errors="coerce").describe().to_json()
            )
    final_hash = file_hash(source)
    if original_hash != final_hash:
        raise ValueError("Training table changed during audit. Re-run after collection finishes.")
    report = {
        "version": "audit-v1",
        "created_at": datetime.now(UTC).isoformat(),
        "table_sha256": original_hash,
        "rows": len(frame),
        "channels": frame.channel_id.nunique(),
        "status_counts": {str(k): int(v) for k, v in manifest.status.value_counts().items()},
        "distributions": distributions,
        "near_duplicate_radius": radius,
        "duplicate_groups": manifest.duplicate_group.nunique(),
        "near_duplicate_pairs_saved": len(pairs),
        "seconds": round(time.monotonic() - started, 1),
        "human_review_status": "pending",
        "notes": [
            "Near-duplicate groups are conservative candidates and are purged across model splits.",
            "Category and locality require human review; script is not language.",
            "Public collection-time views are not CTR or fixed-age outcomes.",
        ],
    }
    write_json(folder / "audit.json", report)
    print(json.dumps(report, indent=2), flush=True)
    return report
