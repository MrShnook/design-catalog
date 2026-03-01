#!/usr/bin/env python3
"""FontShare Batch Scraper - Phase 2"""

import json
import os
import re
import time
from pathlib import Path

from firecrawl import FirecrawlApp

REPO_DIR = Path(__file__).parent
FONTS_DIR = REPO_DIR / "fonts"
DETAILS_DIR = FONTS_DIR / "details"
RAW_DIR = FONTS_DIR / "raw_markdown"
FONT_LIST = FONTS_DIR / "font-list.json"

RAW_DIR.mkdir(exist_ok=True)

with open(FONT_LIST) as f:
    fonts = json.load(f)

app = FirecrawlApp()

results = {
    "total": len(fonts),
    "scraped": 0,
    "skipped": 0,
    "failed": 0,
    "failures": [],
    "skipped_fonts": ["satoshi"],
}


def parse_font_markdown(markdown, font_info):
    """Parse the Firecrawl markdown into structured detail JSON."""
    detail = {
        "name": font_info["name"],
        "url": font_info["url"],
        "category": font_info["category"],
        "designer": "",
        "foundry": "",
        "source": "",
        "license": "",
        "styles": {"static": [], "variable": [], "total_static": 0, "total_variable": 0},
        "glyphs": 0,
        "supported_languages": 0,
        "version": "",
        "fontshare_debut": "",
        "tags": [],
        "description": "",
        "features": {},
        "languages_list": "",
    }

    text = markdown

    # ---- HEADER SECTION (before Details) ----
    # Designer - from "Designed By [Name]" or "Designed By\n\n[Name]"
    dm = re.search(r"Designed\s+By\s*\n*\[([^\]]+)\]", text)
    if dm:
        detail["designer"] = dm.group(1).strip()
    else:
        dm2 = re.search(r"Designed\s+By\s*\n+([^\n\[]+)", text)
        if dm2:
            detail["designer"] = dm2.group(1).strip()

    # Source - Closed Source or Open Source near top
    if "Closed Source" in text:
        detail["source"] = "Closed Source"
    elif "Open Source" in text:
        detail["source"] = "Open Source"

    # Glyphs
    gm = re.search(r"(\d+)\s+Glyphs?", text)
    if gm:
        detail["glyphs"] = int(gm.group(1))

    # ---- SPECIFICATIONS SECTION ----
    specs_start = text.find("### Specifications")
    if specs_start < 0:
        specs_start = text.find("## License")
    
    if specs_start > 0:
        specs_section = text[specs_start:]
        
        # Designed By in specs
        dm3 = re.search(r"Designed\s+By\s*\n+\[([^\]]+)\]", specs_section)
        if dm3:
            detail["designer"] = dm3.group(1).strip()
        
        # Category
        cm = re.search(r"Category\s*\n+(\w+)", specs_section)
        if cm:
            detail["category"] = cm.group(1).strip()
        
        # Available Styles - parse the number
        sm = re.search(r"Available Styles\s*\n+(\d+)\s+Static,?\s*(\d+)\s+Variable", specs_section)
        if sm:
            pass  # We'll get actual style names below
        
        # Style names between "Available Styles" and "Supported Languages"
        styles_match = re.search(r"Available Styles.*?\n(.*?)Supported Languages", specs_section, re.DOTALL)
        if styles_match:
            style_block = styles_match.group(1)
            style_lines = [l.strip() for l in style_block.strip().split("\n") if l.strip()]
            static = []
            variable = []
            for s in style_lines:
                # Skip metadata lines
                if re.match(r"^\d+\s+Static", s) or not s or s.startswith("#"):
                    continue
                if "variable" in s.lower() and len(s) < 30:
                    variable.append(s)
                else:
                    if len(s) < 40 and not any(c in s for c in ["[", "(", "|", "#"]):
                        static.append(s)
            detail["styles"]["static"] = static
            detail["styles"]["variable"] = variable
            detail["styles"]["total_static"] = len(static)
            detail["styles"]["total_variable"] = len(variable)

        # Supported Languages count
        lm = re.search(r"Supported Languages\s*\n+(\d+)", specs_section)
        if lm:
            detail["supported_languages"] = int(lm.group(1))
        
        # Languages list - the big block after the count
        ll = re.search(r"Supported Languages\s*\n+\d+\s*\n+((?:[A-Z][\w\s\(\)éàáâãäåæçèêëìíîïðñòóôõöùúûüýþÿāēīōūǎǐǒǔ'\-]+,?\s*){5,})", specs_section)
        if ll:
            detail["languages_list"] = ll.group(1).strip()
        
        # Version
        vm = re.search(r"Version\s*\n+(\d+\.?\d*)", specs_section)
        if vm:
            detail["version"] = vm.group(1)
        
        # Debut
        dbm = re.search(r"Fontshare Debut\s*\n+(\d{1,2}\s+\w+\s+\d{4})", specs_section)
        if dbm:
            detail["fontshare_debut"] = dbm.group(1)
        
        # Tags
        tm = re.search(r"Tags\s*/?\s*Keywords\s*\n+([^\n]+)", specs_section)
        if tm:
            tags_str = tm.group(1).strip()
            detail["tags"] = [t.strip() for t in tags_str.split(",") if t.strip()]
        
        # License
        lim = re.search(r"License\s*\n+((?:Closed|Open)\s+Source\s*/?\s*[^\n]*)", specs_section)
        if lim:
            detail["license"] = lim.group(1).strip()

    # ---- STORY/DESCRIPTION ----
    story_match = re.search(r"### Story\s*\n+(.*?)(?:\n##|\Z)", text, re.DOTALL)
    if story_match:
        desc = story_match.group(1).strip()
        # Clean up: remove markdown artifacts
        desc = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', desc)  # links to text
        detail["description"] = desc

    # ---- FOUNDRY ----
    # Usually the designer IS the foundry on FontShare, or try to find it
    if detail["designer"]:
        detail["foundry"] = detail["designer"]
    
    # Override if we find explicit foundry mention
    fm = re.search(r"(?:Published|Foundry)[:\s]+([^\n]+)", text)
    if fm:
        detail["foundry"] = fm.group(1).strip()

    return detail


