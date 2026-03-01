#!/usr/bin/env python3
"""
Scrape all Aceternity UI components and blocks using Firecrawl.
Extracts metadata, animation descriptions, and code snippets.
"""

import json
import os
import re
import time
import sys
import traceback
from pathlib import Path

from firecrawl import FirecrawlApp

# ── Paths ──────────────────────────────────────────────────────────
BASE_DIR = Path(os.path.expanduser("~/repos/design-catalog/components"))
LIST_FILE = BASE_DIR / "component-list.json"
DETAILS_DIR = BASE_DIR / "details"
RAW_DIR = BASE_DIR / "raw_markdown"
REPORT_FILE = BASE_DIR / "scrape-report.json"

DETAILS_DIR.mkdir(exist_ok=True)
RAW_DIR.mkdir(exist_ok=True)

# ── Firecrawl ──────────────────────────────────────────────────────
app = FirecrawlApp()

# ── Category inference ─────────────────────────────────────────────
CATEGORY_KEYWORDS = {
    "Backgrounds": ["background", "aurora", "beam", "gradient-bg", "grid-bg", "dot-bg", "noise", "ripple", "star-background", "vortex", "wave-background", "boxes-bg", "pattern"],
    "Cards": ["card", "evervault", "focus-card", "wobble", "hover-effect", "direction-aware", "feature-card"],
    "Text Effects": ["text", "typewriter", "generate-effect", "flip-words", "colourful", "colorful", "encrypted", "wavy", "text-reveal", "text-hover"],
    "Navigation": ["navbar", "dock", "sidebar", "banner", "resizable-navbar", "floating-nav", "tabs"],
    "Hero Sections": ["hero", "macbook-scroll", "container-scroll", "google-gemini-effect"],
    "Carousels & Sliders": ["carousel", "apple-cards", "infinite-moving", "images-slider", "parallax-scroll", "animated-testimonials"],
    "Modals & Overlays": ["modal", "expandable-card", "lens", "svg-mask"],
    "Layout": ["bento", "layout-grid", "feature-section", "timeline", "scroll-reveal", "sticky-scroll", "cover"],
    "Inputs & Forms": ["file-upload", "signup", "input", "placeholders-vanish", "form", "multi-step"],
    "Loaders": ["loader", "multi-step-loader"],
    "Decorative": ["sparkle", "meteor", "tracing-beam", "moving-border", "3d-pin", "following-pointer", "shooting-star", "border-magic", "confetti", "lamp", "candle", "glowing-effect", "glare"],
    "Data Viz": ["globe", "world-map"],
    "Tooltips": ["tooltip", "link-preview", "animated-tooltip"],
    "Buttons": ["button", "hover-border-gradient", "tailwind-buttons", "shimmer"],
    "Comparison": ["compare"],
}

