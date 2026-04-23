"""Generate news brief HTML from news.json + template.html.

Usage:
    python generate.py            # read news.json in repo root, write index.html
    python generate.py path.json  # specify custom input

Flow:
1. Load news.json (structured brief content for a single day)
2. Load template.html
3. Render full HTML (substitute placeholders)
4. Write index.html + {date}.html
5. Update dates.json (keep 7 most recent)
6. Delete {date}.html files not in dates.json (>7 days old)
"""

from __future__ import annotations

import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
KEEP_DAYS = 7
WEEKDAYS_ZH = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]


def weekday_zh(date_str: str) -> str:
    d = datetime.strptime(date_str, "%Y-%m-%d")
    return WEEKDAYS_ZH[d.weekday()]


def esc(text: str) -> str:
    """HTML-escape a string for safe insertion into text content."""
    return html.escape(text, quote=False)


def esc_attr(text: str) -> str:
    """HTML-escape a string for safe insertion into attribute values."""
    return html.escape(text, quote=True)


def render_must_read_item(item: dict, idx: int) -> str:
    num = f"{idx + 1:02d}"
    article_id = item.get("article_id") or f"must-{idx + 1}"
    return (
        f'    <a class="must-read-item" href="#{esc_attr(article_id)}">\n'
        f'      <span class="num">{num}</span>\n'
        f'      <span class="must-title">{esc(item["title"])}</span>\n'
        f'      <span class="must-hint">{esc(item["hint"])}</span>\n'
        f'    </a>'
    )


def render_must_read(items: list[dict]) -> str:
    if not items:
        return "    <!-- no must-read items -->"
    return "\n".join(render_must_read_item(it, i) for i, it in enumerate(items))


TAG_LABELS = {
    "work": ("🎯 工作直擊", "tag-work"),
    "industry": ("📊 產業視野", "tag-industry"),
    "strategy": ("🌏 策略背景", "tag-strategy"),
}


def render_article(art: dict) -> str:
    category = art["category"]
    label, tag_class = TAG_LABELS[category]

    id_attr = f' id="{esc_attr(art["id"])}"' if art.get("id") else ""
    orig_html = ""
    if art.get("orig_title"):
        orig_html = f'      <div class="orig-title">{esc(art["orig_title"])}</div>\n'

    summary = esc(art.get("summary", "")).strip()
    impact = esc(art.get("impact", "")).strip()

    impact_html = ""
    if impact:
        impact_html = (
            f'      <div class="impact">'
            f'<span class="impact-label">對你的意義</span>{impact}</div>\n'
        )

    link_url = art.get("link", "")
    link_text = art.get("link_text", "原文連結")
    link_html = (
        f'        <a href="{esc_attr(link_url)}" target="_blank" rel="noopener noreferrer">{esc(link_text)}</a>'
        if link_url
        else ""
    )

    date_val = art.get("date", "")
    source = art.get("source", "")

    return (
        f'    <article{id_attr} data-category="{esc_attr(category)}">\n'
        f'      <span class="tag {tag_class}">{label}</span>\n'
        f'      <div class="title">{esc(art["title"])}</div>\n'
        f"{orig_html}"
        f'      <div class="summary">{summary}</div>\n'
        f"{impact_html}"
        f'      <div class="footer-meta">\n'
        f'        <span>{esc(date_val)}</span>\n'
        f'        <span class="sep">·</span>\n'
        f'        <span>{esc(source)}</span>\n'
        f'        <span class="sep">·</span>\n'
        f"{link_html}\n"
        f'        <button class="copy-btn" title="複製摘要">📋 複製</button>\n'
        f"      </div>\n"
        f"    </article>"
    )


def render_articles(articles: list[dict]) -> str:
    if not articles:
        return "    <!-- no articles -->"
    return "\n".join(render_article(a) for a in articles)


def count_by_category(articles: list[dict]) -> dict[str, int]:
    counts = {"work": 0, "industry": 0, "strategy": 0}
    for a in articles:
        cat = a.get("category")
        if cat in counts:
            counts[cat] += 1
    return counts