def scrape_font(font_info):
    slug = font_info["slug"]
    url = font_info["url"]
    try:
        result = app.scrape(url, formats=["markdown"], wait_for=5000)
        md = result.markdown
        if not md:
            return None

        # Save raw markdown
        with open(RAW_DIR / f"{slug}.md", "w") as f:
            f.write(md)

        return parse_font_markdown(md, font_info)
    except Exception as e:
        print(f"    ERROR: {e}", flush=True)
        return None


def main():
    print(f"FontShare Batch Scraper - {len(fonts)} fonts", flush=True)
    print("=" * 60, flush=True)

    for i, font in enumerate(fonts):
        slug = font["slug"]

        if slug == "satoshi":
            results["skipped"] += 1
            print(f"[{i+1:3d}/100] SKIP {font['name']} (done)", flush=True)
            continue

        detail_file = DETAILS_DIR / f"{slug}-detail.json"
        if detail_file.exists():
            results["skipped"] += 1
            results["skipped_fonts"].append(slug)
            print(f"[{i+1:3d}/100] SKIP {font['name']} (exists)", flush=True)
            continue

        print(f"[{i+1:3d}/100] {font['name']}...", end=" ", flush=True)

        detail = scrape_font(font)
        if detail:
            with open(detail_file, "w") as f:
                json.dump(detail, f, indent=2, ensure_ascii=False)
            results["scraped"] += 1
            styles_count = detail["styles"]["total_static"] + detail["styles"]["total_variable"]
            print(f"OK ({styles_count} styles, {detail['glyphs']} glyphs)", flush=True)
        else:
            results["failed"] += 1
            results["failures"].append(slug)
            print("FAIL", flush=True)

        # Rate limit
        time.sleep(1.5)

    # Save report
    with open(FONTS_DIR / "scrape-report.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 60, flush=True)
    print(f"Done: {results['scraped']} scraped, {results['skipped']} skipped, {results['failed']} failed", flush=True)
    if results["failures"]:
        print(f"Failed: {', '.join(results['failures'])}", flush=True)


if __name__ == "__main__":
    main()
