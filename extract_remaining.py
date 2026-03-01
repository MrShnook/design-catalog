#!/usr/bin/env python3
"""
Extract source code for remaining 23 Aceternity UI components/blocks.
Handles both component pages (with Code/Manual tabs) and block collection pages.
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

os.makedirs(SOURCE_DIR, exist_ok=True)

app = FirecrawlApp()

# Items that need work
NEEDS_WORK = [
    {"slug": "3d-globe", "type": "component", "url": "https://ui.aceternity.com/components/3d-globe"},
    {"slug": "feature-sections-free", "type": "component", "url": "https://ui.aceternity.com/components/feature-sections-free"},
    {"slug": "backgrounds", "type": "block", "url": "https://ui.aceternity.com/blocks/backgrounds"},
    {"slug": "bento-grids", "type": "block", "url": "https://ui.aceternity.com/blocks/bento-grids"},
    {"slug": "blog-content-sections", "type": "block", "url": "https://ui.aceternity.com/blocks/blog-content-sections"},
    {"slug": "blog-sections", "type": "block", "url": "https://ui.aceternity.com/blocks/blog-sections"},
    {"slug": "cards", "type": "block", "url": "https://ui.aceternity.com/blocks/cards"},
    {"slug": "contact-sections", "type": "block", "url": "https://ui.aceternity.com/blocks/contact-sections"},
    {"slug": "cta-sections", "type": "block", "url": "https://ui.aceternity.com/blocks/cta-sections"},
    {"slug": "faqs", "type": "block", "url": "https://ui.aceternity.com/blocks/faqs"},
    {"slug": "feature-sections", "type": "block", "url": "https://ui.aceternity.com/blocks/feature-sections"},
    {"slug": "footers", "type": "block", "url": "https://ui.aceternity.com/blocks/footers"},
    {"slug": "hero-sections", "type": "block", "url": "https://ui.aceternity.com/blocks/hero-sections"},
    {"slug": "illustrations", "type": "block", "url": "https://ui.aceternity.com/blocks/illustrations"},
    {"slug": "login-and-signup-sections", "type": "block", "url": "https://ui.aceternity.com/blocks/login-and-signup-sections"},
    {"slug": "logo-clouds", "type": "block", "url": "https://ui.aceternity.com/blocks/logo-clouds"},
    {"slug": "navbars", "type": "block", "url": "https://ui.aceternity.com/blocks/navbars"},
    {"slug": "pricing-sections", "type": "block", "url": "https://ui.aceternity.com/blocks/pricing-sections"},
    {"slug": "shaders", "type": "block", "url": "https://ui.aceternity.com/blocks/shaders"},
    {"slug": "sidebars", "type": "block", "url": "https://ui.aceternity.com/blocks/sidebars"},
    {"slug": "stats-sections", "type": "block", "url": "https://ui.aceternity.com/blocks/stats-sections"},
    {"slug": "testimonials", "type": "block", "url": "https://ui.aceternity.com/blocks/testimonials"},
    {"slug": "text-animations", "type": "block", "url": "https://ui.aceternity.com/blocks/text-animations"},
]

results = {}

def create_session():
    session = app.browser(ttl=300)
    print(f"  New browser session: {session.id}", flush=True)
    return session.id, time.time()

def clean_code(text):
    text = text.strip()
    for suffix in ['\nCopy\nSelect Language', '\nSelect Language', '\nCopy', 'Copy']:
        if text.endswith(suffix):
            text = text[:-len(suffix)].rstrip()
    return text

def extract_component(sid, slug, url):
    """Extract source code from a component page (has Code/Manual tabs)."""
    tmp_file = f'/tmp/ace-{slug}-{int(time.time())}.json'

    js_code = f"""
await (async () => {{
    await page.goto('{url}', {{ waitUntil: 'networkidle' }});
    await page.waitForTimeout(3000);

    // Try clicking "Code" button
    const allButtons = await page.$$('button');
    let codeClicked = false;
    for (const btn of allButtons) {{
        const text = await btn.evaluate(el => el.innerText.trim());
        if (text === 'Code') {{ await btn.click(); codeClicked = true; break; }}
    }}
    await page.waitForTimeout(2000);

    // Try clicking "Manual" tab
    const tabs = await page.$$('[role="tab"]');
    let manualClicked = false;
    for (const tab of tabs) {{
        const text = await tab.evaluate(el => el.innerText.trim());
        if (text === 'Manual') {{ await tab.click(); manualClicked = true; break; }}
    }}
    await page.waitForTimeout(2000);

    // Extract all code blocks
    const blocks = await page.evaluate(() => {{
        const codeEls = [...document.querySelectorAll('pre code, pre, [data-rehype-pretty-code-fragment] code')];
        return codeEls.map((el, i) => ({{
            index: i,
            text: el.innerText.trim(),
            length: el.innerText.trim().length
        }}));
    }});

    const pageText = await page.evaluate(() => {{
        const main = document.querySelector('main') || document.body;
        return main.innerText.substring(0, 2000);
    }});

    const fs = require('fs');
    fs.writeFileSync('{tmp_file}', JSON.stringify({{
        codeClicked, manualClicked, blocks, pageText,
        blockCount: blocks.length
    }}));
}})();
"""
    result = app.browser_execute(sid, js_code, language="node", timeout=45)
    if not result.success:
        return None, f"Execute failed: {result.stderr}"

    read_result = app.browser_execute(sid, f"cat {tmp_file}", language="bash", timeout=10)
    if not read_result.success or not read_result.stdout:
        return None, f"Read failed"

    try:
        data = json.loads(read_result.stdout)
    except json.JSONDecodeError as e:
        return None, f"JSON parse: {e}"

    return data, None

def extract_block(sid, slug, url):
    """Extract code from a block collection page."""
    tmp_file = f'/tmp/ace-block-{slug}-{int(time.time())}.json'

    js_code = f"""
