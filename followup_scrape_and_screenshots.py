#!/usr/bin/env python3
"""
Follow-up: Re-scrape 8 skipped components + capture 61 missing screenshots.
"""

import json
import os
import re
import sys
import time
import traceback
from pathlib import Path

REPO_DIR = Path(__file__).parent
DETAILS_DIR = REPO_DIR / "components" / "details"
RAW_DIR = REPO_DIR / "components" / "raw_markdown"
PREVIEWS_DIR = REPO_DIR / "components" / "previews"
LIST_FILE = REPO_DIR / "components" / "component-list.json"

PREVIEWS_DIR.mkdir(exist_ok=True)
RAW_DIR.mkdir(exist_ok=True)
DETAILS_DIR.mkdir(exist_ok=True)

# ==================== PART 1: RE-SCRAPE 8 COMPONENTS ====================

RESCRAPE_SLUGS = [
    "tooltip-card", "macbook-scroll", "3d-card-effect", "ascii-art",
    "canvas-text", "3d-globe", "dither-shader", "dotted-glow-background"
]

# --- Helper functions ---

def infer_category(slug, raw_text, markdown):
    cl = f"{slug} {raw_text} {markdown[:3000]}".lower()
    if any(w in slug for w in ["background", "aurora", "grid-and-dot", "stars-background", "noise"]):
        return "Backgrounds"
    if any(w in slug for w in ["card", "bento"]) and "card-stack" not in slug:
        return "Cards"
    if any(w in slug for w in ["text-", "flip-words", "typewriter", "wavy-text", "colourful", "encrypted"]):
        return "Text Effects"
    if any(w in slug for w in ["navbar", "sidebar", "dock", "menu", "resizable-navbar"]):
        return "Navigation"
    if "hero" in slug:
        return "Hero Sections"
    if any(w in slug for w in ["carousel", "slider", "marquee"]):
        return "Carousels & Sliders"
    if any(w in slug for w in ["modal", "overlay", "expandable"]):
        return "Modals & Overlays"
    if any(w in slug for w in ["grid", "layout", "tabs", "timeline", "sticky-scroll"]):
        return "Layout"
    if any(w in slug for w in ["input", "form", "file-upload", "signup", "login", "placeholder"]):
        return "Inputs & Forms"
    if any(w in slug for w in ["loader", "multi-step"]):
        return "Loaders"
    if any(w in slug for w in ["sparkle", "meteor", "beam", "lamp", "spotlight", "glowing", "glow", "shimmer", "shooting", "vortex", "dither", "ascii"]):
        return "Decorative"
    if any(w in slug for w in ["globe", "world-map", "3d-globe"]):
        return "Data Viz"
    if "tooltip" in slug:
        return "Tooltips"
    if "button" in slug:
        return "Buttons"
    if "compare" in slug:
        return "Comparison"
    if any(w in slug for w in ["canvas", "pixel"]):
        return "Canvas Effects"
    if any(w in slug for w in ["scroll", "parallax", "tracing"]):
        return "Scroll Effects"
    return "Components"

def infer_animation_type(slug, raw_text, markdown):
    cl = f"{slug} {raw_text} {markdown[:2000]}".lower()
    if any(w in cl for w in ["hover", "mouseover", "mouse enter", "onhover"]):
        if "scroll" in cl:
            return "hover+scroll"
        return "hover"
    if any(w in cl for w in ["scroll", "parallax", "sticky", "useScroll"]):
        return "scroll"
    if any(w in cl for w in ["click", "press", "onclick"]):
        return "click"
    if any(w in cl for w in ["continuous", "infinite", "loop", "autoplay", "perpetual"]):
        return "continuous"
    return "load"

