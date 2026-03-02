#!/usr/bin/env python3
"""Extract source code from Aceternity UI block pages using Firecrawl."""

import json
import os
import time
import traceback

from firecrawl import FirecrawlApp

app = FirecrawlApp()

REPO = os.path.expanduser("~/repos/design-catalog")
SOURCE_DIR = os.path.join(REPO, "components", "source_code")
DETAILS_DIR = os.path.join(REPO, "components", "details")

TARGETS = [
    ("shaders", "https://ui.aceternity.com/blocks/shaders"),
    ("feature-sections", "https://ui.aceternity.com/blocks/feature-sections"),
    ("backgrounds", "https://ui.aceternity.com/blocks/backgrounds"),
    ("bento-grids", "https://ui.aceternity.com/blocks/bento-grids"),
    ("blog-sections", "https://ui.aceternity.com/blocks/blog-sections"),
    ("cards", "https://ui.aceternity.com/blocks/cards"),
    ("contact-sections", "https://ui.aceternity.com/blocks/contact-sections"),
    ("cta-sections", "https://ui.aceternity.com/blocks/cta-sections"),
    ("faqs", "https://ui.aceternity.com/blocks/faqs"),
    ("footers", "https://ui.aceternity.com/blocks/footers"),
    ("illustrations", "https://ui.aceternity.com/blocks/illustrations"),
    ("login-and-signup-sections", "https://ui.aceternity.com/blocks/login-and-signup-sections"),
    ("navbars", "https://ui.aceternity.com/blocks/navbars"),
    ("pricing-sections", "https://ui.aceternity.com/blocks/pricing-sections"),
    ("sidebars", "https://ui.aceternity.com/blocks/sidebars"),
    ("stats-sections", "https://ui.aceternity.com/blocks/stats-sections"),
    ("text-animations", "https://ui.aceternity.com/blocks/text-animations"),
]

def create_session():
    print("Creating new browser session...")
    session = app.browser(ttl=300)
    print(f"Session created: {session.id}")
    return session.id

def extract_code(sid, slug, url):
    print(f"\n{'='*60}")
    print(f"Extracting: {slug}")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    js_code = """
await page.goto('""" + url + """', { waitUntil: 'networkidle', timeout: 30000 });
await page.waitForTimeout(4000);

// Try clicking code/source buttons
const codeButtons = await page.$$('button');
for (const btn of codeButtons) {
    const text = await btn.textContent().catch(() => '');
    if (text && (text.toLowerCase().includes('code') || text.toLowerCase().includes('source'))) {
        try { await btn.click(); await page.waitForTimeout(1000); } catch(e) {}
    }
}

const result = await page.evaluate(() => {
    const codeElements = [...document.querySelectorAll('pre code, pre, [data-rehype-pretty-code-fragment] code')];
    const codeBlocks = codeElements
        .map(el => el.innerText || el.textContent)
        .filter(t => t && t.trim().length > 20);
    
    const copyElements = [...document.querySelectorAll('[data-copy], [data-code]')];
    const copyBlocks = copyElements
        .map(el => el.getAttribute('data-copy') || el.getAttribute('data-code') || '')
        .filter(t => t && t.trim().length > 20);
    
    const allLinks = [...document.querySelectorAll('a[href]')];
    const variants = [];
    const seenTitles = new Set();
    allLinks.forEach(a => {
        const href = a.getAttribute('href') || '';
        if (href.includes('/blocks/') && href.split('/').length > 3) {
            const title = a.textContent?.trim()?.substring(0, 80) || '';
            if (title && title.length > 3 && !seenTitles.has(title)) {
                seenTitles.add(title);
                variants.push({ title, link: href });
            }
        }
    });
    
    const heading = document.querySelector('h1')?.textContent?.trim() || '';
    const descEl = document.querySelector('h1 + p') || document.querySelector('.text-neutral-400');
    const desc = descEl?.textContent?.trim() || '';
    
    const installCmds = [...document.querySelectorAll('pre, code')]
        .map(el => el.textContent)
        .filter(t => t && (t.includes('npx') || t.includes('shadcn')));
    
    return {
        codeBlocks: [...new Set([...codeBlocks, ...copyBlocks])],
        variants,
        heading,
        description: desc,
        installCmds: [...new Set(installCmds)],
        totalCodeLength: codeBlocks.reduce((a, b) => a + b.length, 0)
    };
});

const fs = require('fs');
fs.writeFileSync('/tmp/ace-""" + slug + """.json', JSON.stringify(result, null, 2));
"""
    
    try:
        app.browser_execute(sid, js_code, language="node", timeout=45)
    except Exception as e:
        print(f"  Execute error: {e}")
        return None
    
    try:
        read_result = app.browser_execute(sid, f"cat /tmp/ace-{slug}.json", language="bash", timeout=10)
        if hasattr(read_result, 'output'):
            raw = read_result.output
        elif hasattr(read_result, 'result'):
            raw = read_result.result
        elif isinstance(read_result, dict):
            raw = read_result.get('output', read_result.get('result', json.dumps(read_result)))
        else:
            raw = str(read_result)
        
        data = json.loads(raw)
        return data
    except Exception as e:
        print(f"  Read error: {e}")
        traceback.print_exc()
        return None

