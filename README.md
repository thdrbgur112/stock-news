# stock-news

1시간마다 미국 증시 뉴스 소스(Benzinga RSS, Finnhub, Alpha Vantage 등)를 확인해 **새로 올라온 기사만** 번역해서 텔레그램으로 보내는 봇. 본 링크는 `.seen_links.json`에 기록해 중복 전송을 막습니다.

## 구성
- `digest.py` — 수집 → 신규 기사 감지 → 번역 → 저장/전송
- `telegram_*.py`, `welcome_new_subscribers.py` — [news-digest](https://github.com/thdrbgur112/news-digest)와 동일한 텔레그램 구독 구조
- `wake_check.sh` — launchd에서 호출
- `view.py` — 터미널 뷰어

## 설정 (커밋 금지)
- `telegram_config.json`: `{"bot_token": "...", "chat_ids": []}`
- `stock_config.json`: `{"finnhub_key": "...", "alphavantage_key": "..."}` (없으면 RSS만 사용)
