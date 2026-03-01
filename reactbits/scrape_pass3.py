#!/usr/bin/env python3
"""
Pass 3: Extract source code for remaining components using direct Playwright.
For components where Firecrawl browser sandbox failed.
"""
import json
import os
import re
import time
import sys

from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COMPONENT_LIST = os.path.join(BASE_DIR, "component-list.json")
SOURCE_DIR = os.path.join(BASE_DIR, "source_code")
DETAILS_DIR = os.path.join(BASE_DIR, "details")
PREVIEWS_DIR = os.path.join(BASE_DIR, "previews")

os.makedirs(SOURCE_DIR, exist_ok=True)
os.makedirs(PREVIEWS_DIR, exist_ok=True)

# Get failed components from report
RETRY_REPORT = os.path.join(BASE_DIR, "pass2-retry-report.json")
with open(RETRY_REPORT) as f:
    retry_data = json.load(f)
    failed_slugs = {f['slug'] for f in retry_data.get('failed_details', [])}

print(f"Processing {len(failed_slugs)} failed components...")

def extract_component(page, slug, url):
    """Extract source code and screenshot using Playwright."""
    try:
        print(f"  Navigating to {url}...", end=" ", flush=True)
        page.goto(url, wait_until='networkidle', timeout=30000)
        page.wait_for_timeout(3000)
        print("OK")
        
        # Take screenshot of demo first
        print(f"  Taking screenshot...", end=" ", flush=True)
        try:
            demo = page.locator('div[class*="demo"], .preview, [class*="preview"]').first
            if demo.count() > 0:
                demo.screenshot(path=os.path.join(PREVIEWS_DIR, f"{slug}.png"))
            else:
                page.screenshot(path=os.path.join(PREVIEWS_DIR, f"{slug}.png"), full_page=False)
            print("OK")
        except Exception as e:
            print(f"WARN: {e}")
        
        # Click Code tab
        print(f"  Clicking Code tab...", end=" ", flush=True)
        try:
            code_btn = page.locator('button:has-text("Code")').first
            if code_btn.count() > 0:
                code_btn.click()
                page.wait_for_timeout(3000)
                print("OK")
            else:
                print("NOT FOUND")
                return None, "No Code button found"
        except Exception as e:
            print(f"ERROR: {e}")
            return None, f"Click error: {e}"
        
        # Extract code blocks
        print(f"  Extracting code...", end=" ", flush=True)
        code_blocks = page.locator('pre code, pre').all_inner_texts()
        if not code_blocks:
            print("NO CODE")
            return None, "No code blocks found"
        
        code_text = '\n---CODE_BLOCK_SEP---\n'.join(code_blocks)
        print(f"OK ({len(code_text)} chars)")
        return code_text, None
        
    except Exception as e:
        return None, str(e)

def extract_best_source(code_text):
    """Pick the best code block (main component implementation)."""
    blocks = code_text.split('---CODE_BLOCK_SEP---')
    
    cleaned_blocks = []
    for block in blocks:
        lines = block.strip().split('\n')
        cleaned_lines = []
        for line in lines:
            cleaned = re.sub(r'^\s*\d+\s*', '', line)
            cleaned_lines.append(cleaned)
        cleaned = '\n'.join(cleaned_lines).strip()
        if cleaned and len(cleaned) > 20:
            cleaned_blocks.append(cleaned)
    
    if not cleaned_blocks:
        return None
    
    best, best_score = None, -1
    for block in cleaned_blocks:
        score = 0
        if 'import' in block: score += 10
        if 'export' in block: score += 5
        if 'useRef' in block or 'useState' in block or 'useEffect' in block: score += 10
        if 'return' in block and ('<' in block): score += 5
        if 'const ' in block or 'function ' in block: score += 3
        if 'default' in block: score += 3
        score += len(block) / 200
        if score > best_score:
            best_score, best = score, block
    
    return best

with open(os.path.join(BASE_DIR, "component-list.json")) as f:
    all_components = json.load(f)

components = [c for c in all_components if c['slug'] in failed_slugs]

success = []
failed = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1280, 'height': 800})
    page = context.new_page()
    
    for i, comp in enumerate(components):
        slug = comp['slug']
        url = comp['url']
        name = comp['name']
        
        print(f"\n[{i+1}/{len(components)}] {name} ({slug})")
        
        code_text, error = extract_component(page, slug, url)
        
        if error:
            failed.append({"slug": slug, "name": name, "error": error})
            continue
        
        source = extract_best_source(code_text)
        
        if not source or len(source.strip()) < 50:
            failed.append({"slug": slug, "name": name, "error": f"Source too short ({len(source) if source else 0} chars)"})
            continue
        
        ext = ".tsx" if re.search(r':\s*(React\.FC|string|number|boolean|Props\b|interface\s+\w+)', source) else ".jsx"
        
        outpath = os.path.join(SOURCE_DIR, f"{slug}{ext}")
        with open(outpath, 'w') as f:
            f.write(source.strip() + '\n')
        
        detail_path = os.path.join(DETAILS_DIR, f"{slug}.json")
        if os.path.exists(detail_path):
            with open(detail_path) as f:
                detail = json.load(f)
            detail['has_source_code'] = True
            with open(detail_path, 'w') as f:
                json.dump(detail, f, indent=2)
        
        success.append({"slug": slug, "name": name})
        print(f"  SAVED: {slug}{ext} ({len(source)} chars)")
    
    browser.close()

print(f"\n=== PASS 3 COMPLETE ===")
print(f"Success: {len(success)}/{len(components)} | Failed: {len(failed)}")

if failed:
    print("\nFailed:")
    for f in failed:
        print(f"  {f['slug']}: {f['error']}")

report = {
    "pass": "3-playwright",
    "total": len(components),
    "success": len(success),
    "failed": len(failed),
    "success_details": success,
    "failed_details": failed
}
with open(os.path.join(BASE_DIR, "pass3-report.json"), 'w') as f:
    json.dump(report, f, indent=2)
print("Report saved to pass3-report.json")