def infer_category(slug, raw_text, markdown_content=""):
    text_lower = f"{slug} {raw_text}".lower()

    # Direct slug matching first
    slug_map = {
        "aurora-background": "Backgrounds",
        "background-beams": "Backgrounds",
        "background-beams-with-collision": "Backgrounds",
        "background-boxes": "Backgrounds",
        "background-gradient-animation": "Backgrounds",
        "background-lines": "Backgrounds",
        "dot-background": "Backgrounds",
        "grid-background": "Backgrounds",
        "grid-and-dot-backgrounds": "Backgrounds",
        "shooting-stars": "Backgrounds",
        "stars-background": "Backgrounds",
        "wavy-background": "Backgrounds",
        "3d-card-effect": "Cards",
        "card-hover-effect": "Cards",
        "card-spotlight-effect": "Cards",
        "direction-aware-hover-effect": "Cards",
        "evervault-card": "Cards",
        "focus-cards": "Cards",
        "wobble-card": "Cards",
        "glare-card": "Cards",
        "card-stack": "Cards",
        "flip-words": "Text Effects",
        "text-generate-effect": "Text Effects",
        "text-hover-effect": "Text Effects",
        "text-reveal-card": "Text Effects",
        "typewriter-effect": "Text Effects",
        "wavy-text": "Text Effects",
        "colourful-text": "Text Effects",
        "cool-mode": "Text Effects",
        "floating-navbar": "Navigation",
        "floating-dock": "Navigation",
        "resizable-navbar": "Navigation",
        "sidebar": "Navigation",
        "tabs": "Navigation",
        "hero-highlight": "Hero Sections",
        "hero-parallax": "Hero Sections",
        "macbook-scroll": "Hero Sections",
        "container-scroll-animation": "Hero Sections",
        "google-gemini-effect": "Hero Sections",
        "vortex": "Hero Sections",
        "lamp-effect": "Hero Sections",
        "apple-cards-carousel": "Carousels & Sliders",
        "animated-testimonials": "Carousels & Sliders",
        "carousel": "Carousels & Sliders",
        "images-slider": "Carousels & Sliders",
        "infinite-moving-cards": "Carousels & Sliders",
        "parallax-scroll": "Carousels & Sliders",
        "animated-modal": "Modals & Overlays",
        "expandable-card": "Modals & Overlays",
        "lens": "Modals & Overlays",
        "svg-mask-effect": "Modals & Overlays",
        "bento-grid": "Layout",
        "layout-grid": "Layout",
        "feature-sections-with-grid": "Layout",
        "timeline": "Layout",
        "sticky-scroll-reveal": "Layout",
        "cover": "Layout",
        "aceternity-ui-scroll-animation": "Layout",
        "file-upload": "Inputs & Forms",
        "signup-form": "Inputs & Forms",
        "placeholders-and-vanish-input": "Inputs & Forms",
        "multi-step-loader": "Loaders",
        "sparkles": "Decorative",
        "meteors": "Decorative",
        "tracing-beam": "Decorative",
        "moving-border": "Decorative",
        "3d-pin": "Decorative",
        "following-pointer": "Decorative",
        "shooting-stars-effect": "Decorative",
        "glowing-effect": "Decorative",
        "candle-mode": "Decorative",
        "globe": "Data Viz",
        "github-globe": "Data Viz",
        "world-map": "Data Viz",
        "tooltip-card": "Tooltips",
        "animated-tooltip": "Tooltips",
        "link-preview": "Tooltips",
        "tailwindcss-buttons": "Buttons",
        "hover-border-gradient": "Buttons",
        "shimmer-button": "Buttons",
        "compare": "Comparison",
    }

    if slug in slug_map:
        return slug_map[slug]

    # Score each category
    scores = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[cat] = score

    if scores:
        return max(scores, key=scores.get)

    if any(w in text_lower for w in ["scroll", "parallax", "reveal"]):
        return "Layout"
    if any(w in text_lower for w in ["hover", "effect"]):
        return "Decorative"
    return "Layout"


def infer_animation_type(slug, raw_text, markdown_content=""):
    text_lower = f"{slug} {raw_text} {markdown_content[:1000]}".lower()

    if any(w in text_lower for w in ["hover", "mouse over", "pointer"]):
        return "hover"
    if any(w in text_lower for w in ["scroll", "parallax", "viewport", "in view", "whileinview"]):
        return "scroll"
    if any(w in text_lower for w in ["click", "toggle", "press", "tap"]):
        return "click"
    if any(w in text_lower for w in ["drag", "swipe", "draggable"]):
        return "drag"
    if any(w in text_lower for w in ["continuous", "infinite", "loop", "sparkle", "meteor", "aurora", "shimmer", "shooting", "pulse", "float", "rotate", "spin"]):
        return "continuous"
    if any(w in text_lower for w in ["load", "mount", "enter", "appear", "generate", "typewriter", "reveal"]):
        return "load"
    return "load"


