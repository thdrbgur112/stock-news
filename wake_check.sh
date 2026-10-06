#!/bin/bash
# 2시간마다(노트북 켜져있는 동안) 새 구독자 체크 + 새 뉴스 감지
cd "$(dirname "$0")" || exit 1

/usr/bin/python3 welcome_new_subscribers.py

# 22:00~06:59엔 뉴스 안 보냄 (밀린 뉴스는 아침 첫 실행 때 한꺼번에 감)
h=$((10#$(date +%H)))
if [ "$h" -ge 22 ] || [ "$h" -lt 7 ]; then exit 0; fi
/usr/bin/python3 digest.py
