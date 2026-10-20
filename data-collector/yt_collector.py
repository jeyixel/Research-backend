#!/usr/bin/env python3
"""
YouTube corpus collector for the Sri Lankan creator project (Modules E and C).

Commands
  discover   find candidate Sri Lankan channels (search.list, 100 units/call) -> data/candidates.csv
  collect    pull channel + video metadata for channels in a CSV              -> data/yt.db
  thumbs     download thumbnails for collected videos (no API quota used)     -> data/thumbnails/
  export     dump the SQLite tables to CSV                                    -> data/export/
  stats      print a coverage summary

Typical flow
  python yt_collector.py discover
  (review data/candidates.csv, mark approve=y, add your own channels)
  python yt_collector.py collect --channels data/candidates.csv
  python yt_collector.py collect --channels channels.csv
  python yt_collector.py thumbs
  python yt_collector.py stats
"""
import argparse
import csv
import io
import json
import os
import re
import sqlite3
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

API = "https://www.googleapis.com/youtube/v3"
DATA_DIR = Path("data")
DB_PATH = DATA_DIR / "yt.db"
THUMB_DIR = DATA_DIR / "thumbnails"
CATEGORIES = {"gaming", "education", "cooking"}

# Edit freely. Each search.list page costs 100 quota units.
QUERIES = {
    "gaming": [
        "sinhala gaming", "sri lanka gamer", "sinhala gameplay", "sinhala free fire",
        "sinhala pubg mobile", "sinhala minecraft", "sri lankan gaming channel",
        "tamil gaming sri lanka",
    ],
    "education": [
        "sinhala education", "A/L physics sinhala", "O/L maths sinhala",
        "grade 5 scholarship sinhala", "sri lanka online classes", "sinhala lessons",
        "sinhala science lessons", "english lessons sinhala medium", "ICT sinhala",
    ],
    "cooking": [
        "sinhala recipes", "sri lankan food recipes", "sinhala cooking",
        "sri lankan village cooking", "kottu recipe sinhala", "sri lankan rice and curry",
        "සිංහල රෙසිපි", "இலங்கை சமையல்",
    ],
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS channels (
  channel_id TEXT PRIMARY KEY, handle TEXT, title TEXT, category TEXT, country TEXT,
  default_language TEXT, created_at TEXT, subscribers INTEGER, hidden_subscribers INTEGER,
  total_views INTEGER, video_count INTEGER, uploads_playlist TEXT,
  videos_collected INTEGER, fetched_at TEXT
);
CREATE TABLE IF NOT EXISTS videos (
  video_id TEXT PRIMARY KEY, channel_id TEXT, title TEXT, description TEXT,
  published_at TEXT, duration_s INTEGER, yt_category_id TEXT,
  default_language TEXT, default_audio_language TEXT, tags TEXT,
  views INTEGER, likes INTEGER, comments INTEGER, title_script TEXT,
  thumb_url TEXT, thumb_fallback_url TEXT, thumb_quality TEXT, thumb_path TEXT,
  fetched_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_videos_channel ON videos(channel_id);
"""


# --------------------------------------------------------------------------- helpers
class QuotaExceeded(Exception):
    pass


class Api:
    """Thin YouTube Data API v3 client with a local quota counter and retries."""

    def __init__(self, key, budget):
        self.key, self.budget, self.used = key, budget, 0
        self.session = requests.Session()

    def get(self, endpoint, **params):
        cost = 100 if endpoint == "search" else 1
        if self.used + cost > self.budget:
            raise QuotaExceeded(f"local budget reached ({self.used}/{self.budget} units)")
        params["key"] = self.key
        last = None
        for attempt in range(5):
            try:
                r = self.session.get(f"{API}/{endpoint}", params=params, timeout=30)
            except requests.RequestException as e:
                last = str(e)
                time.sleep(2 ** attempt)
                continue
            if r.status_code >= 500:
                last = f"HTTP {r.status_code}"
                time.sleep(2 ** attempt)
                continue
            self.used += cost  # YouTube bills failed (4xx) requests too
            if r.status_code == 200:
                return r.json()
            try:
                reason = r.json()["error"]["errors"][0]["reason"]
            except Exception:
                reason = ""
            if reason in ("quotaExceeded", "dailyLimitExceeded"):
                raise QuotaExceeded("YouTube reports the daily quota is exhausted")
            if reason == "rateLimitExceeded":
                time.sleep(2 ** attempt)
                continue
            raise RuntimeError(f"{endpoint} failed: HTTP {r.status_code} {reason} {r.text[:200]}")
        raise RuntimeError(f"{endpoint} failed after retries: {last}")


def db():
    DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    return conn


def upsert(conn, table, pk, row):
    cols = list(row)
    updates = ", ".join(f"{c}=excluded.{c}" for c in cols if c != pk)
    sql = (f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join('?' * len(cols))}) "
           f"ON CONFLICT({pk}) DO UPDATE SET {updates}")
    conn.execute(sql, [row[c] for c in cols])


def to_int(x):
    return int(x) if x not in (None, "") else None


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


_DUR = re.compile(r"^P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$")


def parse_duration(s):
    m = _DUR.match(s or "")
    if not m:
        return 0
    d, h, mi, sec = (int(x or 0) for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + sec


def title_script(title):
    """Dominant script of a title. Romanised Sinhala ('Singlish') shows up as 'latin'."""
    letters = [c for c in title if c.isalpha()]
    if not letters:
        return "none"
    si = sum("\u0d80" <= c <= "\u0dff" for c in letters) / len(letters)
    ta = sum("\u0b80" <= c <= "\u0bff" for c in letters) / len(letters)
    la = sum(c.isascii() for c in letters) / len(letters)
    best, name = max((si, "sinhala"), (ta, "tamil"), (la, "latin"))
    return name if best >= 0.7 else "mixed"


def parse_ref(ref):
    """Turn a UC id, @handle, or channel URL into an API lookup parameter."""
    ref = ref.strip()
    m = re.fullmatch(r"UC[\w-]{22}", ref) or re.search(r"channel/(UC[\w-]{22})", ref)
    if m:
        return "id", m.group(m.lastindex or 0)
    if ref.startswith("@"):
        return "forHandle", ref
    m = re.search(r"youtube\.com/(@[^/?#\s]+)", ref)
    if m:
        return "forHandle", m.group(1)
    m = re.search(r"youtube\.com/user/([^/?#\s]+)", ref)
    if m:
        return "forUsername", m.group(1)
    return None, ref


def read_channels_csv(path):
    """Needs columns `channel` and `category`. If an `approve` column exists, only y/yes/1/x rows are used."""
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        has_approve = "approve" in (reader.fieldnames or [])
        for r in reader:
            if not (r.get("channel") or "").strip():
                continue
            if has_approve and (r.get("approve") or "").strip().lower() not in ("y", "yes", "1", "x", "true"):
                continue
            rows.append({"channel": r["channel"].strip(), "category": (r.get("category") or "").strip().lower()})
    return rows


def make_api(args):
    key = os.environ.get("YT_API_KEY")
    if not key:
        sys.exit("Missing YT_API_KEY. Put it in a .env file (see .env.example).")
    return Api(key, args.quota_budget)


# --------------------------------------------------------------------------- discover
def cmd_discover(args):
    api = make_api(args)
    found = {}  # channel_id -> {"queries": set, "cats": Counter}
    try:
        for cat, queries in QUERIES.items():
            for q in queries[: args.queries_per_category]:
                token = None
                for _ in range(args.pages):
                    params = dict(part="snippet", type="channel", q=q, regionCode="LK", maxResults=50)
                    if token:
                        params["pageToken"] = token
                    data = api.get("search", **params)
                    for it in data.get("items", []):
                        cid = it["id"]["channelId"]
                        entry = found.setdefault(cid, {"queries": set(), "cats": Counter()})
                        entry["queries"].add(q)
                        entry["cats"][cat] += 1
                    token = data.get("nextPageToken")
                    if not token:
                        break
                print(f"[{cat}] '{q}' -> {len(found)} unique channels so far (quota {api.used})")
    except QuotaExceeded as e:
        print(f"Stopping discovery: {e}")

    ids = list(found)
    rows = []
    try:
        for i in range(0, len(ids), 50):
            data = api.get("channels", part="snippet,statistics", id=",".join(ids[i:i + 50]))
            for it in data.get("items", []):
                sn, st = it["snippet"], it.get("statistics", {})
                country = sn.get("country", "")
                subs = to_int(st.get("subscriberCount"))
                vids = to_int(st.get("videoCount")) or 0
                if country not in ("LK", ""):
                    continue
                if subs is not None and subs < args.min_subs:
                    continue
                if vids < args.min_videos:
                    continue
                info = found[it["id"]]
                top, *rest = [c for c, _ in info["cats"].most_common()]
                rows.append({
                    "channel": it["id"], "category": top, "approve": "",
                    "title": sn.get("title", ""), "handle": sn.get("customUrl", ""),
                    "country": country or "(unset)", "subscribers": subs if subs is not None else "hidden",
                    "video_count": vids, "created_at": sn.get("publishedAt", "")[:10],
                    "matched_queries": " | ".join(sorted(info["queries"])),
                    "other_categories": " ".join(rest),
                    "url": f"https://www.youtube.com/channel/{it['id']}",
                })
    except QuotaExceeded as e:
        print(f"Stopping enrichment: {e}")

    rows.sort(key=lambda r: (r["category"], -(r["subscribers"] if isinstance(r["subscribers"], int) else 0)))
    DATA_DIR.mkdir(exist_ok=True)
    out = DATA_DIR / "candidates.csv"
    cols = ["channel", "category", "approve", "title", "handle", "country", "subscribers",
            "video_count", "created_at", "matched_queries", "other_categories", "url"]
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"\nWrote {len(rows)} candidates to {out}  (quota used: {api.used})")
    print("Open it, fix the `category`, put y in `approve` for real Sri Lankan creators, then run collect.")


# --------------------------------------------------------------------------- collect
def list_upload_ids(api, playlist_id, max_videos):
    ids, token = [], None
    while len(ids) < max_videos:
        params = dict(part="contentDetails", playlistId=playlist_id, maxResults=50)
        if token:
            params["pageToken"] = token
        data = api.get("playlistItems", **params)
        ids += [i["contentDetails"]["videoId"] for i in data.get("items", [])]
        token = data.get("nextPageToken")
        if not token:
            break
    return ids[:max_videos]


def video_row(item, channel_id, fetched_at):
    sn, cd, st = item["snippet"], item["contentDetails"], item.get("statistics", {})
    thumbs = sn.get("thumbnails", {})
    if thumbs.get("maxres"):
        main, quality, fallback = thumbs["maxres"], "maxres", thumbs.get("medium")
    else:
        main, quality, fallback = thumbs.get("medium"), "medium", thumbs.get("high")
    title = sn.get("title", "")
    return {
        "video_id": item["id"], "channel_id": channel_id, "title": title,
        "description": (sn.get("description") or "")[:2000],
        "published_at": sn.get("publishedAt"), "duration_s": parse_duration(cd.get("duration")),
        "yt_category_id": sn.get("categoryId"),
        "default_language": sn.get("defaultLanguage"),
        "default_audio_language": sn.get("defaultAudioLanguage"),
        "tags": json.dumps(sn.get("tags", []), ensure_ascii=False),
        "views": to_int(st.get("viewCount")), "likes": to_int(st.get("likeCount")),
        "comments": to_int(st.get("commentCount")), "title_script": title_script(title),
        "thumb_url": main["url"] if main else None,
        "thumb_fallback_url": fallback["url"] if fallback else None,
        "thumb_quality": quality, "fetched_at": fetched_at,
    }


def collect_channel(api, conn, row, args):
    kind, val = parse_ref(row["channel"])
    if kind is None:
        print(f"  ! cannot parse '{row['channel']}' (use @handle, UC id, or /channel/ URL)")
        return False
    data = api.get("channels", part="snippet,statistics,contentDetails", **{kind: val})
    if not data.get("items"):
        print(f"  ! channel not found: {row['channel']}")
        return False
    ch = data["items"][0]
    cid, sn, st = ch["id"], ch["snippet"], ch.get("statistics", {})
    uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]

    fetched_at = now_iso()
    vids = list_upload_ids(api, uploads, args.max_videos)
    saved = 0
    for i in range(0, len(vids), 50):
        data = api.get("videos", part="snippet,contentDetails,statistics", id=",".join(vids[i:i + 50]))
        for it in data.get("items", []):
            if it["snippet"].get("liveBroadcastContent", "none") != "none":
                continue  # skip live / upcoming
            upsert(conn, "videos", "video_id", video_row(it, cid, fetched_at))
            saved += 1

    upsert(conn, "channels", "channel_id", {
        "channel_id": cid, "handle": sn.get("customUrl"), "title": sn.get("title"),
        "category": row["category"], "country": sn.get("country"),
        "default_language": sn.get("defaultLanguage"), "created_at": sn.get("publishedAt"),
        "subscribers": to_int(st.get("subscriberCount")),
        "hidden_subscribers": int(bool(st.get("hiddenSubscriberCount"))),
        "total_views": to_int(st.get("viewCount")), "video_count": to_int(st.get("videoCount")),
        "uploads_playlist": uploads, "videos_collected": saved, "fetched_at": fetched_at,
    })
    conn.commit()
    subs = st.get("subscriberCount", "hidden")
    print(f"  ok {sn.get('title')} | {row['category']} | subs={subs} | videos saved={saved}")
    return True


def cmd_collect(args):
    api = make_api(args)
    conn = db()
    rows = read_channels_csv(args.channels)
    if not rows:
        sys.exit(f"No usable rows in {args.channels} (needs `channel` and `category` columns).")
    bad = [r for r in rows if r["category"] not in CATEGORIES]
    if bad:
        print(f"Warning: {len(bad)} rows have a category outside {sorted(CATEGORIES)}; they are kept as written.")

    fresh_cutoff = (datetime.now(timezone.utc) - timedelta(days=args.skip_fresh_days)).isoformat()
    ok = skipped = failed = 0
    for n, row in enumerate(rows, 1):
        print(f"[{n}/{len(rows)}] {row['channel']}  (quota {api.used}/{api.budget})")
        kind, val = parse_ref(row["channel"])
        if kind == "id" and not args.refresh:
            hit = conn.execute("SELECT fetched_at FROM channels WHERE channel_id=?", (val,)).fetchone()
            if hit and hit[0] > fresh_cutoff:
                print("  = already collected recently, skipping")
                skipped += 1
                continue
        try:
            if collect_channel(api, conn, row, args):
                ok += 1
            else:
                failed += 1
        except QuotaExceeded as e:
            conn.commit()
            print(f"\nStopped: {e}. Re-run the same command later (tomorrow, or with a higher "
                  f"--quota-budget); finished channels are skipped automatically.")
            break
        except RuntimeError as e:
            print(f"  ! {e}")
            failed += 1
    conn.commit()
    print(f"\nDone. collected={ok} skipped={skipped} failed={failed} quota_used={api.used}")


# --------------------------------------------------------------------------- thumbs
def download_thumb(job):
    vid, url, fallback = job
    for u in (url, fallback):
        if not u:
            continue
        try:
            r = requests.get(u, timeout=20)
            if r.status_code != 200:
                continue
            img = Image.open(io.BytesIO(r.content)).convert("RGB")
            img = img.resize((640, 360), Image.Resampling.LANCZOS)
            path = THUMB_DIR / f"{vid}.jpg"
            img.save(path, "JPEG", quality=90)
            return vid, str(path)
        except Exception:
            continue
    return vid, None


def cmd_thumbs(args):
    THUMB_DIR.mkdir(parents=True, exist_ok=True)
    conn = db()
    q = "SELECT video_id, thumb_url, thumb_fallback_url, thumb_path FROM videos WHERE thumb_url IS NOT NULL"
    jobs = []
    for vid, url, fb, path in conn.execute(q):
        if path and Path(path).exists():
            continue
        jobs.append((vid, url, fb))
    if args.limit:
        jobs = jobs[: args.limit]
    print(f"{len(jobs)} thumbnails to download")
    done = failed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for vid, path in pool.map(download_thumb, jobs):
            if path:
                conn.execute("UPDATE videos SET thumb_path=? WHERE video_id=?", (path, vid))
                done += 1
            else:
                failed += 1
            if (done + failed) % 200 == 0:
                conn.commit()
                print(f"  {done + failed}/{len(jobs)}")
    conn.commit()
    print(f"Done. downloaded={done} failed={failed}")


# --------------------------------------------------------------------------- export / stats
def cmd_export(args):
    conn = db()
    out = DATA_DIR / "export"
    out.mkdir(parents=True, exist_ok=True)
    for table in ("channels", "videos"):
        cur = conn.execute(f"SELECT * FROM {table}")
        cols = [d[0] for d in cur.description]
        with open(out / f"{table}.csv", "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(cols)
            w.writerows(cur)
        print(f"wrote {out / (table + '.csv')}")


def cmd_stats(args):
    conn = db()
    print("Channels / videos per category")
    q = """SELECT c.category, COUNT(DISTINCT c.channel_id), COUNT(v.video_id)
           FROM channels c LEFT JOIN videos v ON v.channel_id=c.channel_id GROUP BY c.category"""
    for cat, nch, nv in conn.execute(q):
        print(f"  {cat or '(none)':<10} channels={nch:<4} videos={nv}")
    print("\nSubscriber size buckets (channels)")
    q = """SELECT CASE WHEN subscribers IS NULL THEN 'hidden' WHEN subscribers<1000 THEN '<1k'
                WHEN subscribers<10000 THEN '1k-10k' WHEN subscribers<100000 THEN '10k-100k'
                ELSE '100k+' END b, COUNT(*) FROM channels GROUP BY b"""
    for b, n in conn.execute(q):
        print(f"  {b:<10} {n}")
    print("\nTitle script (videos)")
    for s, n in conn.execute("SELECT title_script, COUNT(*) FROM videos GROUP BY title_script ORDER BY 2 DESC"):
        print(f"  {s:<8} {n}")
    n_thumb = conn.execute("SELECT COUNT(*) FROM videos WHERE thumb_path IS NOT NULL").fetchone()[0]
    n_all = conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0]
    print(f"\nThumbnails downloaded: {n_thumb}/{n_all}")


# --------------------------------------------------------------------------- main
def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--quota-budget", type=int, default=9000,
                   help="stop before spending more than this many units in one run (default 9000 of the 10,000 daily)")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("discover", help="search for candidate channels")
    d.add_argument("--queries-per-category", type=int, default=99)
    d.add_argument("--pages", type=int, default=1, help="search pages per query (100 units each)")
    d.add_argument("--min-subs", type=int, default=500)
    d.add_argument("--min-videos", type=int, default=20)
    d.set_defaults(fn=cmd_discover)

    c = sub.add_parser("collect", help="collect channel and video metadata")
    c.add_argument("--channels", default="channels.csv")
    c.add_argument("--max-videos", type=int, default=200, help="most recent uploads per channel")
    c.add_argument("--skip-fresh-days", type=int, default=3)
    c.add_argument("--refresh", action="store_true", help="re-collect even if recently collected")
    c.set_defaults(fn=cmd_collect)

    t = sub.add_parser("thumbs", help="download thumbnails")
    t.add_argument("--workers", type=int, default=8)
    t.add_argument("--limit", type=int, default=0)
    t.set_defaults(fn=cmd_thumbs)

    sub.add_parser("export", help="export tables to CSV").set_defaults(fn=cmd_export)
    sub.add_parser("stats", help="coverage summary").set_defaults(fn=cmd_stats)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
