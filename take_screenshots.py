#!/usr/bin/env python3
"""Take specimen screenshots for all FontShare fonts using Playwright."""

import json
import sys
import time
from pathlib import Path

REPO_DIR = Path(__file__).parent
FONTS_DIR = REPO_DIR / "fonts"
SPECIMENS_DIR = FONTS_DIR / "specimens"
FONT_LIST = FONTS_DIR / "font-list.json"

with open(FONT_LIST) as f:
    fonts = json.load(f)

results = {"total": len(fonts), "success": 0, "skipped": 0, "failed": 0, "failures": []}

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
except ImportError:
    print("Playwright not available, skipping screenshots")
    sys.exit(0)

def take_screenshot(page, slug, url):
    """Navigate to font page and take screenshot."""
    try:
        page.goto(url, wait_until="networkidle", timeout=20000)
        # Wait a bit for fonts to load
        page.wait_for_timeout(2000)
        out_path = SPECIMENS_DIR / f"{slug}.png"
        page.screenshot(path=str(out_path), full_page=False)
        return True
    except Exception as e:
        print(f"    ERROR: {e}", flush=True)
        return False


def main():
    print(f"Taking screenshots for {len(fonts)} fonts...", flush=True)
    print("=" * 60, flush=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        for i, font in enumerate(fonts):
            slug = font["slug"]
            url = font["url"]

            # Check if screenshot already exists (using both naming patterns)
            out_path = SPECIMENS_DIR / f"{slug}.png"
            old_path = SPECIMENS_DIR / f"{slug}-specimen.png"

            if out_path.exists():
                results["skipped"] += 1
                print(f"[{i+1:3d}/100] SKIP {font['name']} (exists)", flush=True)
                continue

            # Copy old satoshi-specimen.png -> satoshi.png if needed
            if old_path.exists() and not out_path.exists():
                import shutil
                shutil.copy(old_path, out_path)
                results["skipped"] += 1
                print(f"[{i+1:3d}/100] COPY {font['name']} (renamed)", flush=True)
                continue

            print(f"[{i+1:3d}/100] {font['name']}...", end=" ", flush=True)
            ok = take_screenshot(page, slug, url)

            if ok:
                size = out_path.stat().st_size if out_path.exists() else 0
                results["success"] += 1
                print(f"OK ({size//1024}KB)", flush=True)
            else:
                results["failed"] += 1
                results["failures"].append(slug)
                print("FAIL", flush=True)

            # Small delay between screenshots
            time.sleep(0.5)

        browser.close()

    # Update scrape report
    report_file = FONTS_DIR / "scrape-report.json"
    if report_file.exists():
        with open(report_file) as f:
            report = json.load(f)
    else:
        report = {}

    report["screenshots"] = results

    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 60, flush=True)
    print(f"Done: {results['success']} ok, {results['skipped']} skipped, {results['failed']} failed", flush=True)
    if results["failures"]:
        print(f"Failed: {', '.join(results['failures'])}", flush=True)


if __name__ == "__main__":
    main()
