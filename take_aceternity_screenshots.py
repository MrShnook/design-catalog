#!/usr/bin/env python3
"""Take screenshots of Aceternity UI components."""

import json
import os
import time
import sys
from pathlib import Path

REPO_DIR = Path(__file__).parent
DETAILS_DIR = REPO_DIR / "components" / "details"
PREVIEWS_DIR = REPO_DIR / "components" / "previews"
PREVIEWS_DIR.mkdir(exist_ok=True)

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
except ImportError:
    print("Playwright not available, skipping screenshots")
    sys.exit(0)

# Load all components
components = []
for fname in sorted(os.listdir(DETAILS_DIR)):
    d = json.load(open(DETAILS_DIR / fname))
    components.append(d)

print(f"Taking screenshots for {len(components)} components...")

results = {"success": 0, "skipped": 0, "failed": 0, "failures": []}

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
    )
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        color_scheme="dark",  # Aceternity looks best dark
    )
    page = context.new_page()
    
    for i, comp in enumerate(components):
        slug = comp["slug"]
        url = comp["url"]
        out_path = PREVIEWS_DIR / f"{slug}.png"
        
        if out_path.exists():
            print(f"[{i+1}/{len(components)}] {slug} - skipped (exists)")
            results["skipped"] += 1
            continue
        
        print(f"[{i+1}/{len(components)}] {slug}...", end=" ", flush=True)
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=25000)
            page.wait_for_timeout(3000)  # Let animations settle
            
            # Try to capture the preview area specifically
            # Aceternity pages have a PreviewCode section
            try:
                # Look for the preview container
                preview = page.locator('[data-preview], .preview-container, [class*="preview"]').first
                if preview.is_visible():
                    preview.screenshot(path=str(out_path))
                else:
                    # Fall back to full page screenshot (first viewport)
                    page.screenshot(path=str(out_path), clip={"x": 0, "y": 0, "width": 1280, "height": 800})
            except Exception:
                page.screenshot(path=str(out_path), clip={"x": 0, "y": 0, "width": 1280, "height": 800})
            
            print(f"✓")
            results["success"] += 1
            
        except Exception as e:
            print(f"✗ ({str(e)[:50]})")
            results["failed"] += 1
            results["failures"].append({"slug": slug, "error": str(e)[:100]})
        
        # Rate limiting
        time.sleep(2.5)
    
    browser.close()

# Save results
results["total"] = len(components)
with open(REPO_DIR / "components" / "screenshot-report.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"\nDone: {results['success']} success, {results['skipped']} skipped, {results['failed']} failed")