def infer_tags(slug, raw_text, markdown_content=""):
    text_lower = f"{slug} {raw_text} {markdown_content[:1000]}".lower()
    tags = []
    tag_checks = [
        ("hover", ["hover"]),
        ("3d", ["3d", "perspective", "tilt"]),
        ("scroll", ["scroll", "parallax"]),
        ("gradient", ["gradient"]),
        ("animation", ["animation", "motion", "animate"]),
        ("interactive", ["interactive", "mouse", "pointer", "drag"]),
        ("text", ["text", "typewriter", "typing"]),
        ("background", ["background"]),
        ("card", ["card"]),
        ("responsive", ["responsive"]),
        ("framer-motion", ["framer motion", "motion.div"]),
        ("tailwind", ["tailwind"]),
    ]
    for tag, keywords in tag_checks:
        if any(kw in text_lower for kw in keywords):
            tags.append(tag)
    return tags[:8]


def extract_tech_stack(markdown_content):
    stack = []
    cl = markdown_content.lower()
    if any(w in cl for w in ["framer", "motion.", "animate", "useMotionValue"]):
        stack.append("Framer Motion")
    if "tailwind" in cl or "className" in markdown_content:
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
    if not stack:
        stack = ["Tailwind CSS"]
    return stack


def extract_inspired_by(raw_text, markdown_content):
    text = f"{raw_text} {markdown_content[:1000]}".lower()
    inspirations = {
        "Linear": "linear",
        "Apple": "apple",
        "Clerk": "clerk",
        "Stripe": "stripe",
        "Vercel": "vercel",
        "GitHub": "github",
        "Fey": "fey",
        "Sentry": "sentry",
        "Cal.com": "cal.com",
        "Algolia": "algolia",
    }
    found = []
    for name, kw in inspirations.items():
        if re.search(rf"(inspired|seen on|like|from)\s+.*{kw}", text):
            found.append(name)
        elif kw in raw_text.lower():
            found.append(name)
    return ", ".join(set(found)) if found else "N/A"


def extract_install_command(markdown_content):
    patterns = [
        r"(npx\s+shadcn[^\n]+)",
        r"(npx\s+aceternity-ui[^\n]+)",
        r"(npm\s+install[^\n]+)",
        r"(pnpm\s+add[^\n]+)",
    ]
    for pat in patterns:
        m = re.search(pat, markdown_content)
        if m:
            return m.group(1).strip()
    return ""


def extract_dependencies(markdown_content):
    deps = set()
    patterns = [
        r"npm\s+(?:install|i)\s+([\w@/.-]+)",
        r"pnpm\s+add\s+([\w@/.-]+)",
        r"from\s+['\"](@?[\w/-]+)['\"]",
    ]
    skip = {"react", "next", "next/image", "next/link", "next/font", "react-dom", "./", "../"}
    for pat in patterns:
        for m in re.findall(pat, markdown_content):
            pkg = m.strip()
            if not pkg.startswith(".") and pkg not in skip and not pkg.startswith("react"):
                deps.add(pkg)
    return sorted(deps)[:10]


def extract_code_snippet(markdown_content, slug):
    code_blocks = re.findall(r"```(?:tsx?|jsx?|css)?\n(.*?)```", markdown_content, re.DOTALL)
    if not code_blocks:
        return "// No code snippet found"

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


def extract_description(raw_text, slug, markdown_content=""):
    # Extract name from raw_text and get the description portion
    # raw_text format is usually "Component NameDescription text"
    # Try to find the name and split
    name_title = slug.replace("-", " ").title()

    # Try extracting from markdown first paragraph
    paras = re.findall(r"\n\n([A-Z][^#\n]{10,300})", markdown_content[:2000])
    if paras:
        return paras[0].strip()

    # Fall back to raw_text - try splitting after CamelCase name
    # Common pattern: "3D Card EffectA card perspective effect..."
    for i in range(len(raw_text) - 1, 0, -1):
        if raw_text[i-1].islower() and raw_text[i].isupper():
            return raw_text[i:].strip()
        if raw_text[i-1] in ".!?" and raw_text[i] == " ":
            return raw_text[i+1:].strip()

    return raw_text


