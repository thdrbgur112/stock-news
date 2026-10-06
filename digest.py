#!/usr/bin/env python3
"""1시간마다 미국 증시 뉴스 소스를 체크해서 새로 올라온 기사만 감지/전송."""
import json
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

import telegram_send
import translate

CONFIG_PATH = Path(__file__).parent / "stock_config.json"
SEEN_PATH = Path(__file__).parent / ".seen_links.json"
MAX_SEEN = 2000
PER_FEED = 10
OUT_DIR = Path(__file__).parent / "digests"


def _api_keys():
    if not CONFIG_PATH.exists():
        return {}
    return json.loads(CONFIG_PATH.read_text())


def _local(tag):
    return tag.split("}")[-1]


def _fetch_rss(url, limit):
    """Parses both RSS 2.0 (<item>) and Atom (<entry>) feeds."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        root = ET.fromstring(resp.read())
    items = []
    for entry in root.iter():
        if _local(entry.tag) not in ("item", "entry"):
            continue
        title, link, fallback_link = "", "", ""
        for child in entry:
            local = _local(child.tag)
            if local == "title":
                title = (child.text or "").strip()
            elif local == "link":
                href = (child.get("href") or child.text or "").strip()
                if child.get("rel", "alternate") == "alternate":
                    link = href
                else:
                    fallback_link = href
        link = link or fallback_link
        if title:
            items.append((title, link))
        if len(items) >= limit:
            break
    return items


def fetch_benzinga(limit):
    return _fetch_rss("https://www.benzinga.com/feed", limit)


def fetch_financialjuice(limit):
    return _fetch_rss("https://www.financialjuice.com/feed.ashx?xy=rss", limit)


def fetch_reuters(limit):
    # ponytail: Reuters는 공식 RSS를 없애서 구글 뉴스로 reuters.com만 검색해 대체(글 자체는 진짜 로이터 발행분)
    return _fetch_rss(
        "https://news.google.com/rss/search?q=site:reuters.com%20business&hl=en-US&gl=US&ceid=US:en", limit
    )


def fetch_finnhub(limit):
    key = _api_keys().get("finnhub_key")
    if not key:
        raise RuntimeError("finnhub_key 없음 — stock_config.json에 추가하세요")
    url = f"https://finnhub.io/api/v1/news?category=general&token={key}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    return [(it["headline"], it["url"]) for it in data[:limit]]


def fetch_yahoo(limit):
    return _fetch_rss("https://finance.yahoo.com/news/rssindex", limit)


FEEDS = {
    "Benzinga": fetch_benzinga,
    "Financial Juice": fetch_financialjuice,
    "Reuters": fetch_reuters,
    "Finnhub": fetch_finnhub,
    "Yahoo Finance": fetch_yahoo,
}


def _load_seen():
    if SEEN_PATH.exists():
        return set(json.loads(SEEN_PATH.read_text()))
    return set()


def _save_seen(seen):
    SEEN_PATH.write_text(json.dumps(list(seen)[-MAX_SEEN:]))


def fetch_new_items():
    """각 소스를 체크해서 이전에 못 본 링크만 골라 반환. (new_sections, total_new)"""
    seen = _load_seen()
    new_sections = []
    total_new = 0
    for name, fetch in FEEDS.items():
        items = None
        for attempt in range(2):
            try:
                items = fetch(PER_FEED)
                break
            except Exception:
                time.sleep(1)
        if items is None:
            continue  # 1시간마다 도니까 이번에 실패한 소스는 다음 시간에 다시 시도
        new_items = [(t, l) for t, l in items if l not in seen]
        seen.update(l for _, l in items)
        if new_items:
            new_sections.append({"feed": name, "items": [{"title": t, "link": l} for t, l in new_items]})
            total_new += len(new_items)
    _save_seen(seen)
    return new_sections, total_new


def merge_into_today(new_sections):
    """오늘자 누적 파일에 새 항목을 이어붙임 (터미널 '주식' 명령이 하루 전체를 보여주도록)."""
    if not new_sections:
        return
    OUT_DIR.mkdir(exist_ok=True)
    today = date.today().isoformat()
    json_path = OUT_DIR / f"{today}.json"
    existing = json.loads(json_path.read_text()) if json_path.exists() else []
    by_feed = {sec["feed"]: sec["items"] for sec in existing}
    for sec in new_sections:
        by_feed.setdefault(sec["feed"], [])
        by_feed[sec["feed"]] = sec["items"] + by_feed[sec["feed"]]  # 최신이 위로
    merged = [{"feed": name, "items": by_feed[name]} for name in FEEDS if name in by_feed]
    json_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [f"# {today} 미국 증시 뉴스"]
    for sec in merged:
        md_lines.append(f"\n## {sec['feed']}")
        for it in sec["items"]:
            md_lines.append(f"- [{it['title']}]({it['link']})")
    (OUT_DIR / f"{today}.md").write_text("\n".join(md_lines), encoding="utf-8")


def build_telegram_message(sections, total):
    today = date.today()
    # ponytail: 뉴스 한 건(제목+링크)을 문단 단위로 유지 — 텔레그램이 길면 문단 경계에서만 쪼개서 중간에 안 끊기게 함
    paragraphs = [f"{today.year}년 {today.month}월 {today.day}일 미국 증시 뉴스\n({total}건)"]
    for sec in sections:
        paragraphs.append(f"[{sec['feed']}]")
        for it in sec["items"]:
            paragraphs.append(f"- {translate.to_korean(it['title'])}\n  {it['link']}")
            time.sleep(0.5)
    return "\n\n".join(paragraphs)


def main():
    new_sections, total_new = fetch_new_items()
    merge_into_today(new_sections)
    if total_new == 0:
        print("새 뉴스 없음")
        return
    print(f"{total_new}건 새 뉴스")
    telegram_send.send_text(build_telegram_message(new_sections, total_new))


if __name__ == "__main__":
    main()