def extract_tech_stack(markdown):
    stack = []
    cl = markdown.lower()
    if any(w in cl for w in ["framer", "motion.", "animate", "useMotionValue"]):
        stack.append("Framer Motion")
    if "tailwind" in cl or "className" in markdown:
        stack.append("Tailwind CSS")
    if any(w in cl for w in ["three", "drei", "fiber", "@react-three"]):
        stack.append("Three.js")
    if "gsap" in cl:
        stack.append("GSAP")
    if "canvas" in cl:
        stack.append("Canvas API")
    if "svg" in cl:
        stack.append("SVG")
    if any(w in cl for w in ["use client", "usestate", "useeffect", "useref"]):
        stack.append("React")
    if any(w in cl for w in ["webgl", "shader", "glsl", "fragment shader"]):
        stack.append("WebGL")
    if not stack:
        stack = ["Tailwind CSS"]
    return stack

def extract_inspired_by(raw_text, markdown):
    text = f"{raw_text} {markdown[:1000]}".lower()
    inspirations = {
        "Linear": "linear", "Apple": "apple", "Clerk": "clerk",
        "Stripe": "stripe", "Vercel": "vercel", "GitHub": "github",
        "Fey": "fey", "Sentry": "sentry", "Cal.com": "cal.com", "Algolia": "algolia",
    }
    found = []
    for name, kw in inspirations.items():
        if re.search(rf"(inspired|seen on|like|from)\s+.*{kw}", text):
            found.append(name)
        elif kw in raw_text.lower():
            found.append(name)
    return ", ".join(set(found)) if found else "N/A"

def extract_install_command(markdown):
    patterns = [
        r"(npx\s+shadcn[^\n]+)",
        r"(npx\s+aceternity-ui[^\n]+)",
        r"(npm\s+install[^\n]+)",
        r"(pnpm\s+add[^\n]+)",
    ]
    for pat in patterns:
        m = re.search(pat, markdown)
        if m:
            return m.group(1).strip()
    return ""

def extract_dependencies(markdown):
    deps = set()
    patterns = [
        r"npm\s+(?:install|i)\s+([\w@/.-]+)",
        r"pnpm\s+add\s+([\w@/.-]+)",
        r"from\s+['\"](@?[\w/-]+)['\"]",
    ]
    skip = {"react", "next", "next/image", "next/link", "next/font", "react-dom", "./", "../"}
    for pat in patterns:
        for m in re.findall(pat, markdown):
            pkg = m.strip()
            if not pkg.startswith(".") and pkg not in skip and not pkg.startswith("react"):
                deps.add(pkg)
    return sorted(deps)[:10]

def extract_code_snippet(markdown, slug):
    code_blocks = re.findall(r"```(?:tsx?|jsx?|css)?\n(.*?)```", markdown, re.DOTALL)
    if not code_blocks:
        return f"npx shadcn@latest add @aceternity/{slug}"
    best_block = ""
    best_score = -1
    for block in code_blocks:
        score = 0
        animation_kws = [
            "animate", "variants", "transition", "motion.", "useMotionValue",
            "useSpring", "useTransform", "keyframes", "transform",
            "@keyframes", "animation:", "whileHover", "whileInView",
            "useAnimate", "stagger", "spring", "easing",
            "translateX", "translateY", "translateZ", "rotate", "scale",
            "opacity", "perspective", "useScroll", "scrollYProgress",
        ]
        for kw in animation_kws:
            if kw in block:
                score += 3
        lines = block.strip().split("\n")
        if len(lines) > 80:
            score -= 2
        if len(lines) < 3:
            score -= 5
        if score > best_score:
            best_score = score
            best_block = block
    if not best_block:
        best_block = max(code_blocks, key=lambda b: len(b) if len(b) < 5000 else 0)
    lines = best_block.strip().split("\n")
    if len(lines) > 50:
        best_start = 0
        best_density = 0
        window = 50
        for i in range(len(lines) - window + 1):
            chunk = "\n".join(lines[i:i+window]).lower()
            density = sum(1 for kw in ["animate", "motion", "transform", "transition", "variant", "spring", "keyframe"] if kw in chunk)
            if density > best_density:
                best_density = density
                best_start = i
        lines = lines[best_start:best_start+window]
    return "\n".join(lines)

