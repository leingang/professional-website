#!/bin/sh
# Turn a beamer .tex file into an animated GIF of its slides (one per overlay).
#
#     tools/beamer2gif.sh path/to/overlays.tex [seconds-per-frame]
#
# Compiles with LuaLaTeX (latexmk), renders each page at 200 dpi, drops the
# beamer navigation-symbol strip, crops every frame to the same box (so any
# movement between slides stays visible), and writes path/to/overlays.gif.
# Default: 1 second per frame, looping forever.
# Needs latexmk, pdftoppm (poppler), and ImageMagick 7 (magick).
set -eu

tex=${1:?usage: tools/beamer2gif.sh file.tex [seconds-per-frame]}
secs=${2:-1}
dir=$(cd "$(dirname "$tex")" && pwd)
base=$(basename "$tex" .tex)
delay=$(awk "BEGIN { printf \"%d\", $secs * 100 }")   # GIF delays are in 1/100 s

(cd "$dir" && latexmk -lualatex -interaction=nonstopmode -file-line-error "$base.tex" >/dev/null) || {
  echo "LaTeX failed; see $dir/$base.log" >&2; exit 1; }

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
pdftoppm -r 200 -png "$dir/$base.pdf" "$tmp/f"
for f in "$tmp"/f-*.png; do
  magick "$f" -gravity south -chop 0x60 "$tmp/c-${f##*/f-}"   # strip navigation symbols
done
box=$(magick "$tmp"/c-*.png -evaluate-sequence min -trim -format '%wx%h%X%Y' info:)
# -delay must come before the frames are read, or it isn't applied to them
magick -delay "$delay" "$tmp"/c-*.png -crop "$box" +repage \
  -bordercolor white -border 24 -loop 0 -layers Optimize "$dir/$base.gif"

n=$(magick identify "$dir/$base.gif" | wc -l | tr -d ' ')
echo "wrote $dir/$base.gif ($n frames, ${secs}s each)"
