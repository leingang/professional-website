#!/bin/sh
# Render card.html to site/images/social-card.png (1200x627) with headless Chrome.
set -e
here="$(cd "$(dirname "$0")" && pwd)"
out="$here/../../site/images/social-card.png"
chrome="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
"$chrome" --headless=new --disable-gpu --hide-scrollbars \
  --allow-file-access-from-files --virtual-time-budget=5000 \
  --window-size=1200,627 --screenshot="$out" "file://$here/card.html" 2>/dev/null
echo "Wrote $out"
