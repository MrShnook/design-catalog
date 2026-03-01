#!/usr/bin/env python3
"""Take specimen screenshots for missing FontShare fonts."""

import time
from pathlib import Path
from playwright.sync_api import sync_playwright

SPECIMENS_DIR = Path(__file__).parent / "fonts" / "specimens"

MISSING_FONTS = [
    "aktura", "anton", "array", "bespoke-slab", "bevellier", "boska",
    "boxing", "britney", "comico", "dancing-script", "hoover", "kalam",
    "kihim", "kohinoor-zerone", "kola", "melodrama", "new-title", "nippo",
    "oswald", "paquito", "pencerio", "rosaline", "segment", "stardom",
    "striper", "styro", "telma", "trench-slab", "zina"
]

def main():
    successes = []
    failures = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        for i, slug in enumerate(MISSING_FONTS):
            url = f"https://www.fontshare.com/fonts/{slug}"
            out_path = SPECIMENS_DIR / f"{slug}.png"
            print(f"[{i+1:2d}/{len(MISSING_FONTS)}] {slug}...", end=" ", flush=True)

            for attempt in range(2):  # retry once
                try:
                    page.goto(url, wait_until="networkidle", timeout=20000)
                    page.wait_for_timeout(2000)
                    page.screenshot(path=str(out_path), full_page=False)
                    size = out_path.stat().st_size
                    successes.append(slug)
                    print(f"OK ({size//1024}KB)", flush=True)
                    break
                except Exception as e:
                    if attempt == 0:
                        print(f"retry...", end=" ", flush=True)
                        time.sleep(3)
                    else:
                        failures.append(slug)
                        print(f"FAIL ({e})", flush=True)

            time.sleep(2)  # delay between fonts

        browser.close()

    print(f"\nDone: {len(successes)} ok, {len(failures)} failed")
    if failures:
        print(f"Failed: {', '.join(failures)}")

if __name__ == "__main__":
    main()
