#!/usr/bin/env python3
"""
Pass 2: Extract source code from ReactBits using Firecrawl browser.
Processes all 122 components, saving source code to source_code/ directory.
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
    components = json.load(f)

def create_session():
    """Create a new browser session."""
    session = app.browser(ttl=300)
    return session.id

def extract_code(sid, url, slug, retries=2):
    """Navigate to URL, click Code tab, extract source code blocks."""
    for attempt in range(retries):
        try:
            # Use promise chain pattern (REPL doesn't support top-level await)
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
            r = app.browser_execute(sid, code, language="node", timeout=30)
            
            # Wait for completion
            time.sleep(8)
            
            # Check if done
            r_done = app.browser_execute(sid, f"cat /tmp/rb-done-{slug}.txt 2>/dev/null || echo 'NOT_DONE'", language="bash", timeout=5)
            if r_done.stdout.strip() == 'ERROR':
                r_err = app.browser_execute(sid, f"cat /tmp/rb-error-{slug}.txt 2>/dev/null", language="bash", timeout=5)
                if attempt < retries - 1:
                    time.sleep(2)
                    continue
                return None, f"Error: {r_err.stdout}"
            
            if r_done.stdout.strip() != 'DONE':
                # Wait more
                time.sleep(5)
                r_done = app.browser_execute(sid, f"cat /tmp/rb-done-{slug}.txt 2>/dev/null || echo 'NOT_DONE'", language="bash", timeout=5)
                if r_done.stdout.strip() != 'DONE':
                    if attempt < retries - 1:
                        continue
                    return None, "Timeout"
            
            # Read the code
            r_code = app.browser_execute(sid, f"cat /tmp/rb-code-{slug}.txt", language="bash", timeout=10)
            code_text = r_code.stdout
            
            if not code_text or code_text.strip() == 'NO_CODE':
                if attempt < retries - 1:
                    time.sleep(2)
                    continue
                return None, "No code found"
            
            # Clean up temp files
            app.browser_execute(sid, f"rm -f /tmp/rb-code-{slug}.txt /tmp/rb-done-{slug}.txt /tmp/rb-error-{slug}.txt", language="bash", timeout=5)
            
            return code_text, None
            
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
                continue
            return None, str(e)
    
    return None, "Max retries exceeded"

def extract_component_source(code_text):
    """From all code blocks, find the main component source (usually the longest block with imports)."""
    blocks = code_text.split('---CODE_BLOCK_SEP---')
    
    # Remove line numbers (lines starting with digits followed by content)
    cleaned_blocks = []
    for block in blocks:
        lines = block.strip().split('\n')
        cleaned_lines = []
        for line in lines:
            # Remove leading line numbers like "1import..." or "23  const..."
            cleaned = re.sub(r'^(\d+)', '', line)
            cleaned_lines.append(cleaned)
        cleaned_blocks.append('\n'.join(cleaned_lines))
    
    # Find the main component source - it's the one with imports and component definition
    best_block = None
    best_score = 0
    
    for block in cleaned_blocks:
        score = 0
        if 'import' in block:
            score += 10
        if 'export' in block or 'const ' in block:
            score += 5
        if 'useRef' in block or 'useState' in block or 'useEffect' in block:
            score += 10
        if 'return' in block and ('<' in block or 'jsx' in block.lower()):
            score += 5
        # Longer blocks are more likely to be the source
        score += len(block) / 100
        
        if score > best_score:
            best_score = score
            best_block = block
    
    return best_block

# Track progress
total = len(components)
success = 0
failed = []
skipped = []

# Check already done
already_done = set()
for f in os.listdir(SOURCE_DIR):
    if f.endswith('.tsx') or f.endswith('.jsx'):
        already_done.add(f.rsplit('.', 1)[0])

print(f"Pass 2: Extracting source code for {total} components ({len(already_done)} already done)")

# Create initial session
sid = create_session()
session_count = 0
MAX_PER_SESSION = 25  # Create new session every 25 components

for i, comp in enumerate(components):
    slug = comp['slug']
    url = comp['url']
    name = comp['name']
    
    if slug in already_done:
        print(f"[{i+1}/{total}] SKIP {name}")
        skipped.append(slug)
        success += 1
        continue
    
    # Refresh session periodically
    session_count += 1
    if session_count > MAX_PER_SESSION:
        try:
            app.delete_browser(sid)
        except:
            pass
        sid = create_session()
        session_count = 0
        print(f"  [New browser session]")
    
    print(f"[{i+1}/{total}] {name}...", end=" ", flush=True)
    
    code_text, error = extract_code(sid, url, slug)
    
    if error:
        failed.append({"slug": slug, "error": error})
        print(f"FAIL: {error}")
        continue
    
    # Extract the main component source
    source = extract_component_source(code_text)
    
    if source and len(source.strip()) > 50:
        # Determine extension
        ext = ".tsx" if "tsx" in url or ": " in source else ".jsx"
        # If it has TypeScript syntax, use .tsx
        if re.search(r':\s*(React\.FC|string|number|boolean|Props|Interface)', source):
            ext = ".tsx"
        
        with open(os.path.join(SOURCE_DIR, f"{slug}{ext}"), 'w') as f:
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
        print(f"OK ({len(source)} chars)")
    else:
        failed.append({"slug": slug, "error": "Source too short or empty"})
        print(f"FAIL: source too short")

# Clean up
try:
    app.delete_browser(sid)
except:
    pass

print(f"\n=== PASS 2 COMPLETE ===")
print(f"Success: {success}/{total} | Failed: {len(failed)} | Skipped: {len(skipped)}")
if failed:
    print("\nFailed:")
    for f in failed:
        print(f"  {f['slug']}: {f['error']}")

report = {
    "pass": 2, "total": total, "success": success,
    "failed": len(failed), "skipped": len(skipped),
    "failed_details": failed
}
with open(os.path.join(BASE_DIR, "pass2-report.json"), 'w') as f:
    json.dump(report, f, indent=2)