ANIMATION_DESCS = {
    "3d-card-effect": "Card tilts in 3D space following mouse position with perspective transform. Inner elements float upward with varying translateZ depths on hover. Smooth spring transition on enter/exit.",
    "tooltip-card": "Floating tooltip card appears and follows cursor position on hover with spring-based animation. Card has a smooth opacity and scale transition.",
    "macbook-scroll": "Macbook mockup with content sliding out of the screen as user scrolls. Lid opens with scroll progress, revealing inner content with parallax depth.",
    "3d-pin": "3D pin rises from the surface with perspective transform on hover. Pin content appears with scale and opacity animation.",
    "animated-modal": "Modal animates in with scale and opacity transition. Background blurs with backdrop-filter. Exit animation reverses the entrance with spring physics.",
    "animated-testimonials": "Testimonial cards transition between entries with smooth fade and slide animations. Auto-plays or responds to navigation controls.",
    "animated-tooltip": "Tooltip appears on hover with spring-based scale and opacity animation. Supports multiple items with staggered entrance.",
    "apple-cards-carousel": "Cards fan out in a carousel with 3D perspective transforms. Each card can expand to full view with layout animation, similar to Apple's design pattern.",
    "aurora-background": "Soft gradient blobs shift and morph continuously creating an aurora borealis effect. Multiple color layers blend with CSS filter blur.",
    "background-beams": "Animated light beams sweep across the background. Beams follow paths with varying speeds and opacity, creating a dynamic lighting effect.",
    "background-beams-with-collision": "Light beams animate across the screen and collide/interact when meeting, creating particle effects at intersection points.",
    "background-boxes": "Grid of boxes with hover-activated color fill effects. Boxes light up as cursor moves over them, creating a trail effect.",
    "background-gradient-animation": "Gradient colors shift and blend continuously across the background with smooth color transitions and movement.",
    "background-lines": "Animated lines sweep across the background creating a dynamic linear pattern with varying opacity and speed.",
    "bento-grid": "Grid layout with hover effects on individual cells. Items can have varying sizes and animate on hover with scale and shadow transitions.",
    "canvas-reveal-effect": "Content reveals through a canvas drawing effect. Element content appears as if being drawn or painted on screen.",
    "card-hover-effect": "Card transforms on hover with 3D perspective tilt, spotlight gradient that follows cursor, and elevated shadow effect.",
    "card-spotlight-effect": "Radial spotlight gradient follows cursor position over card surface, creating a dynamic lighting effect on hover.",
    "card-stack": "Cards stack with depth offset and can be swiped/dragged to reveal cards underneath with spring physics.",
    "carousel": "Smooth sliding transitions between content panels with configurable autoplay, navigation controls, and spring-based animations.",
    "colourful-text": "Text cycles through vibrant color transitions with smooth gradient animations applied to individual characters or words.",
    "compare": "Draggable slider reveals before/after comparison of two overlapping images. Slider handle follows cursor with smooth tracking.",
    "container-scroll-animation": "Content transforms and animates within a scrollable container. Elements scale, rotate, and move based on scroll position.",
    "cool-mode": "Particle burst effect triggered on interaction. Colorful particles spray from the interaction point with physics-based movement and fade.",
    "cover": "Cover image with parallax zoom effect on hover or scroll. Image scales subtly while content overlay animates in.",
    "direction-aware-hover-effect": "Hover overlay slides in from the exact direction the cursor entered the element. Calculates entry angle for directional animation.",
    "evervault-card": "Card with animated noise/encryption pattern. Characters randomize and shift continuously, creating a matrix-like encryption visualization effect.",
    "expandable-card": "Card expands from compact preview to full detailed view with smooth layout animation. Other cards dim and shift to accommodate expansion.",
    "feature-sections-with-grid": "Feature sections with animated grid backgrounds. Grid lines pulse or highlight to draw attention to feature content.",
    "file-upload": "File upload component with drag-and-drop zone. Visual feedback on dragover with border animation and progress indication on upload.",
    "flip-words": "Words flip vertically with 3D rotation transition, cycling through a list of terms. Each word animates out and the next animates in with perspective transform.",
    "floating-dock": "Icons magnify on hover with smooth spring animation, similar to macOS dock. Adjacent icons also scale proportionally based on distance from hovered item.",
    "floating-navbar": "Navigation bar floats and transforms on scroll. Shrinks, changes background opacity, or repositions based on scroll direction and position.",
    "focus-cards": "Cards dim and blur when another card is focused/hovered. The focused card scales up slightly while siblings recede with opacity and blur transitions.",
    "following-pointer": "Element smoothly follows cursor position with spring physics and configurable lag. Creates a trailing effect with eased movement.",
    "github-globe": "Interactive 3D globe visualization rendered with WebGL/Three.js. Shows connection arcs between points with animated travel paths.",
    "glare-card": "Card with animated glare/shine effect that follows cursor position, simulating light reflection on a glossy surface.",
    "globe": "Interactive 3D globe with rotating earth visualization. Points and arcs animate on the surface with smooth orbital camera controls.",
    "glowing-effect": "Pulsing glow effect around element borders. Glow intensity and color shift continuously with CSS animation.",
    "google-gemini-effect": "Dramatic 3D particle/mesh effect that responds to scroll and mouse movement. Particles form shapes and disperse with physics-based animation.",
    "grid-and-dot-backgrounds": "Configurable grid or dot pattern backgrounds with optional radial gradient fade and hover-activated highlight effects.",
    "hero-highlight": "Hero text with animated highlight/underline effect. Highlight sweeps across text with gradient animation on load or scroll trigger.",
    "hero-parallax": "Hero section with layered parallax scrolling. Multiple image/content layers move at different speeds creating depth on scroll.",
    "hover-border-gradient": "Animated gradient travels along the button/element border on hover. Gradient rotates around the perimeter with smooth color transitions.",
    "images-slider": "Full-width image slider with smooth crossfade or slide transitions between images. Supports autoplay and gesture-based navigation.",
    "infinite-moving-cards": "Cards scroll continuously in a seamless infinite loop. Direction and speed are configurable. Duplicated items create the illusion of infinite content.",
    "lamp-effect": "Dramatic lamp/light cone effect with glow and shadow animations. Light beam expands from a point source with radial gradient and blur.",
    "layout-grid": "Responsive grid with animated card layouts. Items can be rearranged with layout animations and hover effects on individual cells.",
    "lens": "Magnifying lens effect follows cursor revealing zoomed or alternate content underneath. Lens has smooth tracking with configurable zoom level.",
    "link-preview": "Hovering over a link shows an animated preview card with the target page content. Card appears with spring-based scale and opacity transition.",
    "meteors": "Animated meteor streaks fall diagonally across the container with varying speeds, sizes, and trail effects. Continuous loop animation.",
    "moving-border": "Animated gradient border that travels along the element perimeter. Gradient rotates continuously around the border path with smooth color transitions.",
    "multi-step-loader": "Multi-step loading animation with sequential progress indicators. Steps animate in sequence with checkmarks and transitions between states.",
    "navbar-menu": "Animated navigation menu with dropdown panels. Menu items expand to show sub-content with smooth height and opacity transitions.",
    "parallax-scroll": "Content sections with parallax depth effect on scroll. Elements move at different rates creating a layered 3D scrolling experience.",
    "placeholders-and-vanish-input": "Input placeholder text cycles through suggestions and vanishes with animation when user starts typing. Smooth text transition effects.",
    "resizable-navbar": "Navigation bar that resizes and reorganizes its layout based on scroll position or viewport size with smooth dimension transitions.",
    "shooting-stars": "Animated shooting star streaks fly across the background with glowing trails. Stars appear randomly with varying trajectories and speeds.",
    "sidebar": "Collapsible sidebar navigation with smooth width transitions. Items animate in/out with staggered delays on expand/collapse.",
    "signup-form": "Sign-up form with animated input fields. Labels float on focus, validation states animate, and submit button has loading/success states.",
    "sparkles": "Small bright particles appear and fade randomly across the element. Particles have varying sizes, opacity, and animated lifetimes creating a twinkling effect.",
    "spotlight": "Radial spotlight effect follows cursor position over the element surface. Creates a dramatic lighting effect highlighting content under the cursor.",
    "stars-background": "Star field background with twinkling animation. Stars vary in size and brightness, some with subtle pulsing effects.",
    "sticky-scroll-reveal": "Content sticks while scrolling with progressive reveal of new sections. Each section animates into place as previous content scrolls away.",
    "svg-mask-effect": "SVG-based mask reveals content underneath with animated mask shape changes. Cursor position or scroll controls the mask reveal area.",
    "tabs": "Animated tab switching with active indicator that slides between tab options using layout animation. Content transitions with fade or slide.",
    "tailwindcss-buttons": "Collection of styled button variants with hover, active, and focus state animations. Includes gradient, outline, and ghost styles.",
    "text-generate-effect": "Text appears word by word or character by character with staggered opacity and slight upward movement. Creates a progressive reveal effect.",
    "text-hover-effect": "Text characters animate individually on hover with effects like bounce, color change, or displacement creating a wave-like interactive text.",
    "text-reveal-card": "Card content with text that reveals on hover or scroll with directional mask animation. Text slides in from a specific direction.",
    "timeline": "Vertical timeline with animated entry points. Items animate into view as user scrolls with staggered fade and slide transitions.",
    "tracing-beam": "A beam of light traces along a vertical path as user scrolls down the page. Beam follows scroll progress with glowing head and fading trail.",
    "typewriter-effect": "Text types out character by character with a blinking cursor. Configurable speed, with optional delete and retype animation for multiple strings.",
    "vortex": "Swirling vortex particle effect creating a tunnel or spiral animation. Particles orbit a central point with depth and perspective.",
    "wavy-background": "Background with animated wave shapes that move continuously. Multiple wave layers create depth with varying speeds and amplitudes.",
    "wavy-text": "Text characters animate with a wave-like motion. Each character moves up and down with staggered timing creating a flowing wave effect.",
    "wobble-card": "Card wobbles with slight rotation and tilt on hover interaction. Spring-based physics create a natural, playful movement.",
    "world-map": "Interactive world map with animated connection arcs between geographic points. Dots pulse at locations with arcs that animate along curved paths.",
    "shimmer-button": "Button with a shimmering light sweep effect across the surface. Gradient highlight animates from one side to the other continuously or on hover.",
}


