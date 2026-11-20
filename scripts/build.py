#!/usr/bin/env python3
"""Rebuild the static site from data/tips.json.

Usage: python3 scripts/build.py
Daily runs: merge new tips with scripts/merge.py, then run this, then commit + push.
"""
import json, html, re, datetime, hashlib, pathlib
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEN = ZoneInfo("America/Denver")
D = json.loads((ROOT / "data/tips.json").read_text())
SITE = D["site"]; BASE = SITE["base_url"]; TITLE = SITE["title"]
TAGLINE = "Searchable reference of AI coding and Grok Bot tips from 16 builders on X"
TOPIC_ORDER = ["Grok Bot", "Cursor", "Agent skills & setup", "Prompting", "Code quality",
               "Testing & verification", "Workflows", "Software factories", "Models & evaluation",
               "Mobile & app building"]
e = lambda s: html.escape(str(s or ""), quote=True)

def slug(s): return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

tips = sorted(D["tips"], key=lambda t: t["posted_at"], reverse=True)
videos = sorted(D.get("videos", []), key=lambda v: v["date"], reverse=True)
topics = sorted({t["topic"] for t in tips}, key=lambda x: (TOPIC_ORDER.index(x) if x in TOPIC_ORDER else 99, x))
authors = sorted({t["author"] for t in tips}, key=str.lower)
last_run = datetime.datetime.fromisoformat(D["last_run"])
last_run_label = last_run.astimezone(DEN).strftime("%b %-d, %Y, %-I:%M %p") + " MT"

# "New today": added in the latest run and posted within 2 days before it
def is_new(t):
    added = datetime.datetime.fromisoformat(t["added_at"])
    posted = datetime.datetime.fromisoformat(t["posted_at"].replace("Z", "+00:00"))
    return abs((added - last_run).total_seconds()) < 6 * 3600 and (last_run - posted).total_seconds() < 48 * 3600
new_tips = [t for t in tips if is_new(t)]

css_v = hashlib.md5((ROOT / "assets/site.css").read_bytes()).hexdigest()[:8]
js_v = hashlib.md5((ROOT / "assets/app.js").read_bytes()).hexdigest()[:8]

