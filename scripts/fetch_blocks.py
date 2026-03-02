#!/usr/bin/env python3
"""Fetch Aceternity block pages via web_fetch equivalent (requests) and extract variant info."""

import json
import os
import re
import subprocess
import time

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

def fetch_page_html(url):
    """Fetch raw HTML from a URL."""
    import urllib.request
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode('utf-8', errors='replace')

def parse_block_page(html, slug, base_url):
    """Parse a block page HTML to extract variant info and any code blocks."""
    
    # Extract title from <h1> or <title>
    h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
    heading = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip() if h1_match else slug
    
    title_match = re.search(r'<title>(.*?)</title>', html)
    page_title = title_match.group(1).strip() if title_match else ''
    
    # Extract variant links: /blocks/{slug}/{variant-slug}
    variant_pattern = rf'/blocks/{re.escape(slug)}/([a-z0-9-]+)'
    variant_slugs = list(dict.fromkeys(re.findall(variant_pattern, html)))  # unique, preserve order
    
    variants = []
    for vs in variant_slugs:
        # Try to find a display name near the link
        name = vs.replace('-', ' ').title()
        # Search for text near the link in the HTML
        context_pattern = rf'/blocks/{re.escape(slug)}/{re.escape(vs)}[^>]*>([^<]+)'
        name_match = re.search(context_pattern, html)
        if name_match:
            found_name = name_match.group(1).strip()
            if found_name and len(found_name) > 2 and len(found_name) < 100:
                name = found_name
        variants.append({
            'title': name,
            'slug': vs,
            'link': f'/blocks/{slug}/{vs}',
            'full_url': f'https://ui.aceternity.com/blocks/{slug}/{vs}'
        })
    
    # Extract description from meta or first paragraph after h1
    desc_match = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]*)"', html)
    description = desc_match.group(1).strip() if desc_match else ''
    if not description:
        p_match = re.search(r'</h1>.*?<p[^>]*>(.*?)</p>', html, re.DOTALL)
        if p_match:
            description = re.sub(r'<[^>]+>', '', p_match.group(1)).strip()[:200]
    
    # Extract code blocks
    code_blocks = []
    for match in re.finditer(r'<pre[^>]*><code[^>]*>(.*?)</code></pre>', html, re.DOTALL):
        code = match.group(1)
        # Unescape HTML entities
        code = code.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"').replace('&#39;', "'")
        code = re.sub(r'<[^>]+>', '', code)  # strip any inner HTML tags
        if len(code.strip()) > 30:
            code_blocks.append(code.strip())
    
    # Also check for install commands
    install_cmds = re.findall(r'(npx\s+shadcn@latest\s+add\s+@aceternity/[^\s<"]+)', html)
    install_cmds = list(dict.fromkeys(install_cmds))
    
    # Check for live-preview links
    preview_links = re.findall(r'/live-preview/([a-z0-9-]+)', html)
    preview_links = list(dict.fromkeys(preview_links))
    
    return {
        'heading': heading,
        'page_title': page_title,
        'description': description,
        'variants': variants,
        'code_blocks': code_blocks,
        'install_cmds': install_cmds,
        'preview_links': preview_links,
    }


def save_block(slug, url, info):
    """Save source code file and update details JSON."""
    heading = info['heading']
    description = info['description']
    variants = info['variants']
    code_blocks = info['code_blocks']
    install_cmds = info['install_cmds']
    preview_links = info['preview_links']
    
    has_real_code = len(code_blocks) > 0 and any(
        ('import' in cb or 'export' in cb or 'function' in cb or 'className' in cb)
        for cb in code_blocks
    )
    
    source_path = os.path.join(SOURCE_DIR, f"{slug}.tsx")
    
    if has_real_code:
        parts = []
        for i, block in enumerate(code_blocks):
            if len(block.strip()) > 30 and not (block.strip().startswith('npx ') and len(block.strip()) < 200):
                parts.append(f"// ==============================")
                parts.append(f"// CODE BLOCK {i+1}")
                parts.append(f"// ==============================\n")
                parts.append(block.strip())
                parts.append("")
        if parts:
            content = "\n".join(parts)
            with open(source_path, 'w') as f:
                f.write(content)
            print(f"  SOURCE: {len(content)} bytes, {len(code_blocks)} blocks")
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
        
        if variants:
            lines.append(f"// Available Variants ({len(variants)}):")
            for v in variants:
                lines.append(f"//   - {v['title']} -> {v['full_url']}")
            lines.append(f"//")
        
        if install_cmds:
            lines.append(f"// Install commands (requires all-access pass):")
            for cmd in install_cmds[:10]:
                lines.append(f"//   {cmd}")
            lines.append(f"//")
        
        if preview_links:
            lines.append(f"// Live previews available:")
            for pl in preview_links:
                lines.append(f"//   https://ui.aceternity.com/live-preview/{pl}")
            lines.append(f"//")
        
        lines.append(f"// Note: Source code requires Aceternity UI all-access pass.")
        lines.append(f"// https://ui.aceternity.com/pricing")
        
        content = "\n".join(lines)
        with open(source_path, 'w') as f:
            f.write(content)
        print(f"  SUMMARY: {len(content)} bytes, {len(variants)} variants")
    
    # Update details JSON
    details_path = os.path.join(DETAILS_DIR, f"{slug}.json")
    details = {}
    if os.path.exists(details_path):
        with open(details_path) as f:
            details = json.load(f)
    
    details['full_source_available'] = has_real_code
    if variants:
        details['block_variants'] = [v['title'] for v in variants]
        details['block_urls'] = [v['full_url'] for v in variants]
    if install_cmds:
        details['install_command'] = '; '.join(install_cmds[:5])
    if preview_links:
        details['preview_urls'] = [f"https://ui.aceternity.com/live-preview/{pl}" for pl in preview_links]
    
    with open(details_path, 'w') as f:
        json.dump(details, f, indent=2)
    
    return has_real_code


def main():
    results = {}
    
    for slug, url in TARGETS:
        print(f"\n--- {slug} ---")
        try:
            html = fetch_page_html(url)
            print(f"  Fetched {len(html)} bytes")
            info = parse_block_page(html, slug, url)
            print(f"  Parsed: heading='{info['heading']}', variants={len(info['variants'])}, "
                  f"code={len(info['code_blocks'])}, installs={len(info['install_cmds'])}, "
                  f"previews={len(info['preview_links'])}")
            
            has_code = save_block(slug, url, info)
            results[slug] = "CODE" if has_code else "SUMMARY"
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
            results[slug] = "ERROR"
        
        time.sleep(0.5)
    
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
    print("FINAL RESULTS:")
    for s, st in results.items():
        print(f"  [{st}] {s}")
    
    code_ct = sum(1 for v in results.values() if v == "CODE")
    summ_ct = sum(1 for v in results.values() if v == "SUMMARY")
    err_ct = sum(1 for v in results.values() if v == "ERROR")
    done_ct = sum(1 for v in results.values() if v == "ALREADY_DONE")
    print(f"\nCode: {code_ct} | Summary: {summ_ct} | Already: {done_ct} | Errors: {err_ct}")

if __name__ == "__main__":
    main()
