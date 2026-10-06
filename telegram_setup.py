#!/usr/bin/env python3
"""텔레그램 봇 최초 1회 설정.
1) 텔레그램 앱에서 @BotFather 에게 /newbot 으로 봇 생성 -> 토큰 받기
2) 만든 봇 검색해서 대화 시작(아무 메시지나, 예: /start)
3) 이 스크립트 실행 -> 토큰 입력하면 chat_id 자동으로 찾아줌
"""
import json
import urllib.request
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "telegram_config.json"


def main():
    bot_token = input("봇 토큰 (BotFather가 준 값): ").strip()
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    with urllib.request.urlopen(url, timeout=10) as resp:
        result = json.loads(resp.read())

    chats = {
        u["message"]["chat"]["id"]: u["message"]["chat"].get("first_name", "")
        for u in result.get("result", [])
        if "message" in u
    }
    if not chats:
        print("대화 내역이 없습니다. 구독할 사람들이 먼저 이 봇에게 아무 메시지나 보낸 뒤 다시 실행하세요.")
        return

    for chat_id, name in chats.items():
        print(f"구독자 추가: {name} (chat_id={chat_id})")

    CONFIG_PATH.write_text(
        json.dumps({"bot_token": bot_token, "chat_ids": list(chats.keys())}, indent=2, ensure_ascii=False)
    )
    print(f"설정 완료: {CONFIG_PATH} ({len(chats)}명)")


if __name__ == "__main__":
    main()
