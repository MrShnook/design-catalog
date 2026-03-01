#!/usr/bin/env python3
"""Build fonts/catalog.md from all detail JSON files."""

import json
from pathlib import Path
from collections import defaultdict
from datetime import date

FONTS_DIR = Path("fonts")
DETAILS_DIR = FONTS_DIR / "details"
SPECIMENS_DIR = FONTS_DIR / "specimens"

# Category display order and friendly names
CATEGORY_ORDER = ["Sans", "Serif", "Display", "Script", "Slab", "Handwritten", "Other"]

# Load all detail files
all_fonts = []
for f in sorted(DETAILS_DIR.glob("*-detail.json")):
    with open(f) as fh:
        data = json.load(fh)
        data["_slug"] = f.stem.replace("-detail", "")
        all_fonts.append(data)

print(f"Building catalog from {len(all_fonts)} fonts...")

# Group by primary category
by_category = defaultdict(list)
for font in all_fonts:
    raw_cat = font.get("category", "Other")
    # Use first category if multiple listed (e.g. "Serif, Slab" -> "Serif")
    primary = raw_cat.split(",")[0].strip() if raw_cat else "Other"
    if primary not in CATEGORY_ORDER:
        primary = "Other"
    by_category[primary].append(font)

# Sort fonts within each category by name
for cat in by_category:
    by_category[cat].sort(key=lambda x: x["name"])

today = date.today().strftime("%Y-%m-%d")
total = len(all_fonts)

lines = [
    "# FontShare Design Catalog",
    f"*{total} free quality fonts — last updated: {today}*",
    "",
    "FontShare is a free, high-quality font platform by Indian Type Foundry (ITF).",
    "All fonts are free to use for personal and commercial projects under their respective licenses.",
    "",
    "**Quick Navigation:**",
]

# TOC
for cat in CATEGORY_ORDER:
    if cat in by_category:
        count = len(by_category[cat])
        anchor = cat.lower().replace(" ", "-").replace(",", "")
        lines.append(f"- [{cat} ({count} fonts)](#{anchor})")

lines.append("")
lines.append("---")
lines.append("")

def format_styles(font):
    """Format style count as a short string."""
    s = font.get("styles", {})
    static = s.get("total_static", 0)
    variable = s.get("total_variable", 0)
    parts = []
    if static: parts.append(f"{static}st")
    if variable: parts.append(f"{variable}var")
    return "+".join(parts) if parts else "—"

def format_tags(font):
    tags = font.get("tags", [])
    return ", ".join(tags[:3]) if tags else "—"

def format_best_for(font):
    """Infer best use from tags/description."""
    tags = [t.lower() for t in font.get("tags", [])]
    desc = (font.get("description", "") or "").lower()
    cat = (font.get("category", "") or "").lower()
    
    hints = []
    if any(t in tags for t in ["branding", "logos"]): hints.append("Branding")
    if any(t in tags for t in ["editorial", "magazines"]): hints.append("Editorial")
    if any(t in tags for t in ["web", "ui", "app"]): hints.append("Web/UI")
    if any(t in tags for t in ["display", "headlines", "banners"]): hints.append("Headlines")
    if any(t in tags for t in ["body text", "books"]): hints.append("Body text")
    if not hints:
        if "display" in cat: hints.append("Display/Headlines")
        elif "script" in cat or "handwritten" in cat: hints.append("Decorative")
        elif "mono" in font.get("name", "").lower() or "mono" in font.get("_slug", "").lower(): hints.append("Code/UI")
        elif "serif" in cat: hints.append("Editorial/Web")
        else: hints.append("General use")
    
    return ", ".join(hints[:2])

for cat in CATEGORY_ORDER:
    if cat not in by_category:
        continue
    
    fonts = by_category[cat]
    anchor = cat.lower().replace(" ", "-")
    
    lines.append(f"## {cat} ({len(fonts)} fonts)")
    lines.append("")
    lines.append("| Font | Designer | Glyphs | Languages | Styles | Tags | Best For |")
    lines.append("|------|----------|--------|-----------|--------|------|----------|")
    
    for font in fonts:
        slug = font["_slug"]
        name = font["name"]
        designer = font.get("designer", "—") or "—"
        # Shorten long designer names
        if len(designer) > 25:
            designer = designer[:22] + "..."
        glyphs = font.get("glyphs", 0) or "—"
        langs = font.get("supported_languages", 0) or "—"
        styles = format_styles(font)
        tags = format_tags(font)
        best_for = format_best_for(font)
        
        # Check if specimen exists
        has_specimen = (SPECIMENS_DIR / f"{slug}.png").exists()
        spec_link = f"[specimen](specimens/{slug}.png)" if has_specimen else "—"
        
        name_link = f"[{name}](details/{slug}-detail.json)"
        
        lines.append(f"| {name_link} | {designer} | {glyphs} | {langs} | {styles} | {tags} | {best_for} |")
    
    lines.append("")

# Add a quick-reference section for agents
lines.append("---")
lines.append("")
lines.append("## Agent Quick Reference")
lines.append("")
lines.append("Use this catalog to pick fonts for design work. Key selection criteria:")
lines.append("")
lines.append("**For SaaS/Tech products:** General Sans, Space Grotesk, Plus Jakarta Sans, Satoshi, Outfit, Switzer")
lines.append("**For editorial/magazine:** Zodiak, Gambetta, Sentient, Erode, Lora, Literata")
lines.append("**For branding/logos:** Clash Display, Clash Grotesk, Cabinet Grotesk, Panchang, Satoshi")
lines.append("**For display/impact:** Bebas Neue, Tanker, Nippo, Anton, Sharpie, Array")
lines.append("**For script/decorative:** Telma, Britney, Dancing Script, Melodrama")
lines.append("**For code/mono:** JetBrains Mono, Azeret Mono")
lines.append("**For friendly/rounded:** Nunito, Quicksand, Pally, Roundo, Chillax")
lines.append("**Variable fonts:** Satoshi, General Sans, Zodiak, Erode, Manrope, Archivo (look for 'var' in Styles)")
lines.append("")
lines.append("All fonts: Free for commercial use (verify license in detail JSON for specifics).")
lines.append("")

catalog_text = "\n".join(lines)
catalog_path = FONTS_DIR / "catalog.md"
with open(catalog_path, "w") as f:
    f.write(catalog_text)

print(f"Catalog written to {catalog_path}")
print(f"Total lines: {len(lines)}")
print(f"\nCategory breakdown:")
for cat in CATEGORY_ORDER:
    if cat in by_category:
        print(f"  {cat}: {len(by_category[cat])}")
