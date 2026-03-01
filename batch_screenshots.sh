#!/bin/bash
cd ~/repos/design-catalog
source ~/.profile

# Load component list to build URL map
python3 -c "
import json
cl = json.load(open('components/component-list.json'))
for c in cl:
    print(f\"{c['slug']}|{c['url']}\")
" > /tmp/slug_urls.txt

SLUGS=(
    navbars noise-background parallax-scroll pixelated-canvas
    placeholders-and-vanish-input pointer-highlight
    shooting-stars-and-stars-background sidebar sidebars
    signup-form sparkles spotlight spotlight-new
    stateful-button stats-sections sticky-banner
    sticky-scroll-reveal svg-mask-effect tabs
    tailwindcss-buttons testimonials text-animations
    text-generate-effect text-hover-effect text-reveal-card
    timeline tooltip-card tracing-beam typewriter-effect
    vortex wavy-background webcam-pixel-grid wobble-card world-map
)

SUCCESS=0
FAILED=0
SKIPPED=0
FAILURES=""
TOTAL=${#SLUGS[@]}
IDX=0

for slug in "${SLUGS[@]}"; do
    IDX=$((IDX + 1))
    OUT="components/previews/${slug}.png"
    
    if [ -f "$OUT" ]; then
        echo "[$IDX/$TOTAL] $slug - skipped (exists)"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi
    
    # Get URL from lookup
    URL=$(grep "^${slug}|" /tmp/slug_urls.txt | cut -d'|' -f2)
    if [ -z "$URL" ]; then
        URL="https://ui.aceternity.com/components/${slug}"
    fi
    
    echo -n "[$IDX/$TOTAL] $slug... "
    
    # Run as subprocess with timeout
    timeout 45 python3 single_screenshot.py "$slug" "$URL" "$OUT" 2>/dev/null
    EXIT=$?
    
    if [ $EXIT -eq 0 ] && [ -f "$OUT" ]; then
        echo "OK"
        SUCCESS=$((SUCCESS + 1))
    else
        echo "FAIL (exit=$EXIT)"
        FAILED=$((FAILED + 1))
        FAILURES="$FAILURES $slug"
    fi
    
    sleep 2
done

echo ""
echo "Done: $SUCCESS OK, $SKIPPED skipped, $FAILED failed"
if [ -n "$FAILURES" ]; then
    echo "Failures:$FAILURES"
fi