await (async () => {{
    await page.goto('{url}', {{ waitUntil: 'networkidle' }});
    await page.waitForTimeout(3000);

    // Click ALL "Code" buttons/tabs
    const codeButtons = await page.$$('button');
    let clickedCount = 0;
    for (const btn of codeButtons) {{
        const text = await btn.evaluate(el => el.innerText.trim());
        if (text === 'Code') {{
            try {{
                await btn.click();
                clickedCount++;
                await page.waitForTimeout(500);
            }} catch(e) {{}}
        }}
    }}
    await page.waitForTimeout(2000);

    const tabTriggers = await page.$$('[role="tab"]');
    for (const tab of tabTriggers) {{
        const text = await tab.evaluate(el => el.innerText.trim());
        if (text === 'Code') {{
            try {{
                await tab.click();
                clickedCount++;
                await page.waitForTimeout(500);
            }} catch(e) {{}}
        }}
    }}
    await page.waitForTimeout(2000);

    // Extract code blocks
    const blocks = await page.evaluate(() => {{
        const codeEls = [...document.querySelectorAll('pre code, pre, [data-rehype-pretty-code-fragment] code')];
        return codeEls.map((el, i) => ({{
            index: i,
            text: el.innerText.trim(),
            length: el.innerText.trim().length
        }}));
    }});

    // Get section headings
    const sections = await page.evaluate(() => {{
        const headings = [...document.querySelectorAll('h2, h3')];
        return headings.map(h => ({{ tag: h.tagName, text: h.innerText.trim().substring(0, 150) }}));
    }});

    // Get install commands
    const installCmds = await page.evaluate(() => {{
        const pres = [...document.querySelectorAll('pre')];
        return pres
            .map(p => p.innerText.trim())
            .filter(t => t.startsWith('npm ') || t.startsWith('npx ') || t.startsWith('yarn ') || t.startsWith('pnpm '));
    }});

    // Get all links to individual block pages
    const blockLinks = await page.evaluate(() => {{
        const anchors = [...document.querySelectorAll('a[href]')];
        return anchors
            .map(a => ({{ href: a.href, text: a.innerText.trim().substring(0, 100) }}))
            .filter(a => a.href.includes('/blocks/'));
    }});

    const pageText = await page.evaluate(() => {{
        const main = document.querySelector('main') || document.body;
        return main.innerText.substring(0, 5000);
    }});

    const fs = require('fs');
    fs.writeFileSync('{tmp_file}', JSON.stringify({{
        clickedCount, blocks, sections, installCmds, blockLinks, pageText,
        blockCount: blocks.length
    }}));
}})();
"""
    result = app.browser_execute(sid, js_code, language="node", timeout=60)
    if not result.success:
        return None, f"Execute failed: {result.stderr}"

    read_result = app.browser_execute(sid, f"cat {tmp_file}", language="bash", timeout=10)
    if not read_result.success or not read_result.stdout:
        return None, f"Read failed"

    try:
        data = json.loads(read_result.stdout)
    except json.JSONDecodeError as e:
        return None, f"JSON parse: {e}"

    return data, None


def process_item(sid, item, index, total):
    slug = item['slug']
    url = item['url']
    comp_type = item['type']

    print(f"\n[{index+1}/{total}] {comp_type}: {slug}", flush=True)

    if comp_type == 'component':
        data, error = extract_component(sid, slug, url)
    else:
        data, error = extract_block(sid, slug, url)

    if error:
        print(f"  ERROR: {error}", flush=True)
        results[slug] = {'status': 'failed', 'error': error}
        return False

    blocks = data.get('blocks', [])
    print(f"  Found {len(blocks)} code blocks", flush=True)

    if blocks:
        for i, b in enumerate(blocks[:5]):
            preview = b['text'][:80].replace('\n', ' ')
            print(f"    Block {i}: {b['length']}ch - {preview}...", flush=True)

    # Process extracted code
    all_code = []
    for b in blocks:
        code = clean_code(b['text'])
        if len(code) > 20:
            all_code.append(code)

    source_blocks = [c for c in all_code if not c.startswith('npm ') and not c.startswith('npx ') and not c.startswith('yarn ')]
    install_blocks = [c for c in all_code if c.startswith('npm ') or c.startswith('npx ') or c.startswith('yarn ')]

    # Also check install cmds from page scan
    if comp_type == 'block' and data.get('installCmds'):
        for cmd in data['installCmds']:
            if cmd not in install_blocks:
                install_blocks.append(cmd)

    source_code = None
    usage_code = None

    if comp_type == 'component':
        if source_blocks:
            source_code = max(source_blocks, key=len)
            if len(source_blocks) > 1:
                sorted_b = sorted(source_blocks, key=len, reverse=True)
                usage_code = sorted_b[1]
    else:
        if source_blocks:
            source_code = '\n\n// ============================================\n// NEXT BLOCK EXAMPLE\n// ============================================\n\n'.join(source_blocks)

    # For blocks with no code: build descriptive file
    if not source_code and comp_type == 'block':
        lines = [f"// Aceternity UI Blocks: {slug}", f"// URL: {url}", "//", "// This is a block collection page (premium content).", "//"]

        sections = data.get('sections', [])
        if sections:
            lines.append("// Available block variants:")
            for s in sections:
                if s.get('text'):
                    lines.append(f"//   - {s['text']}")
            lines.append("//")

        if install_blocks:
            lines.append("// Dependencies:")
            for cmd in install_blocks:
                lines.append(f"//   {cmd}")
            lines.append("//")

        block_links = data.get('blockLinks', [])
        if block_links:
            # Filter to just sub-block links
            sub_links = [l for l in block_links if f'/blocks/{slug}/' in l.get('href', '')]
            if sub_links:
                lines.append("// Individual block pages:")
                for link in sub_links:
                    lines.append(f"//   {link['href']}")
                lines.append("//")

        page_text = data.get('pageText', '')
        if page_text:
            lines.append("// Page content:")
            for line in page_text.split('\n')[:50]:
                stripped = line.strip()
                if stripped:
                    lines.append(f"// {stripped}")

        source_code = '\n'.join(lines)

    # Save
    if source_code:
        source_path = os.path.join(SOURCE_DIR, f"{slug}.tsx")
        with open(source_path, 'w') as f:
            f.write(source_code)
        print(f"  Saved: {len(source_code)} chars", flush=True)

    has_real_source = bool(source_blocks and any(len(b) > 100 for b in source_blocks))

    # Update detail JSON
    detail_path = os.path.join(DETAILS_DIR, f"{slug}.json")
    if os.path.exists(detail_path):
        with open(detail_path) as f:
            detail = json.load(f)
    else:
        detail = {'slug': slug, 'url': url, 'type': comp_type}

    if source_blocks:
        snippet = source_blocks[0]
        snippet_lines = snippet.split('\n')
        detail['code_snippet'] = '\n'.join(snippet_lines[:80]) + ('\n// ...' if len(snippet_lines) > 80 else '')
    if usage_code:
        detail['usage_example'] = usage_code[:3000]
    if install_blocks:
        detail['install_command'] = install_blocks[0]
    detail['full_source_available'] = has_real_source

    if comp_type == 'block':
        sections = data.get('sections', [])
        if sections:
            detail['block_variants'] = [s['text'] for s in sections if s.get('text')]
        block_links = data.get('blockLinks', [])
        sub_links = [l['href'] for l in block_links if f'/blocks/{slug}/' in l.get('href', '')]
        if sub_links:
            detail['block_urls'] = sub_links

    with open(detail_path, 'w') as f:
        json.dump(detail, f, indent=2)

    results[slug] = {
        'status': 'success' if has_real_source else 'partial',
        'blocks_found': len(blocks),
        'source_length': len(source_code) if source_code else 0,
        'has_real_source': has_real_source,
        'type': comp_type
    }

    return True


def main():
    total = len(NEEDS_WORK)
    print(f"Processing {total} items", flush=True)

    sid, session_start = create_session()

    for i, item in enumerate(NEEDS_WORK):
        if time.time() - session_start > 240:
            print("\n  Refreshing session...", flush=True)
            try:
                app.delete_browser(sid)
            except:
                pass
            sid, session_start = create_session()

        try:
            process_item(sid, item, i, total)
        except Exception as e:
            print(f"  EXCEPTION: {e}", flush=True)
            traceback.print_exc()
            results[item['slug']] = {'status': 'failed', 'error': str(e)}
            try:
                sid, session_start = create_session()
            except:
                time.sleep(5)
                sid, session_start = create_session()

        time.sleep(2)

    try:
        app.delete_browser(sid)
    except:
        pass

    # Summary
    print(f"\n{'='*60}", flush=True)
    success = sum(1 for r in results.values() if r.get('status') == 'success')
    partial = sum(1 for r in results.values() if r.get('status') == 'partial')
    failed = sum(1 for r in results.values() if r.get('status') == 'failed')
    print(f"DONE: {success} success, {partial} partial, {failed} failed out of {total}", flush=True)

    for slug, r in sorted(results.items()):
        status = r.get('status', '?')
        src_len = r.get('source_length', 0)
        print(f"  {status:8s} {slug:40s} {src_len}ch", flush=True)

    with open(os.path.join(COMPONENTS_DIR, 'remaining-extraction-report.json'), 'w') as f:
        json.dump(results, f, indent=2)


if __name__ == '__main__':
    main()
