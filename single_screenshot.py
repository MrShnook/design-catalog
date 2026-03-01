#!/usr/bin/env python3
"""Take a single screenshot. Args: slug url output_path"""
import sys
from playwright.sync_api import sync_playwright

slug = sys.argv[1]
url = sys.argv[2]
out = sys.argv[3]

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage",
                   "--disable-gpu", "--single-process"]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            color_scheme="dark",
        )
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3500)
        page.screenshot(path=out, clip={"x": 0, "y": 0, "width": 1280, "height": 800})
        browser.close()
    print(f"OK:{slug}")
except Exception as e:
    print(f"FAIL:{slug}:{str(e)[:80]}")
    sys.exit(1)
