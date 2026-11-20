#!/usr/bin/env python3
"""Merge a daily run into data/tips.json.

Usage: python3 scripts/merge.py new.json [--window 2026-11-19/2026-11-20]
new.json: {"tips": [...], "videos": [...]}  (either key optional)
- Tips are deduped by id, then by (source_url, title). Existing tips are never overwritten
  except to fill missing fields.
- Videos are matched by id; an incoming video with a summary updates summary/summary_status
  (use summary_status "done" for watched summaries, "transcript" for transcript-only).
- Sets last_run to now (America/Denver) and logs the run.
"""
import json, sys, datetime, pathlib
from zoneinfo import ZoneInfo
ROOT = pathlib.Path(__file__).resolve().parent.parent
P = ROOT / "data/tips.json"
D = json.loads(P.read_text())
new = json.loads(pathlib.Path(sys.argv[1]).read_text())
window = sys.argv[sys.argv.index("--window") + 1] if "--window" in sys.argv else None
now = datetime.datetime.now(ZoneInfo("America/Denver")).replace(microsecond=0).isoformat()
by_id = {t["id"]: t for t in D["tips"]}
by_src = {(t["source_url"], t["title"]) for t in D["tips"]}
added = 0
for t in new.get("tips", []):
    if t["id"] in by_id:
        for k, v in t.items(): by_id[t["id"]].setdefault(k, v)
        continue
    if (t["source_url"], t["title"]) in by_src: continue
    t.setdefault("added_at", now)
    D["tips"].append(t); by_id[t["id"]] = t; by_src.add((t["source_url"], t["title"])); added += 1
vids = {v["id"]: v for v in D.setdefault("videos", [])}
vadded = vupd = 0
for v in new.get("videos", []):
    if v["id"] in vids:
        cur = vids[v["id"]]
        if v.get("summary"):
            cur["summary"] = v["summary"]; cur["summary_status"] = v.get("summary_status", "done"); vupd += 1
        for k, val in v.items(): cur.setdefault(k, val)
    else:
        v.setdefault("added_at", now); v.setdefault("summary_status", "coming")
        D["videos"].append(v); vids[v["id"]] = v; vadded += 1
D["last_run"] = now
D.setdefault("runs", []).append({"at": now, "window": window, "tips_added": added, "videos_added": vadded, "video_summaries_updated": vupd})
P.write_text(json.dumps(D, indent=1, ensure_ascii=False))
print(f"merged: +{added} tips, +{vadded} videos, {vupd} video summaries updated; total {len(D['tips'])} tips")
