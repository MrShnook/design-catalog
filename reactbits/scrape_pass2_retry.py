#!/usr/bin/env python3
"""
Pass 2 Retry: Extract source code for remaining components.
Handles session expiry by creating new sessions every 10 components.
"""
import json
import os
import re
import time
import sys

from firecrawl import FirecrawlApp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COMPONENT_LIST = os.path.join(BASE_DIR, "component-list.json")
SOURCE_DIR = os.path.join(BASE_DIR, "source_code")
DETAILS_DIR = os.path.join(BASE_DIR, "details")

os.makedirs(SOURCE_DIR, exist_ok=True)

app = FirecrawlApp()

with open(COMPONENT_LIST) as f:
    all_components = json.load(f)

# Find which are missing
already_done = set()
for f in os.listdir(SOURCE_DIR):
    if f.endswith('.tsx') or f.endswith('.jsx'):
        already_done.add(f.rsplit('.', 1)[0])

components = [c for c in all_components if c['slug'] not in already_done]
print(f"Remaining: {len(components)} components to process")

def create_session():
    try:
        session = app.browser(ttl=600)
        return session.id
    except Exception as e:
        print(f"  Session create error: {e}, retrying...")
        time.sleep(3)
        session = app.browser(ttl=600)
        return session.id

def extract_code(sid, url, slug, retries=3):
    """Extract source code. Returns (code_text, error)."""
    for attempt in range(retries):
        try:
            code = f"""
var fs = require('fs');
page.goto('{url}', {{ waitUntil: 'networkidle' }}).then(function() {{
    return new Promise(function(r) {{ setTimeout(r, 3000); }});
}}).then(function() {{
    return page.evaluate(function() {{
        var btns = [...document.querySelectorAll('button')];
        var codeBtn = btns.find(function(b) {{ return b.textContent.trim() === 'Code'; }});
        if (codeBtn) codeBtn.click();
    }});
}}).then(function() {{
    return new Promise(function(r) {{ setTimeout(r, 3000); }});
}}).then(function() {{
    return page.evaluate(function() {{
        var codes = [...document.querySelectorAll('pre code, pre')];
        return codes.map(function(c) {{ return c.innerText; }}).join('\\n---CODE_BLOCK_SEP---\\n');
    }});
}}).then(function(code) {{
    fs.writeFileSync('/tmp/rb-code-{slug}.txt', code || 'NO_CODE');
    fs.writeFileSync('/tmp/rb-done-{slug}.txt', 'DONE');
}}).catch(function(e) {{
    fs.writeFileSync('/tmp/rb-error-{slug}.txt', e.toString());
    fs.writeFileSync('/tmp/rb-done-{slug}.txt', 'ERROR');
}});
"""
            r = app.browser_execute(sid, code, language="node", timeout=35)
            
            # Wait for completion (up to 15s)
            for wait in range(3):
                time.sleep(5)
                r_done = app.browser_execute(sid, f"cat /tmp/rb-done-{slug}.txt 2>/dev/null || echo 'NOT_DONE'", language="bash", timeout=5)
                status = r_done.stdout.strip()
                if status in ('DONE', 'ERROR'):
                    break
            
            if status == 'ERROR':
                r_err = app.browser_execute(sid, f"cat /tmp/rb-error-{slug}.txt 2>/dev/null", language="bash", timeout=5)
                if attempt < retries - 1:
                    time.sleep(3)
                    continue
                return None, f"JS Error: {r_err.stdout[:200]}"
            
            if status != 'DONE':
                if attempt < retries - 1:
                    time.sleep(5)
                    continue
                return None, "Timeout waiting for DONE"
            
            r_code = app.browser_execute(sid, f"cat /tmp/rb-code-{slug}.txt", language="bash", timeout=10)
            code_text = r_code.stdout
            
            # Clean up
            app.browser_execute(sid, f"rm -f /tmp/rb-code-{slug}.txt /tmp/rb-done-{slug}.txt /tmp/rb-error-{slug}.txt", language="bash", timeout=5)
            
            if not code_text or code_text.strip() in ('NO_CODE', ''):
                if attempt < retries - 1:
                    time.sleep(3)
                    continue
                return None, "No code extracted"
            
            return code_text, None
            
        except Exception as e:
            err_str = str(e)
            if '410' in err_str or 'destroyed' in err_str.lower() or 'expired' in err_str.lower():
                return None, "SESSION_EXPIRED"
            if attempt < retries - 1:
                time.sleep(3)
                continue
            return None, str(e)
    
    return None, "Max retries exceeded"

