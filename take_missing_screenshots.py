#!/usr/bin/env python3
"""Take screenshots for missing Aceternity components — resilient batch mode."""
import json
import time
import sys
from pathlib import Path

REPO_DIR = Path(__file__).parent
PREVIEWS_DIR = REPO_DIR / "components" / "previews"
LIST_FILE = REPO_DIR / "components" / "component-list.json"
PREVIEWS_DIR.mkdir(exist_ok=True)

from playwright.sync_api import sync_playwright

# Load component list for URL lookup
with open(LIST_FILE) as f:
    comp_list = json.load(f)
slug_to_item = {c["slug"]: c for c in comp_list}

ALL_SLUGS = [
    "blog-content-sections", "blog-sections", "hero-sections", "hero-sections-free",
    "hover-border-gradient", "illustrations", "images-badge", "images-slider",
    "infinite-moving-cards", "keyboard", "lamp-effect", "layout-grid",
    "layout-text-flip", "lens", "link-preview", "loader",
    "login-and-signup-sections", "logo-clouds", "macbook-scroll", "meteors",
    "moving-border", "multi-step-loader", "navbar-menu", "navbars",
    "noise-background", "parallax-scroll", "pixelated-canvas",
    "placeholders-and-vanish-input", "pointer-highlight", "pricing-sections",
    "resizable-navbar", "scales", "shaders",
    "shooting-stars-and-stars-background", "sidebar", "sidebars",
    "signup-form", "sparkles", "spotlight", "spotlight-new",
    "stateful-button", "stats-sections", "sticky-banner",
    "sticky-scroll-reveal", "svg-mask-effect", "tabs",
    "tailwindcss-buttons", "testimonials", "text-animations",
    "text-generate-effect", "text-hover-effect", "text-reveal-card",
    "timeline", "tooltip-card", "tracing-beam", "typewriter-effect",
    "vortex", "wavy-background", "webcam-pixel-grid", "wobble-card", "world-map"
]

# Filter to only missing
missing = [s for s in ALL_SLUGS if not (PREVIEWS_DIR / f"{s}.png").exists()]
print(f"Need screenshots for {len(missing)} components")

if not missing:
    print("Nothing to do!")
    sys.exit(0)

BATCH_SIZE = 10
results = {"success": 0, "failed": 0, "failures": []}

for batch_start in range(0, len(missing), BATCH_SIZE):
    batch = missing[batch_start:batch_start + BATCH_SIZE]
    batch_num = batch_start // BATCH_SIZE + 1
    total_batches = (len(missing) + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"\n--- Batch {batch_num}/{total_batches} ({len(batch)} items) ---")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage",
                       "--disable-gpu"]
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                color_scheme="dark",
            )
            page = context.new_page()
            
            for j, slug in enumerate(batch):
                idx = batch_start + j + 1
                out_path = PREVIEWS_DIR / f"{slug}.png"
                
                if out_path.exists():
                    print(f"[{idx}/{len(missing)}] {slug} - skipped")
                    continue
                
                item = slug_to_item.get(slug)
                url = item["url"] if item else f"https://ui.aceternity.com/components/{slug}"
                
                print(f"[{idx}/{len(missing)}] {slug}...", end=" ", flush=True)
                
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(3000)
                    
                    # Full viewport screenshot
                    page.screenshot(path=str(out_path), clip={"x": 0, "y": 0, "width": 1280, "height": 800})
                    print("OK")
                    results["success"] += 1
                except Exception as e:
                    print(f"FAIL ({str(e)[:60]})")
                    results["failed"] += 1
                    results["failures"].append(slug)
                
                time.sleep(2.5)
            
            browser.close()
    except Exception as e:
        print(f"Batch {batch_num} crashed: {e}")
        # Mark remaining in batch as failed
        for slug in batch:
            if not (PREVIEWS_DIR / f"{slug}.png").exists():
                results["failed"] += 1
                results["failures"].append(slug)
    
    # Small pause between batches
    time.sleep(1)

print(f"\nDone: {results['success']} OK, {results['failed']} failed")
if results["failures"]:
    print(f"Failures: {results['failures']}")