def save_results(slug, url, data):
    if data is None:
        print(f"  No data for {slug}")
        return False
    
    code_blocks = data.get('codeBlocks', [])
    variants = data.get('variants', [])
    heading = data.get('heading', '')
    description = data.get('description', '')
    install_cmds = data.get('installCmds', [])
    total_code_len = data.get('totalCodeLength', 0)
    
    print(f"  Heading: {heading}")
    print(f"  Description: {(description or 'N/A')[:100]}")
    print(f"  Code blocks: {len(code_blocks)}, total length: {total_code_len}")
    print(f"  Variants: {len(variants)}, Install cmds: {len(install_cmds)}")
    
    has_real_code = total_code_len > 100 and any(
        ('import' in cb or 'export' in cb or 'function' in cb or 'const' in cb or 'className' in cb)
        for cb in code_blocks
    )
    
    source_path = os.path.join(SOURCE_DIR, f"{slug}.tsx")
    
    if has_real_code:
        parts = []
        for i, block in enumerate(code_blocks):
            if block.strip() and len(block.strip()) > 20:
                if block.strip().startswith('npx ') and len(block.strip()) < 200:
                    continue
                parts.append(f"// ==============================")
                parts.append(f"// CODE BLOCK {i+1}")
                parts.append(f"// ==============================\n")
                parts.append(block.strip())
                parts.append("")
        
        if parts:
            content = "\n".join(parts)
            with open(source_path, 'w') as f:
                f.write(content)
            print(f"  => Saved {len(content)} bytes of source code")
        else:
            has_real_code = False
    
    if not has_real_code:
        lines = [
            f"// Aceternity UI Block: {heading or slug}",
            f"// URL: {url}",
            f"// Type: Block Collection Page",
            f"//",
        ]
        if description:
            lines.append(f"// Description: {description}")
            lines.append(f"//")
        
        if variants:
            seen = set()
            clean_variants = []
            for v in variants:
                t = v.get('title', '').strip()
                if t and t not in seen and len(t) < 80 and 'Build websites faster' not in t and 'All-Access' not in t:
                    seen.add(t)
                    clean_variants.append(v)
            
            if clean_variants:
                lines.append(f"// Available Variants ({len(clean_variants)}):")
                for v in clean_variants:
                    link = v.get('link', '')
                    lines.append(f"//   - {v['title']}" + (f" -> {link}" if link else ""))
                lines.append(f"//")
        
        if install_cmds:
            lines.append(f"// Install commands found:")
            for cmd in install_cmds[:5]:
                c = cmd.strip().replace('\\n', ' ')
                if len(c) < 200:
                    lines.append(f"//   {c}")
            lines.append(f"//")
        
        lines.append(f"// Note: This is a collection/showcase page.")
        lines.append(f"// Individual variant source code requires Aceternity UI all-access pass.")
        lines.append(f"// Purchase at: https://ui.aceternity.com/pricing")
        
        if code_blocks:
            real_blocks = [cb for cb in code_blocks if len(cb.strip()) > 50 and not cb.strip().startswith('npx ')]
            if real_blocks:
                lines.append(f"\n// --- Partial code found on page ---\n")
                for i, cb in enumerate(real_blocks[:5]):
                    lines.append(f"// --- Block {i+1} ---")
                    lines.append(cb.strip())
                    lines.append("")
        
        content = "\n".join(lines)
        with open(source_path, 'w') as f:
            f.write(content)
        print(f"  => Saved summary ({len(content)} bytes)")
    
    # Update details JSON
    details_path = os.path.join(DETAILS_DIR, f"{slug}.json")
    if os.path.exists(details_path):
        with open(details_path) as f:
            details = json.load(f)
    else:
        details = {}
    
    details['full_source_available'] = has_real_code
    
    if variants:
        clean_names = []
        seen = set()
        for v in variants:
            t = v.get('title', '').strip()
            if t and t not in seen and len(t) < 80 and 'Build websites faster' not in t and 'All-Access' not in t:
                seen.add(t)
                clean_names.append(t)
        if clean_names:
            details['block_variants'] = clean_names
        
        urls_list = [v.get('link', '') for v in variants if v.get('link', '').startswith('/') or v.get('link', '').startswith('http')]
        if urls_list:
            full_urls = [f"https://ui.aceternity.com{u}" if u.startswith('/') else u for u in urls_list]
            details['block_urls'] = full_urls
    
    with open(details_path, 'w') as f:
        json.dump(details, f, indent=2)
    print(f"  => Updated details JSON (full_source_available: {has_real_code})")
    
    return has_real_code


def main():
    sid = create_session()
    results = {}
    
    print(f"Processing {len(TARGETS)} block pages...\n")
    
    for i, (slug, url) in enumerate(TARGETS):
        try:
            data = extract_code(sid, slug, url)
            has_code = save_results(slug, url, data)
            results[slug] = "source_extracted" if has_code else "summary_saved"
        except Exception as e:
            print(f"  Error: {e}")
            traceback.print_exc()
            results[slug] = f"error: {str(e)[:100]}"
            try:
                sid = create_session()
            except:
                print("  Failed to recreate session")
        
        if i < len(TARGETS) - 1:
            time.sleep(1)
    
    # Ensure feature-sections-free details is correct
    details_path = os.path.join(DETAILS_DIR, "feature-sections-free.json")
    if os.path.exists(details_path):
        with open(details_path) as f:
            details = json.load(f)
        details['full_source_available'] = True
        with open(details_path, 'w') as f:
            json.dump(details, f, indent=2)
    results["feature-sections-free"] = "already_complete"
    
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    for slug, status in results.items():
        icon = "OK" if status in ("source_extracted", "already_complete") else "DOC" if status == "summary_saved" else "ERR"
        print(f"  [{icon}] {slug}: {status}")
    
    extracted = sum(1 for v in results.values() if v == "source_extracted")
    summaries = sum(1 for v in results.values() if v == "summary_saved")
    errors = sum(1 for v in results.values() if v.startswith("error"))
    already = sum(1 for v in results.values() if v == "already_complete")
    print(f"\nTotal: {len(results)} | Extracted: {extracted} | Summaries: {summaries} | Already done: {already} | Errors: {errors}")

if __name__ == "__main__":
    main()
