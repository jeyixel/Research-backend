#!/usr/bin/env python3
"""
Build the training table for Module E (channel/view-range model) and Module C (packaging model)
from data/yt.db.

No CTR or retention is available from the public API, so targets are *relative performance proxies*:

  y_log_views       log(1 + views)                       -> Module E target (use with past-only features)
  y_rel_neighbors   log_views - median log_views of the  -> Module C target ("did this video beat what
                    ~10 videos either side of it            this channel normally gets?", channel size
                                                            and drift cancel out)
  y_rel_prev        log_views - median log_views of the  -> alternative E target (delta vs. channel baseline)
                    previous ~10 videos
  y_rank_in_channel percentile of log_views in channel   -> robust ranking target

`prev_*` features only use videos published *before* the row, so they are safe to use as model inputs.
`fold` is a channel-level fold (0-4): use GroupKFold-style splits on it so you measure generalisation
to channels the model has never seen.
"""
import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


def per_channel_features(g, k, min_neighbors, min_prev):
    g = g.sort_values("published_at").reset_index(drop=True)
    n = len(g)
    lv = g["log_views"].to_numpy()
    like_rate = (g["likes"] / g["views"].replace(0, np.nan)).to_numpy(dtype=float)
    comment_rate = (g["comments"] / g["views"].replace(0, np.nan)).to_numpy(dtype=float)
    days = ((g["published_at"] - pd.Timestamp("1970-01-01", tz="UTC")).dt.total_seconds() / 86400).to_numpy()

    nb = np.full(n, np.nan)
    prev = np.full(n, np.nan)
    gap = np.full(n, np.nan)
    p_like = np.full(n, np.nan)
    p_comment = np.full(n, np.nan)
    for i in range(n):
        lo = max(0, i - k)
        neigh = np.concatenate([lv[lo:i], lv[i + 1:min(n, i + k + 1)]])
        if len(neigh) >= min_neighbors:
            nb[i] = np.median(neigh)
        if i - lo >= min_prev:
            prev[i] = np.median(lv[lo:i])
            gap[i] = (days[i] - days[lo]) / (i - lo)
            p_like[i] = pd.Series(like_rate[lo:i]).median()
            p_comment[i] = pd.Series(comment_rate[lo:i]).median()

    g["neighbor_median_log_views"] = nb
    g["prev_median_log_views"] = prev
    g["prev_avg_gap_days"] = gap
    g["prev_median_like_rate"] = p_like
    g["prev_median_comment_rate"] = p_comment
    g["y_rel_neighbors"] = g["log_views"] - g["neighbor_median_log_views"]
    g["y_rel_prev"] = g["log_views"] - g["prev_median_log_views"]
    g["y_rank_in_channel"] = g["log_views"].rank(pct=True)
    g["like_rate"] = like_rate
    g["comment_rate"] = comment_rate
    return g


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default="data/yt.db")
    ap.add_argument("--out", default="data/training_table.csv")
    ap.add_argument("--min-age-days", type=int, default=30, help="drop videos whose views have not settled yet")
    ap.add_argument("--min-duration-s", type=int, default=181, help="drop Shorts / very short clips (default: > 3 min)")
    ap.add_argument("--min-channel-videos", type=int, default=15)
    ap.add_argument("--window", type=int, default=10, help="neighbour / history window (videos)")
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    df = pd.read_sql_query(
        """SELECT v.*, c.category, c.title AS channel_title, c.subscribers, c.country AS channel_country
           FROM videos v JOIN channels c ON c.channel_id = v.channel_id""", conn)
    print(f"raw videos: {len(df)}  channels: {df['channel_id'].nunique()}")

    df["published_at"] = pd.to_datetime(df["published_at"], utc=True)
    df["fetched_at"] = pd.to_datetime(df["fetched_at"], utc=True)
    df["age_days"] = (df["fetched_at"] - df["published_at"]).dt.total_seconds() / 86400

    df = df[df["views"].notna()]
    df = df[df["duration_s"] >= args.min_duration_s]
    df = df[df["age_days"] >= args.min_age_days]
    df = df.copy()
    df["log_views"] = np.log1p(df["views"])
    counts = df.groupby("channel_id")["video_id"].transform("count")
    df = df[counts >= args.min_channel_videos]
    print(f"after filters (long-form, >= {args.min_age_days} days old, "
          f">= {args.min_channel_videos} videos/channel): {len(df)} videos, {df['channel_id'].nunique()} channels")
    if df.empty:
        raise SystemExit("Nothing left after filtering. Collect more data or relax the filters.")

    parts = [per_channel_features(g, args.window, min_neighbors=6, min_prev=3)
             for _, g in df.groupby("channel_id")]
    df = pd.concat(parts, ignore_index=True)

    local = df["published_at"].dt.tz_convert("Asia/Colombo")
    df["upload_hour_lk"] = local.dt.hour
    df["upload_dow_lk"] = local.dt.dayofweek
    df["title_len"] = df["title"].str.len()
    df["title_words"] = df["title"].str.split().str.len()
    df["tag_count"] = df["tags"].apply(lambda s: len(json.loads(s)) if isinstance(s, str) and s else 0)
    df["fold"] = df["channel_id"].apply(lambda c: int(hashlib.md5(c.encode()).hexdigest(), 16) % 5)
    df["y_log_views"] = df["log_views"]

    cols = [
        "video_id", "channel_id", "channel_title", "category", "fold", "published_at", "age_days",
        "title", "title_script", "title_len", "title_words", "duration_s", "tag_count",
        "upload_hour_lk", "upload_dow_lk", "thumb_path", "thumb_quality",
        "views", "likes", "comments", "like_rate", "comment_rate", "subscribers",
        "prev_median_log_views", "prev_avg_gap_days", "prev_median_like_rate", "prev_median_comment_rate",
        "y_log_views", "y_rel_prev", "y_rel_neighbors", "y_rank_in_channel",
    ]
    out = df[cols]
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False, encoding="utf-8-sig")

    print(f"\nwrote {args.out}: {len(out)} rows")
    print(out.groupby("category").agg(channels=("channel_id", "nunique"), videos=("video_id", "count")))
    print("\ntarget summary:")
    print(out[["y_log_views", "y_rel_prev", "y_rel_neighbors", "y_rank_in_channel"]].describe().round(2))
    print("\nreminders: use `fold` for channel-level CV; do NOT feed channel-level inputs (subscribers, channel id) "
          "into Module C; `subscribers` is a snapshot at collection time, so treat it as approximate for E.")


if __name__ == "__main__":
    main()
