#!/usr/bin/env python3
"""영어 제목을 한국어로 번역. MyMemory API 우선, 실패 시 구글 비공식 엔드포인트로 대체 (둘 다 키 불필요)."""
import json
import re
import urllib.error
import urllib.parse
import urllib.request

_HANGUL = re.compile(r"[가-힣]")


def is_korean(text):
    return bool(_HANGUL.search(text))


def _mymemory(text):
    params = urllib.parse.urlencode({"q": text, "langpair": "en|ko"})
    url = f"https://api.mymemory.translated.net/get?{params}"
    with urllib.request.urlopen(url, timeout=10) as resp:
        data = json.loads(resp.read())
    result = data.get("responseData", {}).get("translatedText", "")
    if not result or data.get("responseStatus") != 200:
        raise ValueError("empty/failed response")
    return result


def _google(text):
    params = urllib.parse.urlencode({"client": "gtx", "sl": "auto", "tl": "ko", "dt": "t", "q": text})
    url = f"https://translate.googleapis.com/translate_a/single?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    return "".join(chunk[0] for chunk in data[0])


def to_korean(text):
    if is_korean(text):
        return text
    for translator in (_mymemory, _google):
        try:
            return translator(text)
        except Exception:
            continue
    return text
