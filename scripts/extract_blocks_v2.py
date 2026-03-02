#!/usr/bin/env python3
"""Extract source code from Aceternity UI block pages using Firecrawl v2."""

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

def extract_page(sid, slug, url):
    print(f"\n--- {slug} ({url}) ---")
    
    js_code = """
await page.goto('""" + url + """', { waitUntil: 'networkidle', timeout: 30000 });
await page.waitForTimeout(3000);

// Try clicking code/source buttons
const btns = await page.$$('button');
for (const btn of btns) {
    const text = await btn.textContent().catch(() => '');
    if (text && (text.toLowerCase().includes('code') || text.toLowerCase().includes('copy'))) {
        try { await btn.click(); await page.waitForTimeout(500); } catch(e) {}
    }
}

const result = await page.evaluate(() => {
    const codeEls = [...document.querySelectorAll('pre code, pre, [data-rehype-pretty-code-fragment] code')];
    const codeBlocks = codeEls
        .map(el => (el.innerText || el.textContent || '').trim())
        .filter(t => t.length > 20);
    
    const allLinks = [...document.querySelectorAll('a[href]')];
    const variants = [];
    const seen = new Set();
    allLinks.forEach(a => {
        const href = a.getAttribute('href') || '';
        if (href.includes('/blocks/') && href.split('/').length > 3) {
            const title = (a.textContent || '').trim().substring(0, 80);
            if (title && title.length > 3 && !seen.has(title)) {
                seen.add(title);
                variants.push({ title, link: href });
            }
        }
    });
    
    const heading = (document.querySelector('h1') || {}).textContent?.trim() || '';
    const descEl = document.querySelector('h1 + p') || document.querySelector('.text-neutral-400');
    const desc = (descEl?.textContent || '').trim().split('self.__wrap')[0].trim();
    
    const installEls = [...document.querySelectorAll('pre, code')]
        .map(el => (el.textContent || '').trim())
        .filter(t => t.includes('npx') || t.includes('shadcn'));
    
    return {
        codeBlocks,
        variants,
        heading,
        description: desc,
        installCmds: [...new Set(installEls)],
        totalCodeLength: codeBlocks.reduce((a, b) => a + b.length, 0)
    };
});

const fs = require('fs');
fs.writeFileSync('/tmp/ace-""" + slug + """.json', JSON.stringify(result, null, 2));
"""
    
    try:
        r = app.browser_execute(sid, js_code, language="node", timeout=45)
        if not r.success:
            print(f"  Node exec failed: {r.stderr}")
            return None
    except Exception as e:
        print(f"  Node exec error: {e}")
        return None
    
    try:
        r2 = app.browser_execute(sid, f"cat /tmp/ace-{slug}.json", language="bash", timeout=10)
        if r2.stdout:
            data = json.loads(r2.stdout)
            return data
        else:
            print(f"  Empty stdout from cat")
            return None
    except Exception as e:
        print(f"  Read error: {e}")
        return None

