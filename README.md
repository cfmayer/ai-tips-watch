# AI Tips Watch

Searchable reference of AI coding and Grok Bot tips from 16 builders on X. Live at https://cfmayer.github.io/ai-tips-watch/

- `data/tips.json`: all tips and videos, plus `last_run` and a run log. Each tip: `id`, `date`, `posted_at`, `author`, `topic`, `tags`, `title`, `tip`, `credit`, `source_url`, `source_type`, `video_timestamp`, `related_urls`, `added_at`.
- `scripts/merge.py new.json`: merge a daily run (dedupes by id and by source+title; updates video summaries by id).
- `scripts/build.py`: regenerate `index.html`, `archive/`, `about/`, `404.html`, `sitemap.xml`, `feed.xml`.

Daily run: collect, write `new.json`, then `python3 scripts/merge.py new.json && python3 scripts/build.py && git commit -am "Daily update" && git push`.
