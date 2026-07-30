#!/usr/bin/env bash
# Build docs/Draft_Dissertation.pdf from the Markdown source.
#
# Requires pandoc and a XeLaTeX installation (TeX Live "basic" scheme suffices;
# docs/pandoc-header.tex deliberately avoids packages outside it).
#
# Two details matter and are easy to get wrong:
#
#   * pandoc must run from docs/, because the figures are referenced as
#     ../data/*.png relative to the Markdown file. Invoking it from the repository
#     root makes those paths resolve outside the repository and the build fails.
#
#   * the input format must be `markdown`, NOT `gfm`. Pandoc's gfm reader discards
#     pipe-table column widths, emitting width-less `l`/`c` columns whose cells
#     cannot wrap; the wide evaluation tables then overflow the margin by up to
#     170pt. The `markdown` reader assigns proportional p{} widths from the
#     separator rows, which is why several tables carry deliberately widened
#     separators. `markdown` is pandoc's default for .md, so simply not passing
#     --from is correct; it is named explicitly here to document the requirement.
#
# Usage:  ./scripts/build_pdf.sh
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$PWD"

cd docs
pandoc Draft_Dissertation.md \
  --from=markdown+tex_math_dollars \
  --output=Draft_Dissertation.pdf \
  --pdf-engine=xelatex \
  --include-in-header=pandoc-header.tex \
  --toc --toc-depth=3 \
  -V geometry:a4paper -V geometry:margin=1in \
  -V fontsize=11pt \
  -V colorlinks=true -V linkcolor=blue -V urlcolor=blue -V toccolor=black \
  --metadata title="Auto-Echo: Automated Discovery of Memory Hierarchy Latency Patterns from User-Space" \
  --metadata author="Harsh Raj Singh · MSc Advanced Computer Science · Queen Mary University of London" \
  --metadata date="July 2026"

echo "built docs/Draft_Dissertation.pdf"

# Keep the copy at the repository root in step; it is the tracked artefact.
cp Draft_Dissertation.pdf "$ROOT/Draft_Dissertation.pdf"
echo "copied to Draft_Dissertation.pdf (repository root)"
