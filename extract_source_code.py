#!/usr/bin/env python3
"""
Extract source code for all 123 Aceternity UI components using Firecrawl browser.
Uses IIFE wrappers to avoid variable collision across browser_execute calls.
"""

import json
import os
import sys
import time
import traceback

from firecrawl import FirecrawlApp

BASE_DIR = os.path.expanduser("~/repos/design-catalog")
COMPONENTS_DIR = os.path.join(BASE_DIR, "components")
DETAILS_DIR = os.path.join(COMPONENTS_DIR, "details")
SOURCE_DIR = os.path.join(COMPONENTS_DIR, "source_code")
REPORT_FILE = os.path.join(COMPONENTS_DIR, "code-extraction-report.json")
PROGRESS_FILE = os.path.join(COMPONENTS_DIR, "extraction-progress.json")

os.makedirs(SOURCE_DIR, exist_ok=True)

app = FirecrawlApp()

with open(os.path.join(COMPONENTS_DIR, "component-list.json")) as f:
    components = json.load(f)

print(f"Total components: {len(components)}", flush=True)

progress = {}
if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE) as f:
        progress = json.load(f)

def save_progress():
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def create_session():
    session = app.browser(ttl=300)
    print(f"  New session: {session.id}", flush=True)
    return session.id, time.time()

def clean_code_block(text):
    text = text.strip()
    for suffix in ['\nCopy\nSelect Language', '\nSelect Language', '\nCopy']:
        if text.endswith(suffix):
            text = text[:-len(suffix)].rstrip()
    if text.endswith('Copy'):
        text = text[:-4].rstrip()
    return text

def extract_code_for_component(sid, slug, url):
    """Extract code using IIFE-wrapped browser_execute."""
    
    # Use a unique temp filename
    tmp_file = f'/tmp/ace-{slug}-{int(time.time())}.json'
    
    js_code = f"""
await (async () => {{
    await page.goto('{url}', {{ waitUntil: 'networkidle' }});
    await page.waitForTimeout(2500);

    // Click "Code" button
    const allButtons = await page.$$('button');
    let codeClicked = false;
    for (const btn of allButtons) {{
        const text = await btn.evaluate(el => el.innerText.trim());
        if (text === 'Code') {{ await btn.click(); codeClicked = true; break; }}
    }}
    await page.waitForTimeout(1500);

    // Click "Manual" tab
    const tabs = await page.$$('[role="tab"]');
    let manualClicked = false;
    for (const tab of tabs) {{
        const text = await tab.evaluate(el => el.innerText.trim());
        if (text === 'Manual') {{ await tab.click(); manualClicked = true; break; }}
    }}
    await page.waitForTimeout(1500);

    // Extract all code blocks
    const blocks = await page.evaluate(() => {{
        const codeEls = [...document.querySelectorAll('pre')];
        return codeEls.map((el, i) => ({{
            index: i,
            text: el.innerText.trim(),
            length: el.innerText.trim().length,
            label: ''
        }}));
    }});

    // Get install command from CLI tab
    let installCmd = '';
    for (const tab of tabs) {{
        const text = await tab.evaluate(el => el.innerText.trim());
        if (text === 'CLI') {{ await tab.click(); break; }}
    }}
    await page.waitForTimeout(500);
    const cliBlocks = await page.evaluate(() => {{
        const codeEls = [...document.querySelectorAll('pre')];
        return codeEls.map(el => el.innerText.trim()).filter(t => t.includes('npx shadcn'));
    }});
    if (cliBlocks.length > 0) installCmd = cliBlocks[0];

    const result = JSON.stringify({{
        codeClicked, manualClicked,
        blocks, installCmd,
        blockCount: blocks.length
    }});

    const fs = require('fs');
    fs.writeFileSync('{tmp_file}', result);
}})();
"""
    
    result = app.browser_execute(sid, js_code, language="node", timeout=45)
    
    if not result.success:
        return None, f"Execute failed: {result.stderr}"
    
    # Read result file
    read_result = app.browser_execute(sid, f"cat {tmp_file}", language="bash", timeout=10)
    
    if not read_result.success or not read_result.stdout:
        return None, f"Read failed: {read_result.stderr}"
    
    try:
        data = json.loads(read_result.stdout)
    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {e}"
    
    return data, None

