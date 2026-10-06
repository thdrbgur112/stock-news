#!/usr/bin/env python3
"""새로 구독한 사람에게는 다음날까지 기다리지 않고 그 자리에서 오늘자 브리핑을 즉시 보냄."""
import json
from datetime import date
from pathlib import Path

import digest
import telegram_send

SEEN_PATH = Path(__file__).parent / ".seen_subscribers.json"


def main():
    cfg = telegram_send.load_config()
    if not cfg:
        return

    chat_ids = telegram_send._sync_subscribers(cfg)
    seen = set(json.loads(SEEN_PATH.read_text())) if SEEN_PATH.exists() else set()
    new_ids = [c for c in chat_ids if c not in seen]

    if new_ids:
        today = date.today().isoformat()
        digest_path = digest.OUT_DIR / f"{today}.json"
        if not digest_path.exists():
            new_sections, _ = digest.fetch_new_items()
            digest.merge_into_today(new_sections)
        sections = json.loads(digest_path.read_text()) if digest_path.exists() else []
        total = sum(len(s["items"]) for s in sections)

        message = digest.build_telegram_message(sections, total)
        for chat_id in new_ids:
            telegram_send.send_text_to(cfg["bot_token"], chat_id, message)

    SEEN_PATH.write_text(json.dumps(sorted(set(chat_ids) | seen)))


if __name__ == "__main__":
    main()
