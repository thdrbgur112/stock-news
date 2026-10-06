#!/usr/bin/env python3
"""텔레그램 봇으로 다이제스트 요약 전송. 보낼 때마다 봇에게 말 건 사람을 자동으로 구독자로 등록."""
import json
import urllib.parse
import urllib.request
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "telegram_config.json"


def _sync_subscribers(cfg):
    url = f"https://api.telegram.org/bot{cfg['bot_token']}/getUpdates"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            result = json.loads(resp.read())
        new_ids = {u["message"]["chat"]["id"] for u in result.get("result", []) if "message" in u}
    except Exception:
        new_ids = set()
    merged = sorted(set(cfg.get("chat_ids", [])) | new_ids)
    if merged != cfg.get("chat_ids"):
        cfg["chat_ids"] = merged
        CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False))
    return merged


def load_config():
    if not CONFIG_PATH.exists():
        return None
    return json.loads(CONFIG_PATH.read_text())


def _split_long_paragraph(para, limit):
    """뉴스 한 건 자체가 극단적으로 길 때만 어쩔 수 없이 줄 단위로 쪼갬(거의 안 일어남)."""
    lines = para.split("\n")
    chunks, current = [], ""
    for line in lines:
        candidate = f"{current}\n{line}" if current else line
        if len(candidate) > limit:
            if current:
                chunks.append(current)
            current = line
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def _chunk(text, limit=3500):
    """빈 줄로 구분된 문단(뉴스 한 건 = 제목+링크) 단위로만 잘라서, 제목과 링크가 갈라지지 않게 함."""
    paragraphs = text.split("\n\n")
    chunks, current = [], ""
    for para in paragraphs:
        if len(para) > limit:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_split_long_paragraph(para, limit))
            continue
        candidate = f"{current}\n\n{para}" if current else para
        if len(candidate) > limit:
            chunks.append(current)
            current = para
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def _send_one(bot_token, chat_id, text):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=10) as resp:
            result = json.loads(resp.read())
        return result.get("ok", False)
    except Exception as e:
        print(f"텔레그램 전송 실패(chat_id={chat_id}): {e}")
        return False


def send_text_to(bot_token, chat_id, message):
    return all(_send_one(bot_token, chat_id, chunk) for chunk in _chunk(message))


def send_text(message):
    cfg = load_config()
    if not cfg:
        print("텔레그램 설정 없음 — telegram_setup.py를 먼저 실행하세요.")
        return False
    chat_ids = _sync_subscribers(cfg)
    results = [send_text_to(cfg["bot_token"], chat_id, message) for chat_id in chat_ids]
    return all(results)
