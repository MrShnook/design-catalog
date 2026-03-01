#!/usr/bin/env python3
"""
Pass 1: Firecrawl standard scrape for metadata + props.
Saves raw markdown and creates detail JSON files.
"""
import json
import os
import re
import time
import sys

from firecrawl import FirecrawlApp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COMPONENT_LIST = os.path.join(BASE_DIR, "component-list.json")
RAW_MD_DIR = os.path.join(BASE_DIR, "raw_markdown")
DETAILS_DIR = os.path.join(BASE_DIR, "details")

os.makedirs(RAW_MD_DIR, exist_ok=True)
os.makedirs(DETAILS_DIR, exist_ok=True)

app = FirecrawlApp()

with open(COMPONENT_LIST) as f:
    components = json.load(f)

def parse_props(md):
    props = []
    lines = md.split('\n')
    in_table = False
    for line in lines:
        if '| Property |' in line or '| Prop |' in line:
            in_table = True
            continue
        if in_table and ('| ---' in line or '|---' in line):
            continue
        if in_table and line.strip().startswith('|'):
            cells = [c.strip() for c in line.split('|')[1:-1]]
            if len(cells) >= 4:
                props.append({
                    "name": cells[0],
                    "type": cells[1],
                    "default": cells[2],
                    "description": cells[3]
                })
            elif len(cells) == 3:
                props.append({
                    "name": cells[0],
                    "type": cells[1],
                    "default": cells[2],
                    "description": ""
                })
        elif in_table and not line.strip().startswith('|'):
            in_table = False
    return props

def parse_dependencies(md):
    deps = []
    lines = md.split('\n')
    in_deps = False
    for i, line in enumerate(lines):
        if '## Dependencies' in line:
            in_deps = True
            continue
        if in_deps:
            if line.startswith('##') or line.startswith('Created'):
                break
            cleaned = line.strip()
            if cleaned and not cleaned.startswith('[') and cleaned not in ['-', '|', '']:
                for dep in re.split(r'[\s,]+', cleaned):
                    dep = dep.strip('`').strip()
                    if dep and dep not in ['', '-', '|', 'None', 'none']:
                        deps.append(dep)
    return deps

def parse_creator(md):
    match = re.search(r'Created\s+(?:with\s*)?(?:by\s+)?\[([^\]]+)\]', md)
    if match:
        return match.group(1)
    match = re.search(r'Created\s+(?:with\s*)?(?:by\s+)?(\w+)', md)
    if match:
        return match.group(1)
    return ""

def guess_animation_type(md, name, category):
    md_lower = md.lower()
    if 'scroll' in md_lower or 'scrolltrigger' in md_lower:
        return "scroll"
    if 'hover' in md_lower:
        return "hover"
    if 'click' in md_lower:
        return "click"
    if 'intersection' in md_lower:
        return "scroll"
    if category == "backgrounds":
        return "continuous"
    return "mount"

def guess_tech_stack(deps):
    stack = ["React"]
    dep_str = ' '.join(deps).lower()
    if 'gsap' in dep_str:
        stack.append("GSAP")
    if 'framer-motion' in dep_str or 'motion' in dep_str:
        stack.append("Framer Motion")
    if 'three' in dep_str:
        stack.append("Three.js")
    if '@react-three' in dep_str:
        stack.append("React Three Fiber")
    if 'ogl' in dep_str:
        stack.append("OGL")
    return stack

total = len(components)
success = 0
failed = []
skipped = []

already_done = set()
for f in os.listdir(DETAILS_DIR):
    if f.endswith('.json'):
        already_done.add(f.replace('.json', ''))

print(f"Processing {total} components ({len(already_done)} already done)")

for i, comp in enumerate(components):
    slug = comp['slug']
    url = comp['url']
    name = comp['name']
    category = comp['category']
    
    if slug in already_done:
        print(f"[{i+1}/{total}] SKIP {name}")
        skipped.append(slug)
        success += 1
        continue
    
    print(f"[{i+1}/{total}] {name}...", end=" ", flush=True)
    
    try:
        result = app.scrape(url, formats=["markdown"])
        md = result.markdown or ""
        
        with open(os.path.join(RAW_MD_DIR, f"{slug}.md"), 'w') as f:
            f.write(md)
        
        props = parse_props(md)
        deps = parse_dependencies(md)
        creator = parse_creator(md)
        animation_type = guess_animation_type(md, name, category)
        tech_stack = guess_tech_stack(deps)
        
        detail = {
            "name": name,
            "slug": slug,
            "url": url,
            "source": "reactbits",
            "category": category,
            "description": "",
            "animation_type": animation_type,
            "animation_description": "",
            "tech_stack": tech_stack,
            "dependencies": deps,
            "props": props,
            "creator": creator,
            "has_source_code": False,
            "free": True
        }
        
        with open(os.path.join(DETAILS_DIR, f"{slug}.json"), 'w') as f:
            json.dump(detail, f, indent=2)
        
        success += 1
        print(f"OK ({len(props)}p, {len(deps)}d)")
        
    except Exception as e:
        failed.append({"slug": slug, "error": str(e)})
        print(f"FAIL: {e}")
    
    time.sleep(1.5)

print(f"\n=== PASS 1 COMPLETE ===")
print(f"Success: {success}/{total} | Failed: {len(failed)} | Skipped: {len(skipped)}")
if failed:
    for f in failed:
        print(f"  FAIL: {f['slug']}: {f['error']}")

report = {
    "pass": 1, "total": total, "success": success,
    "failed": len(failed), "skipped": len(skipped),
    "failed_details": failed
}
with open(os.path.join(BASE_DIR, "pass1-report.json"), 'w') as f:
    json.dump(report, f, indent=2)