def head(title, desc, path, depth):
    pre = "../" * depth
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{BASE}{path}">
<meta name="color-scheme" content="light dark">
<script>(function(){{var d=document.documentElement,t=null;try{{t=localStorage.getItem('theme')}}catch(e){{}}if(t!=='light'&&t!=='dark'){{t=window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'}}d.setAttribute('data-theme',t)}})();</script>
<link rel="icon" href="{pre}favicon.svg" type="image/svg+xml">
<link rel="alternate" type="application/atom+xml" title="{TITLE} (Atom feed)" href="{BASE}feed.xml">
<link rel="stylesheet" href="{pre}assets/site.css?v={css_v}">
<meta property="og:site_name" content="{TITLE}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{BASE}{path}">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <div class="wrap top-in">
    <a class="brand" href="{pre or './'}"><span class="logo" aria-hidden="true">◆</span> {TITLE}</a>
    <nav>
      <a href="{pre or './'}#topics">Topics</a>
      <a href="{pre or './'}#videos">Videos</a>
      <a href="{pre}archive/">Archive</a>
      <a href="{pre}about/">About</a>
      <button class="theme" type="button" aria-label="Toggle dark mode" onclick="(function(d){{var t=d.getAttribute('data-theme')==='dark'?'light':'dark';d.setAttribute('data-theme',t);try{{localStorage.setItem('theme',t)}}catch(e){{}}}})(document.documentElement)">◐</button>
    </nav>
  </div>
</header>
"""

def foot(depth):
    pre = "../" * depth
    return f"""<footer class="foot"><div class="wrap">
<p>{TITLE} is compiled from public posts and videos on X and YouTube. Each tip is paraphrased and links to its exact source. Last updated {e(last_run_label)}. <a href="{BASE}feed.xml">Atom feed</a> · <a href="{pre}data/tips.json">tips.json</a></p>
</div></footer>
</body></html>
"""

def tip_card(t, prefix=""):
    src_label = {"post": "Post on X", "article": "Article", "video": "Video", "video-transcript": "Video (from transcript)"}.get(t.get("source_type"), "Source")
    ts = f' at {e(t["video_timestamp"])}' if t.get("video_timestamp") else ""
    related = "".join(f' · <a href="{e(u)}" rel="noopener">related</a>' for u in t.get("related_urls", []))
    credit = f'<span class="credit">{e(t["credit"])}</span>' if t.get("credit") else ""
    note = f'<p class="note">{e(t["note"])}</p>' if t.get("note") else ""
    tags = " ".join(t.get("tags", []))
    date = datetime.date.fromisoformat(t["date"]).strftime("%b %-d, %Y")
    search = " ".join([t["title"], t["tip"], t["author"], t["topic"], tags, t.get("credit") or ""]).lower()
    return f"""<article class="tip" id="{prefix}{e(t['id'])}" data-topic="{e(t['topic'])}" data-author="{e(t['author'])}" data-search="{e(search)}">
  <div class="meta"><a class="topic-pill" href="#t-{slug(t['topic'])}">{e(t['topic'])}</a> <span>@{e(t['author'])}</span> <time datetime="{e(t['posted_at'])}">{date}</time>{credit}</div>
  <h3>{e(t['title'])}</h3>
  <p>{e(t['tip'])}</p>{note}
  <p class="src"><a href="{e(t['source_url'])}" rel="noopener">{src_label}{ts} ↗</a>{related} · <a class="perma" href="#{e(t['id'])}" aria-label="Link to this tip">#</a></p>
</article>"""

def video_card(v):
    mins = v["duration_s"] // 60; secs = v["duration_s"] % 60
    dur = f"{mins // 60}h {mins % 60}m" if mins >= 60 else f"{mins}:{secs:02d}"
    if v.get("summary_status") == "done" and v.get("summary"):
        body = f'<p class="vsum"><span class="badge ok">Summary</span> {e(v["summary"])}</p>'
    elif v.get("summary_status") == "transcript" and v.get("summary"):
        body = f'<p class="vsum"><span class="badge tr">Summary from transcript</span> {e(v["summary"])}</p>'
    elif v.get("summary_status") == "skipped":
        body = f'<p class="vsum"><span class="badge skip">Not summarized</span> {e(v.get("note"))}</p>'
    else:
        body = '<p class="vsum"><span class="badge wait">Video summary coming</span></p>'
    search = " ".join([v["title"], v["poster"], v.get("summary") or ""]).lower()
    return f"""<article class="video" id="v-{e(v['id'])}" data-author="{e(v['poster'])}" data-search="{e(search)}">
  <div class="meta"><span>@{e(v['poster'])}</span> <span>{dur}</span> <time>{datetime.date.fromisoformat(v['date']).strftime('%b %-d, %Y')}</time></div>
  <h3><a href="{e(v['source_url'])}" rel="noopener">{e(v['title'])} ↗</a></h3>
  {body}
  <p class="src"><a href="{e(v['posted_in'])}" rel="noopener">Shared in this post ↗</a></p>
</article>"""

# ---------- index ----------
topic_counts = {tp: sum(1 for t in tips if t["topic"] == tp) for tp in topics}
chips = "".join(f'<button type="button" class="chip" data-topic="{e(tp)}" aria-pressed="false">{e(tp)} <span>{topic_counts[tp]}</span></button>' for tp in topics)
author_opts = "".join(f'<option value="{e(a)}">@{e(a)}</option>' for a in authors)
toc = "".join(f'<li><a href="#t-{slug(tp)}">{e(tp)}</a> <span>{topic_counts[tp]}</span></li>' for tp in topics)
sections = ""
for tp in topics:
    items = "\n".join(tip_card(t) for t in tips if t["topic"] == tp)
    sections += f'<section class="topic" id="t-{slug(tp)}"><h2>{e(tp)} <span class="count">{topic_counts[tp]}</span></h2>\n{items}\n</section>\n'
new_html = "\n".join(tip_card(t, "new-") for t in new_tips) or '<p class="empty">No new tips in the latest run.</p>'
vids_html = "\n".join(video_card(v) for v in videos)
desc = f"{len(tips)} tips across {len(topics)} topics on Grok Bot, Cursor, agent skills, prompting and AI coding workflows, each linked to its source."
index = head(f"{TITLE}: {TAGLINE}", desc, "", 0) + f"""
<main id="main" class="wrap">
<section class="hero">
  <h1>{TITLE}</h1>
  <p class="lede">{e(TAGLINE)}. Every tip is paraphrased from a post, article or video and links to the exact source. Updated daily.</p>
  <p class="stats"><strong>{len(tips)}</strong> tips · <strong>{len(topics)}</strong> topics · <strong>{len(videos)}</strong> videos · updated {e(last_run_label)}</p>
</section>
<div class="controls" role="search">
  <label class="sr" for="q">Search tips</label>
  <input id="q" type="search" placeholder="Search tips, e.g. lint, voice, meetings, routines" autocomplete="off">
  <label class="sr" for="author">Filter by author</label>
  <select id="author"><option value="">All authors</option>{author_opts}</select>
  <div class="chips" aria-label="Filter by topic">{chips}</div>
  <p id="status" class="status" aria-live="polite"></p>
</div>
<section id="results" class="results" hidden><h2>Results</h2><div id="results-list"></div></section>
<div id="browse">
<section class="new" id="new"><h2>New today <span class="count">{len(new_tips)}</span></h2>
<p class="hint">Tips added in the latest run from posts in the previous two days.</p>
{new_html}
</section>
<nav class="toc" id="topics" aria-label="Topics"><h2>Topics</h2><ul>{toc}<li><a href="#videos">Videos</a> <span>{len(videos)}</span></li></ul></nav>
{sections}
<section class="videos" id="videos"><h2>Videos <span class="count">{len(videos)}</span></h2>
<p class="hint">Videos these accounts posted or linked about AI tooling. Summaries get added after the videos are watched; anything marked "from transcript" was written from auto-captions only.</p>
{vids_html}
</section>
</div>
</main>
<script src="assets/app.js?v={js_v}" defer></script>
""" + foot(0)
(ROOT / "index.html").write_text(index)

# ---------- archive ----------
rows = ""
for t in tips:
    rows += f'<tr data-search="{e((t["title"]+" "+t["tip"]+" "+t["author"]+" "+t["topic"]).lower())}"><td><time>{e(t["date"])}</time></td><td>@{e(t["author"])}</td><td>{e(t["topic"])}</td><td><a href="../#{e(t["id"])}">{e(t["title"])}</a></td><td><a href="{e(t["source_url"])}" rel="noopener">source{(" @ "+e(t["video_timestamp"])) if t.get("video_timestamp") else ""} ↗</a></td></tr>\n'
archive = head(f"Archive · {TITLE}", "Every tip, newest first.", "archive/", 1) + f"""
<main id="main" class="wrap">
<h1>Archive</h1>
<p class="lede">All {len(tips)} tips, newest first by post date. Runs so far: {len(D.get('runs', []))}.</p>
<label class="sr" for="aq">Filter archive</label>
<input id="aq" type="search" placeholder="Filter the archive" autocomplete="off" oninput="var q=this.value.toLowerCase();document.querySelectorAll('tbody tr').forEach(function(r){{r.hidden=q&&r.dataset.search.indexOf(q)<0}})">
<div class="tablewrap"><table class="archive"><thead><tr><th>Date</th><th>Author</th><th>Topic</th><th>Tip</th><th>Source</th></tr></thead><tbody>
{rows}</tbody></table></div>
</main>
""" + foot(1)
(ROOT / "archive").mkdir(exist_ok=True); (ROOT / "archive/index.html").write_text(archive)

# ---------- about ----------
accts = ", ".join(f'<a href="https://x.com/{a}" rel="noopener">@{a}</a>' for a in D["accounts"])
about = head(f"About · {TITLE}", "What AI Tips Watch is and how it's made.", "about/", 1) + f"""
<main id="main" class="wrap prose">
<h1>About</h1>
<p>{TITLE} collects practical tips about Grok Bot and other AI tools (coding agents, Cursor, Claude Code, Codex, agent skills, prompting and workflows) from a fixed list of builders on X: {accts}.</p>
<h2>How it works</h2>
<ul>
<li>A daily run reads these accounts' recent public posts (plus threads, quoted posts and linked videos), keeps only practical AI-tooling content, and merges new tips into <a href="../data/tips.json">data/tips.json</a>, deduplicated by source.</li>
<li>Tips are paraphrased, not quoted verbatim, and every one links to its exact source post, article or video (with a timestamp when it comes from a video). When an account shares someone else's post, the original author is credited.</li>
<li>Nothing is invented: no numbers or claims appear that aren't in the source. Video summaries are added only after a video has been watched; summaries marked "from transcript" were written from auto-captions only.</li>
<li>Off-topic posts are skipped.</li>
</ul>
<p>Last updated {e(last_run_label)}.</p>
</main>
""" + foot(1)
(ROOT / "about").mkdir(exist_ok=True); (ROOT / "about/index.html").write_text(about)

# ---------- 404 ----------
nf = head(f"Not found · {TITLE}", "Page not found.", "404.html", 0).replace('href="favicon.svg"', f'href="{BASE}favicon.svg"').replace('href="assets/', f'href="{BASE}assets/').replace('href="archive/', f'href="{BASE}archive/').replace('href="about/', f'href="{BASE}about/').replace('href="./', f'href="{BASE}') + f"""
<main id="main" class="wrap prose"><h1>Not found</h1><p>That page doesn't exist. Try the <a href="{BASE}">tips index</a> or the <a href="{BASE}archive/">archive</a>.</p></main>
""" + foot(0)
(ROOT / "404.html").write_text(nf)

# ---------- sitemap, feed, robots ----------
(ROOT / "sitemap.xml").write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>{BASE}</loc><lastmod>{last_run.date().isoformat()}</lastmod></url>
  <url><loc>{BASE}archive/</loc><lastmod>{last_run.date().isoformat()}</lastmod></url>
  <url><loc>{BASE}about/</loc></url>
</urlset>
""")
entries = ""
for t in sorted(tips, key=lambda t: (t["added_at"], t["posted_at"]), reverse=True)[:60]:
    entries += f"""  <entry>
    <title>{e(t['topic'])}: {e(t['title'])}</title>
    <link rel="alternate" type="text/html" href="{BASE}#{e(t['id'])}"/>
    <link rel="related" href="{e(t['source_url'])}"/>
    <id>{BASE}#{e(t['id'])}</id>
    <published>{e(t['posted_at'])}</published>
    <updated>{e(t['added_at'])}</updated>
    <author><name>@{e(t['author'])}</name></author>
    <summary>{e(t['tip'])} (Source: {e(t['source_url'])})</summary>
  </entry>
"""
(ROOT / "feed.xml").write_text(f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>{TITLE}</title>
  <subtitle>{e(TAGLINE)}</subtitle>
  <link rel="self" type="application/atom+xml" href="{BASE}feed.xml"/>
  <link rel="alternate" type="text/html" href="{BASE}"/>
  <id>{BASE}</id>
  <updated>{last_run.isoformat()}</updated>
  <author><name>{TITLE}</name></author>
{entries}</feed>
""")
(ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE}sitemap.xml\n")
(ROOT / ".nojekyll").write_text("")
print(f"built: {len(tips)} tips, {len(topics)} topics, {len(videos)} videos, {len(new_tips)} new today")