def extract_best_source(code_text):
    """Pick the best code block (main component implementation)."""
    blocks = code_text.split('---CODE_BLOCK_SEP---')
    
    cleaned_blocks = []
    for block in blocks:
        lines = block.strip().split('\n')
        cleaned_lines = []
        for line in lines:
            cleaned = re.sub(r'^\d+', '', line)
            cleaned_lines.append(cleaned)
        cleaned = '\n'.join(cleaned_lines).strip()
        if cleaned:
            cleaned_blocks.append(cleaned)
    
    if not cleaned_blocks:
        return None
    
    # Score each block - prefer ones with imports and component logic
    best, best_score = None, -1
    for block in cleaned_blocks:
        score = 0
        if 'import' in block: score += 10
        if 'export' in block: score += 5
        if 'useRef' in block or 'useState' in block or 'useEffect' in block: score += 10
        if 'return' in block and ('<' in block): score += 5
        if 'const ' in block or 'function ' in block: score += 3
        score += len(block) / 200  # length bonus
        if score > best_score:
            best_score, best = score, block
    
    return best

total = len(components)
success = 0
failed = []

# Process in batches of 10 with fresh sessions
BATCH_SIZE = 10
sid = create_session()
session_component_count = 0

for i, comp in enumerate(components):
    slug = comp['slug']
    url = comp['url']
    name = comp['name']

    # New session every BATCH_SIZE components
    if session_component_count >= BATCH_SIZE:
        try:
            app.delete_browser(sid)
        except:
            pass
        time.sleep(2)
        sid = create_session()
        session_component_count = 0
        print(f"  [New session created]")

    print(f"[{i+1}/{total}] {name}...", end=" ", flush=True)
    
    code_text, error = extract_code(sid, url, slug)
    session_component_count += 1
    
    if error == "SESSION_EXPIRED":
        print(f"session expired, new session...", end=" ", flush=True)
        try:
            app.delete_browser(sid)
        except:
            pass
        time.sleep(2)
        sid = create_session()
        session_component_count = 0
        code_text, error = extract_code(sid, url, slug)
        session_component_count += 1
    
    if error:
        failed.append({"slug": slug, "name": name, "error": error})
        print(f"FAIL: {error}")
        continue
    
    source = extract_best_source(code_text)
    
    if not source or len(source.strip()) < 50:
        failed.append({"slug": slug, "name": name, "error": "Source too short"})
        print(f"FAIL: source too short ({len(source) if source else 0} chars)")
        continue
    
    # Determine extension
    ext = ".tsx" if re.search(r':\s*(React\.FC|string|number|boolean|Props\b|interface\s+\w+)', source) else ".jsx"
    
    outpath = os.path.join(SOURCE_DIR, f"{slug}{ext}")
    with open(outpath, 'w') as f:
        f.write(source.strip() + '\n')
    
    # Update detail JSON
    detail_path = os.path.join(DETAILS_DIR, f"{slug}.json")
    if os.path.exists(detail_path):
        with open(detail_path) as f:
            detail = json.load(f)
        detail['has_source_code'] = True
        with open(detail_path, 'w') as f:
            json.dump(detail, f, indent=2)
    
    success += 1
    print(f"OK ({len(source)} chars, {ext})")

# Clean up
try:
    app.delete_browser(sid)
except:
    pass

print(f"\n=== PASS 2 RETRY COMPLETE ===")
print(f"Success: {success}/{total} | Failed: {len(failed)}")
if failed:
    print("\nFailed:")
    for f in failed:
        print(f"  {f['slug']}: {f['error']}")

report = {
    "pass": "2-retry", "total": total, "success": success,
    "failed": len(failed), "failed_details": failed
}
with open(os.path.join(BASE_DIR, "pass2-retry-report.json"), 'w') as f:
    json.dump(report, f, indent=2)
print("Report saved.")