def extract_description(raw_text, slug, markdown=""):
    paras = re.findall(r"\n\n([A-Z][^#\n]{10,300})", markdown[:2000])
    if paras:
        return paras[0].strip()
    for i in range(len(raw_text) - 1, 0, -1):
        if raw_text[i-1].islower() and raw_text[i].isupper():
            return raw_text[i:].strip()
    return raw_text

ANIMATION_DESCS = {
    "3d-card-effect": "Card tilts in 3D space following mouse position with perspective transform. Inner elements float upward with varying translateZ depths on hover. Smooth spring transition on enter/exit.",
    "tooltip-card": "Floating tooltip card appears and follows cursor position on hover with spring-based animation. Card has a smooth opacity and scale transition.",
    "macbook-scroll": "Macbook mockup with content sliding out of the screen as user scrolls. Lid opens with scroll progress, revealing inner content with parallax depth.",
    "ascii-art": "Converts images to ASCII art in real-time with customizable character sets and color modes. Characters update dynamically based on pixel brightness.",
    "canvas-text": "Animated text rendered on HTML canvas with colorful curved lines tracing letter paths. Lines animate in with drawing motion.",
    "3d-globe": "Interactive 3D globe with tooltip labels and avatar markers at geographic coordinates. Globe rotates and supports camera orbit controls.",
    "dither-shader": "Real-time ordered dithering effect applied to images via WebGL shader. Creates a retro pixel art aesthetic with configurable dither patterns.",
    "dotted-glow-background": "Background pattern of dots with animated glow effects and opacity transitions. Dots pulse and glow creating an ambient atmosphere.",
}

def make_animation_description(slug, raw_text, markdown, category, animation_type):
    if slug in ANIMATION_DESCS:
        return ANIMATION_DESCS[slug]
    return f"Interactive UI component with {animation_type} animation effect. Provides visual feedback and smooth transitions."

def infer_tags(slug, raw_text, markdown):
    tags = []
    cl = f"{slug} {raw_text} {markdown[:2000]}".lower()
    tag_checks = [
        ("hover", ["hover", "mouse"]),
        ("scroll", ["scroll", "parallax"]),
        ("3d", ["3d", "perspective", "three"]),
        ("text", ["text", "word", "typewriter", "font"]),
        ("background", ["background", "bg-"]),
        ("card", ["card"]),
        ("animation", ["animate", "motion", "transition"]),
        ("interactive", ["click", "drag", "pointer", "cursor"]),
        ("gradient", ["gradient"]),
        ("particles", ["particle", "sparkle", "star"]),
        ("canvas", ["canvas"]),
        ("shader", ["shader", "webgl", "glsl"]),
        ("svg", ["svg"]),
        ("loading", ["loader", "loading", "spinner"]),
        ("form", ["form", "input", "signup"]),
        ("navigation", ["nav", "menu", "sidebar"]),
        ("layout", ["grid", "layout", "bento"]),
        ("image", ["image", "photo", "gallery"]),
    ]
    for tag, keywords in tag_checks:
        if any(kw in cl for kw in keywords):
            tags.append(tag)
    return tags[:6] if tags else ["ui"]

def infer_use_cases(category, slug):
    use_case_map = {
        "Backgrounds": ["Hero sections", "Landing pages", "Feature sections"],
        "Cards": ["Feature cards", "Product showcases", "Team members"],
        "Text Effects": ["Headlines", "Hero text", "Loading states"],
        "Navigation": ["App navigation", "Dashboards", "Marketing sites"],
        "Hero Sections": ["Landing pages", "Product pages", "Marketing sites"],
        "Carousels & Sliders": ["Testimonials", "Image galleries", "Feature showcases"],
        "Modals & Overlays": ["Dialogs", "Image zoom", "Detail views"],
        "Layout": ["Feature sections", "Dashboards", "Content pages"],
        "Inputs & Forms": ["Sign-up forms", "Contact forms", "Search"],
        "Loaders": ["Page transitions", "Data loading", "Progress indicators"],
        "Decorative": ["Visual accents", "Hero sections", "Background effects"],
        "Data Viz": ["Data dashboards", "Location displays", "Analytics"],
        "Tooltips": ["Navigation hints", "Info cards", "Link previews"],
        "Buttons": ["CTAs", "Form submissions", "Navigation"],
        "Comparison": ["Before/after", "Feature comparison", "Pricing"],
        "Canvas Effects": ["Hero sections", "Interactive art", "Landing pages"],
        "Scroll Effects": ["Landing pages", "Storytelling", "Product showcases"],
    }
    return use_case_map.get(category, ["General UI", "Interactive sections"])


