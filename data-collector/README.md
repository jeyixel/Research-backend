# Sri Lankan YouTube corpus collector (Modules E and C)

Collects public channel and video data for Sri Lankan **gaming, education and cooking** creators
through the YouTube Data API v3, downloads thumbnails, and builds a training table with
*relative-performance* targets. No creator CSV is needed.

## Setup (about 10 minutes)

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # then paste your key into .env as YT_API_KEY=...
```

## The plan

| Step | Command | Quota | Output |
|---|---|---|---|
| 1. Discover candidates | `python yt_collector.py discover` | ~2,500 units (25 queries x 100) | `data/candidates.csv` |
| 2. Human review | open the CSV and fix `category`; put `y` in `approve` for channels to collect. To approve every row at once, run `python approveall.py` from this folder. Add your own channels to `channels.csv` if needed. | 0 | approved list |
| 3. Collect metadata | `python yt_collector.py collect --channels data/candidates.csv` then `... --channels channels.csv` | ~9 units per channel (200 videos) | `data/yt.db` |
| 4. Thumbnails | `python yt_collector.py thumbs` | 0 (not API) | `data/thumbnails/<video_id>.jpg` (640x360) |
| 5. Check coverage | `python yt_collector.py stats` | 0 | summary in terminal |
| 6. Training table | `python build_training_table.py` | 0 | `data/training_table.csv` |

Default daily quota is 10,000 units and `search.list` costs 100 per call, while channel, playlist and
video reads cost 1. So discovery is the expensive step; collection is cheap. The script stops at
`--quota-budget` (default 9,000) and a re-run skips finished channels, so it is safe to resume.

### Adding your own channels (`channels.csv`)

```csv
channel,category,notes
@somehandle,cooking,
https://www.youtube.com/@another,gaming,small channel
UCxxxxxxxxxxxxxxxxxxxxxx,education,A/L physics
```

`channel` can be an `@handle`, a `/channel/UC...` URL or a raw channel ID. Old `/c/name` URLs cannot be
resolved cheaply, so open the channel and copy its `@handle` instead. `category` must be `gaming`,
`education` or `cooking`. Category is labelled **per channel by a human** because YouTube has no
"cooking" category, and its own category IDs are too noisy for this.

## Target sample

- 40 to 60 channels per category, 150 to 200 recent videos each (roughly 20k to 30k videos in total).
- Spread the sizes: some under 5k subscribers, many in 5k to 100k, a few above that. The tool is
  meant for small and new creators, so don't let big channels dominate.
- Spread the languages (Sinhala, Tamil, English, mixed). `title_script` is stored per video; note that
  romanised Sinhala shows up as `latin`, which your NLP teammate's classifier can refine.
- Prefer channels that upload long-form videos. Shorts (under about 3 minutes) are filtered out of the
  training table by default.

## What the training table contains

| Column group | Use |
|---|---|
| `y_rel_neighbors` | **Module C target.** log views minus the median of ~10 videos either side, so channel size and growth cancel out. |
| `y_log_views`, `y_rel_prev`, `prev_*` | **Module E.** `prev_*` features use only videos published *before* the row (no leakage). |
| `fold` | Channel-level fold (0 to 4). Cross-validate on it so scores reflect unseen channels. |
| `thumb_path`, `title`, `category` | Module C inputs (thumbnail, title, category only). |

## Rules that keep the results honest

1. **Module C must not see channel-level inputs** (subscribers, channel ID, channel history), or it learns
   "which channel is this" instead of "is this thumbnail good".
2. **Videos younger than 30 days are dropped** because their views have not settled (`--min-age-days`).
3. `subscribers` is a snapshot from collection time (YouTube also rounds it), so it is approximate for
   Module E. Prefer the `prev_*` features.
4. The targets are proxies. Report them to the panel as *predicted relative performance*, not as true CTR or retention.
5. Check YouTube's API Services terms before sharing or publishing the dataset. Thumbnails belong to
   their creators, so keep the corpus private and use it for research only.

## Files

- `yt_collector.py`: discover, collect, thumbs, export, stats
- `build_training_table.py`: filters, relative targets, past-only features, channel folds
- `channels.csv`: your manual list (header only for now)
- `data/`: created on first run (database, thumbnails, exports)