def classify_blocks(blocks):
    """Classify code blocks into usage vs component source."""
    usage = None
    source = None
    deps = None
    
    clean_blocks = []
    for block in blocks:
        text = clean_code_block(block['text'])
        if len(text) < 10:
            continue
        clean_blocks.append({'text': text, 'length': len(text), 'index': block['index']})
    
    for cb in clean_blocks:
        text = cb['text']
        
        # Dependency install
        if text.startswith('npm ') or text.startswith('yarn ') or text.startswith('pnpm '):
            deps = text
            continue
        
        # Utils (cn function) - skip
        if 'cn(' in text and len(text) < 300 and 'twMerge' in text:
            continue
        
        # Usage/demo code
        is_demo = 'Demo' in text and ('@/components/ui/' in text or '@/components/' in text)
        
        if is_demo:
            if usage is None:
                usage = text
            continue
        
        # If it has Demo but is short, treat as usage
        if 'Demo' in text and len(text) < 3000:
            if usage is None:
                usage = text
            continue
        
        # Component source (typically longer, no "Demo" in name)
        if source is None or len(text) > len(source):
            source = text
    
    # If only found usage but no separate source
    if source is None and usage is not None:
        source = usage
        usage = None
    
    # Fallback: longest block
    if source is None and clean_blocks:
        longest = max(clean_blocks, key=lambda b: b['length'])
        source = longest['text']
    
    return {'usage': usage, 'source': source, 'deps': deps}

def process_component(sid, comp, index, total):
    slug = comp['slug']
    url = comp['url']
    comp_type = comp.get('type', 'component')
    
    print(f"[{index+1}/{total}] {slug}", end='', flush=True)
    
    if slug in progress and progress[slug].get('status') == 'success':
        print(f" (skip)", flush=True)
        return True
    
    data, error = extract_code_for_component(sid, slug, url)
    
    if error:
        print(f" ERR: {error[:60]}", flush=True)
        progress[slug] = {'status': 'failed', 'error': error}
        save_progress()
        return False
    
    blocks = data.get('blocks', [])
    install_cmd = clean_code_block(data.get('installCmd', ''))
    
    if not blocks:
        print(f" (no code)", flush=True)
        progress[slug] = {'status': 'no_code', 'error': 'No blocks'}
        save_progress()
        return False
    
    classified = classify_blocks(blocks)
    source_code = classified['source']
    usage_example = classified['usage']
    
    if source_code:
        source_code = clean_code_block(source_code)
    if usage_example:
        usage_example = clean_code_block(usage_example)
    
    # Save full source
    if source_code:
        with open(os.path.join(SOURCE_DIR, f"{slug}.tsx"), 'w') as f:
            f.write(source_code)
    
    # Update detail JSON
    detail_path = os.path.join(DETAILS_DIR, f"{slug}.json")
    if os.path.exists(detail_path):
        with open(detail_path) as f:
            detail = json.load(f)
    else:
        detail = {'slug': slug, 'url': url, 'type': comp_type}
    
    if source_code:
        lines = source_code.split('\n')
        detail['code_snippet'] = '\n'.join(lines[:100]) + ('\n// ...' if len(lines) > 100 else '')
    if usage_example:
        detail['usage_example'] = usage_example
    if install_cmd:
        detail['install_command'] = install_cmd
    detail['full_source_available'] = bool(source_code and len(source_code) > 50)
    
    with open(detail_path, 'w') as f:
        json.dump(detail, f, indent=2)
    
    src_len = len(source_code) if source_code else 0
    print(f" OK ({len(blocks)}blk, {src_len}ch)", flush=True)
    
    progress[slug] = {
        'status': 'success',
        'blocks_found': len(blocks),
        'source_length': src_len,
        'has_usage': bool(usage_example),
        'has_source': bool(source_code)
    }
    save_progress()
    return True

def main():
    total = len(components)
    sid, session_start = create_session()
    
    counts = {'success': 0, 'failed': 0, 'no_code': 0}
    
    for i, comp in enumerate(components):
        # Refresh session every 4 min
        if time.time() - session_start > 240:
            print("  Refreshing session...", flush=True)
            try: app.delete_browser(sid)
            except: pass
            sid, session_start = create_session()
        
        try:
            ok = process_component(sid, comp, i, total)
            if ok:
                counts['success'] += 1
            else:
                st = progress.get(comp['slug'], {}).get('status', 'failed')
                counts['no_code' if st == 'no_code' else 'failed'] += 1
        except Exception as e:
            print(f" EXCEPTION: {e}", flush=True)
            progress[comp['slug']] = {'status': 'failed', 'error': str(e)}
            save_progress()
            counts['failed'] += 1
            try:
                sid, session_start = create_session()
            except:
                time.sleep(5)
                sid, session_start = create_session()
        
        time.sleep(1.5)
    
    try: app.delete_browser(sid)
    except: pass
    
    report = {'total': total, **counts, 'components': progress}
    with open(REPORT_FILE, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n{'='*50}", flush=True)
    print(f"DONE: {counts['success']} ok, {counts['failed']} fail, {counts['no_code']} no-code", flush=True)

if __name__ == '__main__':
    main()