def rescrape_components():
    """Re-scrape the 8 skipped components via Firecrawl."""
    print("\n" + "="*60)
    print("PART 1: Re-scraping 8 skipped components via Firecrawl")
    print("="*60 + "\n")

    from firecrawl import FirecrawlApp
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key:
        print("ERROR: FIRECRAWL_API_KEY not set!")
        return {"success": 0, "failed": 8, "failures": RESCRAPE_SLUGS}

    app = FirecrawlApp(api_key=api_key)

    with open(LIST_FILE) as f:
        comp_list = json.load(f)
    slug_to_item = {c["slug"]: c for c in comp_list}

    results = {"success": 0, "failed": 0, "failures": []}

    for i, slug in enumerate(RESCRAPE_SLUGS):
        item = slug_to_item.get(slug, {})
        url = item.get("url", f"https://ui.aceternity.com/components/{slug}")
        raw_text = item.get("raw_text", slug.replace("-", " ").title())
        comp_type = item.get("type", "component")

        print(f"[{i+1}/{len(RESCRAPE_SLUGS)}] Scraping: {slug}...", end=" ", flush=True)

        try:
            result = app.scrape(url, formats=["markdown"])
            markdown = getattr(result, "markdown", "") or ""

            if not markdown:
                print("FAIL (no markdown returned)")
                results["failed"] += 1
                results["failures"].append(slug)
                continue

            # Save raw markdown
            raw_file = RAW_DIR / f"{slug}.md"
            raw_file.write_text(markdown, encoding="utf-8")

            # Parse into structured JSON
            category = infer_category(slug, raw_text, markdown)
            animation_type = infer_animation_type(slug, raw_text, markdown)
            description = extract_description(raw_text, slug, markdown)
            animation_desc = make_animation_description(slug, raw_text, markdown, category, animation_type)
            code_snippet = extract_code_snippet(markdown, slug)
            tech_stack = extract_tech_stack(markdown)
            inspired_by = extract_inspired_by(raw_text, markdown)
            install_cmd = extract_install_command(markdown)
            dependencies = extract_dependencies(markdown)
            tags = infer_tags(slug, raw_text, markdown)
            use_cases = infer_use_cases(category, slug)
            free = comp_type == "component"

            name = slug.replace("-", " ").title()
            name_match = re.search(r"#\s+(.+?)(?:\n|$)", markdown[:500])
            if name_match:
                candidate = name_match.group(1).strip()
                if len(candidate) > 2 and "aceternity" not in candidate.lower():
                    name = candidate

            detail = {
                "name": name,
                "slug": slug,
                "url": url,
                "type": comp_type,
                "description": description,
                "category": category,
                "tags": tags,
                "animation_type": animation_type,
                "animation_description": animation_desc,
                "tech_stack": tech_stack,
                "inspired_by": inspired_by,
                "dependencies": dependencies,
                "code_snippet": code_snippet,
                "install_command": install_cmd,
                "use_cases": use_cases,
                "free": free,
            }

            detail_file = DETAILS_DIR / f"{slug}.json"
            detail_file.write_text(json.dumps(detail, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"OK ({category} / {animation_type})")
            results["success"] += 1

        except Exception as e:
            print(f"FAIL ({str(e)[:80]})")
            results["failed"] += 1
            results["failures"].append(slug)
            traceback.print_exc()

        if i < len(RESCRAPE_SLUGS) - 1:
            time.sleep(1.5)

    print(f"\nPart 1 done: {results['success']} success, {results['failed']} failed")
    if results["failures"]:
        print(f"  Failed: {results['failures']}")
    return results


# ==================== PART 2: CAPTURE 61 SCREENSHOTS ====================

SCREENSHOT_SLUGS = [
    "blog-content-sections", "blog-sections", "hero-sections", "hero-sections-free",
    "hover-border-gradient", "illustrations", "images-badge", "images-slider",
    "infinite-moving-cards", "keyboard", "lamp-effect", "layout-grid",
    "layout-text-flip", "lens", "link-preview", "loader",
    "login-and-signup-sections", "logo-clouds", "macbook-scroll", "meteors",
    "moving-border", "multi-step-loader", "navbar-menu", "navbars",
    "noise-background", "parallax-scroll", "pixelated-canvas",
    "placeholders-and-vanish-input", "pointer-highlight", "pricing-sections",
    "resizable-navbar", "scales", "shaders",
    "shooting-stars-and-stars-background", "sidebar", "sidebars",
    "signup-form", "sparkles", "spotlight", "spotlight-new",
    "stateful-button", "stats-sections", "sticky-banner",
    "sticky-scroll-reveal", "svg-mask-effect", "tabs",
    "tailwindcss-buttons", "testimonials", "text-animations",
    "text-generate-effect", "text-hover-effect", "text-reveal-card",
    "timeline", "tooltip-card", "tracing-beam", "typewriter-effect",
    "vortex", "wavy-background", "webcam-pixel-grid", "wobble-card", "world-map"
]

def capture_screenshots():
    """Capture 61 missing screenshots using Playwright."""
    print("\n" + "="*60)
    print("PART 2: Capturing 61 missing screenshots via Playwright")
    print("="*60 + "\n")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: Playwright not installed!")
        return {"success": 0, "failed": len(SCREENSHOT_SLUGS)}

    with open(LIST_FILE) as f:
        comp_list = json.load(f)
    slug_to_item = {c["slug"]: c for c in comp_list}

    results = {"success": 0, "failed": 0, "skipped": 0, "failures": []}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage",
                   "--disable-gpu", "--disable-web-security"]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            color_scheme="dark",
        )
        page = context.new_page()

        for i, slug in enumerate(SCREENSHOT_SLUGS):
            out_path = PREVIEWS_DIR / f"{slug}.png"

            if out_path.exists():
                print(f"[{i+1}/{len(SCREENSHOT_SLUGS)}] {slug} - skipped (exists)")
                results["skipped"] += 1
                continue

            item = slug_to_item.get(slug)
            if item:
                url = item["url"]
            else:
                url = f"https://ui.aceternity.com/components/{slug}"

            print(f"[{i+1}/{len(SCREENSHOT_SLUGS)}] {slug}...", end=" ", flush=True)

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=25000)
                page.wait_for_timeout(3000)

                try:
                    preview = page.locator('[data-preview], .preview-container, [class*="preview"]').first
                    if preview.is_visible(timeout=2000):
                        preview.screenshot(path=str(out_path))
                    else:
                        page.screenshot(path=str(out_path), clip={"x": 0, "y": 0, "width": 1280, "height": 800})
                except Exception:
                    page.screenshot(path=str(out_path), clip={"x": 0, "y": 0, "width": 1280, "height": 800})

                print("OK")
                results["success"] += 1

            except Exception as e:
                print(f"FAIL ({str(e)[:60]})")
                results["failed"] += 1
                results["failures"].append({"slug": slug, "error": str(e)[:100]})

            time.sleep(2.5)

        browser.close()

    print(f"\nPart 2 done: {results['success']} success, {results['skipped']} skipped, {results['failed']} failed")
    if results["failures"]:
        print(f"  Failures: {[f['slug'] for f in results['failures']]}")
    return results


if __name__ == "__main__":
    part = sys.argv[1] if len(sys.argv) > 1 else "all"
    if part in ("all", "scrape", "1"):
        scrape_results = rescrape_components()
    if part in ("all", "screenshots", "2"):
        screenshot_results = capture_screenshots()
    print("\n" + "="*60)
    print("ALL DONE")
    print("="*60)