def update_dates_json(date: str) -> list[str]:
    path = REPO_ROOT / "dates.json"
    if path.exists():
        dates = json.loads(path.read_text(encoding="utf-8"))
    else:
        dates = []

    if date not in dates:
        dates.append(date)

    # Newest first, keep top N
    dates = sorted(dates, reverse=True)[:KEEP_DAYS]
    path.write_text(json.dumps(dates, ensure_ascii=False) + "\n", encoding="utf-8")
    return dates


def cleanup_old_snapshots(active_dates: list[str]) -> list[str]:
    """Delete YYYY-MM-DD.html files not in active_dates list."""
    removed = []
    for f in REPO_ROOT.glob("[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].html"):
        if f.stem not in active_dates:
            f.unlink()
            removed.append(f.name)
    return removed


def backup_previous_index(target_date: str) -> str | None:
    """Copy current index.html to {OLD_DATE}.html if OLD_DATE != target_date
    and {OLD_DATE}.html does not already exist. Returns old date or None.
    """
    index = REPO_ROOT / "index.html"
    if not index.exists():
        return None

    text = index.read_text(encoding="utf-8")
    # Extract meta[name="brief-date"] content
    import re

    m = re.search(r'name="brief-date"\s+content="([^"]+)"', text)
    if not m:
        return None

    old_date = m.group(1)
    if old_date == target_date:
        return None

    snapshot = REPO_ROOT / f"{old_date}.html"
    if not snapshot.exists():
        snapshot.write_text(text, encoding="utf-8")
    return old_date


def main(news_path: Path) -> None:
    news = json.loads(news_path.read_text(encoding="utf-8"))
    date = news["date"]
    weekday = news.get("weekday") or weekday_zh(date)
    update_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    tw = news.get("tw", [])
    intl = news.get("intl", [])
    must_read = news.get("must_read", [])

    all_articles = tw + intl
    cat_counts = count_by_category(all_articles)

    template = (REPO_ROOT / "template.html").read_text(encoding="utf-8")

    rendered = (
        template
        .replace("{{DATE}}", esc(date))
        .replace("{{WEEKDAY}}", esc(weekday))
        .replace("{{UPDATE_DATE}}", esc(update_date))
        .replace("{{TW_COUNT}}", str(len(tw)))
        .replace("{{INTL_COUNT}}", str(len(intl)))
        .replace("{{TOTAL_COUNT}}", str(len(all_articles)))
        .replace("{{WORK_COUNT}}", str(cat_counts["work"]))
        .replace("{{INDUSTRY_COUNT}}", str(cat_counts["industry"]))
        .replace("{{STRATEGY_COUNT}}", str(cat_counts["strategy"]))
        .replace("{{MUST_READ_COUNT}}", str(len(must_read)))
        .replace("{{MUST_READ_ITEMS}}", render_must_read(must_read))
        .replace("{{TW_ARTICLES}}", render_articles(tw))
        .replace("{{INTL_ARTICLES}}", render_articles(intl))
    )

    # Backup old index.html as {OLD_DATE}.html if needed
    old_date = backup_previous_index(date)

    # Write new index.html and snapshot
    (REPO_ROOT / "index.html").write_text(rendered, encoding="utf-8")
    (REPO_ROOT / f"{date}.html").write_text(rendered, encoding="utf-8")

    # Update dates.json
    active_dates = update_dates_json(date)

    # Clean up stale snapshots
    removed = cleanup_old_snapshots(active_dates)

    print(f"[generate] Date: {date} ({weekday})")
    print(f"[generate] TW: {len(tw)} articles | INTL: {len(intl)} articles")
    print(f"[generate] Categories: work={cat_counts['work']}, industry={cat_counts['industry']}, strategy={cat_counts['strategy']}")
    print(f"[generate] Must-read: {len(must_read)} items")
    if old_date:
        print(f"[generate] Backed up old index.html as {old_date}.html")
    print(f"[generate] Active dates: {active_dates}")
    if removed:
        print(f"[generate] Removed stale snapshots: {removed}")
    print("[generate] Done.")


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO_ROOT / "news.json"
    if not path.exists():
        print(f"[generate] ERROR: {path} not found", file=sys.stderr)
        sys.exit(1)
    main(path)
