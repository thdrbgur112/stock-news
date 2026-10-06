#!/usr/bin/env python3
"""Print today's stock digest; Terminal.app auto-links plain URLs, so print them as text."""
import json
import sys
from datetime import date
from pathlib import Path

OUT_DIR = Path(__file__).parent / "digests"

COLORS = ["\033[96m", "\033[92m", "\033[93m", "\033[95m", "\033[94m", "\033[91m"]
RESET = "\033[0m"
DIM = "\033[2m"
BOLD = "\033[1m"


def main():
    path = OUT_DIR / f"{date.today().isoformat()}.json"
    if not path.exists():
        print("아직 오늘자 다이제스트가 없습니다.")
        sys.exit(0)
    sections = json.loads(path.read_text())

    total = sum(len(sec["items"]) for sec in sections)
    print(f"\n{BOLD}📈 {date.today().isoformat()} 미국 증시 뉴스  ({total}건){RESET}")

    for i, sec in enumerate(sections):
        color = COLORS[i % len(COLORS)]
        bar = "█" * len(sec["items"])
        print(f"\n{color}{BOLD}■ {sec['feed']}{RESET} {DIM}({len(sec['items'])}){RESET}  {color}{bar}{RESET}")
        for it in sec["items"]:
            print(f"  {color}·{RESET} {it['title']}")
            print(f"    {it['link']}")


if __name__ == "__main__":
    main()