def save_results(slug, url, data):
    if not data:
        return False
    
    code_blocks = data.get('codeBlocks', [])
    variants = data.get('variants', [])
    heading = data.get('heading', '') or slug
    description = data.get('description', '')
    install_cmds = data.get('installCmds', [])
    total_code_len = data.get('totalCodeLength', 0)
    
    # Filter out junk variants
    clean_variants = []
    seen = set()
    for v in variants:
        t = v.get('title', '').strip()
        if (t and t not in seen and len(t) < 80 
            and 'Build websites faster' not in t 
            and 'All-Access' not in t
            and 'Build faster' not in t):
            seen.add(t)
            clean_variants.append(v)
    
    has_real_code = total_code_len > 100 and any(
        ('import' in cb or 'export' in cb or 'function' in cb or 'className' in cb)
        for cb in code_blocks
    )
    
    print(f"  heading={heading}, desc_len={len(description)}, code_blocks={len(code_blocks)}, "
          f"total_code={total_code_len}, variants={len(clean_variants)}, has_code={has_real_code}")
    
    source_path = os.path.join(SOURCE_DIR, f"{slug}.tsx")
    
    if has_real_code:
        parts = []
        for i, block in enumerate(code_blocks):
            b = block.strip()
            if len(b) > 20 and not (b.startswith('npx ') and len(b) < 200):
                parts.append(f"// ==============================")
                parts.append(f"// CODE BLOCK {i+1}")
                parts.append(f"// ==============================\n")
                parts.append(b)
                parts.append("")
        if parts:
            content = "\n".join(parts)
            with open(source_path, 'w') as f:
                f.write(content)
            print(f"  => SOURCE: {len(content)} bytes")
        else:
            has_real_code = False
    
    if not has_real_code:
        lines = [
            f"// Aceternity UI Block: {heading}",
            f"// URL: {url}",
            f"// Type: Block Collection Page (premium)",
            f"//",
        ]
        if description:
            lines.append(f"// Description: {description}")
            lines.append(f"//")
        
        if clean_variants:
            lines.append(f"// Available Variants ({len(clean_variants)}):")
            for v in clean_variants:
                link = v.get('link', '')
                full_link = f"https://ui.aceternity.com{link}" if link.startswith('/') else link
                lines.append(f"//   - {v['title']} -> {full_link}")
            lines.append(f"//")
        
        if install_cmds:
            lines.append(f"// Install (requires all-access pass):")
            for cmd in install_cmds[:3]:
                c = cmd.strip().replace('\n', ' ')[:180]
                lines.append(f"//   {c}")
            lines.append(f"//")
        
        lines.append(f"// Note: Source code requires Aceternity UI all-access pass.")
        lines.append(f"// https://ui.aceternity.com/pricing")
        
        # Any partial code on page
        real_blocks = [cb for cb in code_blocks if len(cb.strip()) > 50 and not cb.strip().startswith('npx ')]
        if real_blocks:
            lines.append(f"\n// --- Partial code found on page ---\n")
            for i, cb in enumerate(real_blocks[:3]):
                lines.append(f"// --- Block {i+1} ---")
                lines.append(cb.strip())
                lines.append("")
        
        content = "\n".join(lines)
        with open(source_path, 'w') as f:
            f.write(content)
        print(f"  => SUMMARY: {len(content)} bytes")
    
    # Update details JSON
    details_path = os.path.join(DETAILS_DIR, f"{slug}.json")
    details = {}
    if os.path.exists(details_path):
        with open(details_path) as f:
            details = json.load(f)
    
    details['full_source_available'] = has_real_code
    if clean_variants:
        details['block_variants'] = [v['title'] for v in clean_variants]
        urls = [f"https://ui.aceternity.com{v['link']}" if v['link'].startswith('/') else v['link'] 
                for v in clean_variants if v.get('link')]
        if urls:
            details['block_urls'] = urls
    
    with open(details_path, 'w') as f:
        json.dump(details, f, indent=2)
    
    return has_real_code

def main():
    sid = create_session()
    results = {}
    
    for i, (slug, url) in enumerate(TARGETS):
        try:
            data = extract_page(sid, slug, url)
            has_code = save_results(slug, url, data)
            results[slug] = "CODE" if has_code else "SUMMARY"
        except Exception as e:
            print(f"  FAIL: {e}")
            traceback.print_exc()
            results[slug] = "ERROR"
            try:
                sid = create_session()
            except:
                pass
        time.sleep(1)
    
    # feature-sections-free already done
    fp = os.path.join(DETAILS_DIR, "feature-sections-free.json")
    if os.path.exists(fp):
        with open(fp) as f:
            d = json.load(f)
        d['full_source_available'] = True
        with open(fp, 'w') as f:
            json.dump(d, f, indent=2)
    results["feature-sections-free"] = "ALREADY_DONE"
    
    print(f"\n{'='*50}")
    print("RESULTS:")
    for s, st in results.items():
        print(f"  {s}: {st}")
    
    code_ct = sum(1 for v in results.values() if v == "CODE")
    summ_ct = sum(1 for v in results.values() if v == "SUMMARY")
    err_ct = sum(1 for v in results.values() if v == "ERROR")
    done_ct = sum(1 for v in results.values() if v == "ALREADY_DONE")
    print(f"\nCode: {code_ct} | Summary: {summ_ct} | Already: {done_ct} | Errors: {err_ct}")

if __name__ == "__main__":
    main()