def make_animation_description(slug, raw_text, markdown_content, category, animation_type):
    if slug in ANIMATION_DESCS:
        return ANIMATION_DESCS[slug]

    text_lower = f"{slug} {raw_text} {markdown_content[:3000]}".lower()
    desc_parts = []

    if "3d" in slug or "perspective" in text_lower:
        desc_parts.append("Element transforms in 3D space with perspective.")
    if "card" in slug and "hover" in text_lower:
        desc_parts.append("Card transforms on hover with smooth spring transitions.")
    if "parallax" in text_lower:
        desc_parts.append("Layers move at different speeds creating depth illusion on scroll.")
    if "typewriter" in text_lower:
        desc_parts.append("Text appears character by character simulating typing.")
    if "gradient" in text_lower and ("shift" in text_lower or "animate" in text_lower):
        desc_parts.append("Gradient colors shift and blend continuously.")
    if "sparkle" in text_lower:
        desc_parts.append("Small bright particles appear and fade randomly across the element.")
    if "meteor" in text_lower or "shooting" in text_lower:
        desc_parts.append("Streaks of light animate diagonally across the container.")
    if "beam" in text_lower:
        desc_parts.append("Light beam effect sweeps across the element.")
    if "aurora" in text_lower:
        desc_parts.append("Soft gradient blobs shift and morph creating an aurora borealis effect.")
    if "flip" in text_lower:
        desc_parts.append("Content flips with 3D rotation transition between states.")
    if "reveal" in text_lower or "generate" in text_lower:
        desc_parts.append("Content reveals progressively with staggered opacity and blur transitions.")
    if "moving-border" in slug:
        desc_parts.append("Animated gradient travels along the element border.")
    if "spotlight" in text_lower:
        desc_parts.append("Radial light effect follows cursor position.")
    if "wobble" in text_lower:
        desc_parts.append("Element wobbles with slight rotation on interaction.")
    if "globe" in text_lower:
        desc_parts.append("Interactive 3D globe with rotating/interactive earth visualization.")
    if "infinite" in text_lower and "moving" in text_lower:
        desc_parts.append("Items scroll continuously in a seamless loop.")
    if "expand" in text_lower:
        desc_parts.append("Element expands from compact to full view with smooth layout animation.")
    if "sticky" in text_lower and "scroll" in text_lower:
        desc_parts.append("Content sticks while scrolling with progressive reveal.")
    if "dock" in text_lower:
        desc_parts.append("Icons magnify on hover with smooth spring animation, similar to macOS dock.")
    if "lamp" in text_lower:
        desc_parts.append("Dramatic lamp/light cone effect with glow and shadow animations.")
    if "lens" in text_lower:
        desc_parts.append("Magnifying lens effect follows cursor revealing zoomed content.")
    if "compare" in text_lower:
        desc_parts.append("Draggable slider reveals before/after comparison of two images.")
    if "tooltip" in text_lower:
        desc_parts.append("Floating tooltip card appears on hover with spring animation.")
    if "modal" in text_lower:
        desc_parts.append("Modal animates in with scale/opacity transition and backdrop blur.")
    if "tabs" in text_lower:
        desc_parts.append("Active tab indicator slides between options with layout animation.")
    if "bento" in text_lower:
        desc_parts.append("Grid layout with hover effects on individual cells.")

    if desc_parts:
        return " ".join(desc_parts)

    return f"Interactive UI component with {animation_type} animation effect. Provides visual feedback and smooth transitions."


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
    }
    return use_case_map.get(category, ["General UI", "Interactive sections"])


