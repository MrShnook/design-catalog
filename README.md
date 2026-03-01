# Design Catalog 🎨

Curated design resource catalog for AI-powered design workflows.

## What Is This?

A structured, agent-readable catalog of design resources — fonts, components, color palettes — scraped from the best free design resource sites. Built for AI agents that need to make informed design decisions without browsing.

## Structure

```
fonts/
├── catalog.md              # Master list — agent reads this first
├── details/                # One markdown file per font with full metadata
│   ├── satoshi.md
│   ├── general-sans.md
│   └── ...
└── specimens/              # Screenshot of each font's specimen
    ├── satoshi.png
    ├── general-sans.png
    └── ...

components/                 # Future: Aceternity UI, Shadcn, Magic UI
├── catalog.md
├── details/
└── previews/

scripts/                    # Scraper and refresh scripts
```

## Usage

1. Agent reads `fonts/catalog.md` for the master list (fast, cheap)
2. Filters to candidates based on brief/vibe
3. Reads individual detail files for shortlisted fonts
4. Optionally reviews specimen images for visual confirmation
5. Returns recommendation with import/usage code

## Sources

| Source | Type | Status |
|--------|------|--------|
| [FontShare](https://fontshare.com) | Fonts (100) | ✅ Cataloged |
| [Aceternity UI](https://ui.aceternity.com) | Components | 📋 Planned |
| More TBD | | |

## Refresh

Catalog is refreshed monthly via scraper scripts in `scripts/`.

---

*Part of the [Shnook Ventures](https://github.com/MrShnook) ecosystem.*