def process_component(item, index, total):
    slug = item["slug"]
    url = item["url"]
    comp_type = item["type"]
    raw_text = item["raw_text"]

    print(f"[{index+1}/{total}] Processing: {slug} ({comp_type})", flush=True)

    # Check if already processed
    detail_file = DETAILS_DIR / f"{slug}.json"
    if detail_file.exists():
        print(f"  -> Already exists, skipping", flush=True)
        return {"slug": slug, "status": "skipped"}

    try:
        result = app.scrape(url, formats=["markdown"])

        markdown = result.markdown or ""

        if not markdown:
            print(f"  -> No markdown returned", flush=True)
            return {"slug": slug, "status": "no_markdown"}

        # Save raw markdown
        raw_file = RAW_DIR / f"{slug}.md"
        raw_file.write_text(markdown, encoding="utf-8")

        # Extract metadata
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

        # Extract name from markdown heading
        name = slug.replace("-", " ").title()
        name_match = re.search(r"#\s+(.+?)(?:\n|$)", markdown[:500])
        if name_match:
            candidate = name_match.group(1).strip()
            # Skip if it's just "Aceternity UI" or something generic
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

        detail_file.write_text(json.dumps(detail, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  -> Saved: {category} / {animation_type}", flush=True)
        return {"slug": slug, "status": "success", "category": category}

    except Exception as e:
        error_msg = str(e)
        print(f"  -> ERROR: {error_msg}", flush=True)
        traceback.print_exc()
        return {"slug": slug, "status": "error", "error": error_msg}


def main():
    with open(LIST_FILE) as f:
        components = json.load(f)

    print(f"Processing {len(components)} components...", flush=True)

    results = []
    success = 0
    errors = 0
    skipped = 0

    for i, item in enumerate(components):
        result = process_component(item, i, len(components))
        results.append(result)

        if result["status"] == "success":
            success += 1
        elif result["status"] in ("error", "no_markdown"):
            errors += 1
        elif result["status"] == "skipped":
            skipped += 1

        # Rate limiting
        if result["status"] not in ("skipped",) and i < len(components) - 1:
            time.sleep(1.5)

    # Save report
    report = {
        "total": len(components),
        "success": success,
        "errors": errors,
        "skipped": skipped,
        "results": results,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with open(REPORT_FILE, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n{'='*50}", flush=True)
    print(f"DONE: {success} success, {errors} errors, {skipped} skipped", flush=True)
    print(f"Report saved to {REPORT_FILE}", flush=True)


if __name__ == "__main__":
    main()
