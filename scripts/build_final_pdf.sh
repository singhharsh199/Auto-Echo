#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Build the final IEEEtran research paper and report the one number that
# decides whether it is submittable: the page count against the 12-page limit
# (MSc Project Guide Sec. 4.3.1, excluding references and appendices).
#
# pdflatex, not xelatex: IEEE expects it, and the Unicode glyphs xelatex would
# buy us are handled by \cmark / \xmark macros instead. See the header comment
# in Final_Dissertation.tex for why that matters -- pdflatex drops those glyphs
# SILENTLY, so a clean build is not evidence the output is correct.
#
# No BibTeX pass: the bibliography is hand-written as \bibitem entries so the
# Harvard house style of Guide Sec. 8.2 can be matched exactly.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIR="$ROOT/docs/Final_Dissertation"
JOB="Final_Dissertation"

cd "$DIR" || { echo "cannot cd to $DIR"; exit 1; }

# Two passes resolve \label/\ref and natbib's author-year citations.
for pass in 1 2; do
  if ! pdflatex -interaction=nonstopmode -halt-on-error "$JOB.tex" >/dev/null 2>&1; then
    echo "BUILD FAILED on pass $pass -- last errors:"
    grep -m 10 -A 2 "^!" "$JOB.log" 2>/dev/null || tail -25 "$JOB.log"
    exit 1
  fi
done

pages=$(grep -oE "Output written on $JOB\.pdf \([0-9]+ page" "$JOB.log" | grep -oE "[0-9]+")
undef=$(grep -c "LaTeX Warning: Citation" "$JOB.log" 2>/dev/null || true)
unref=$(grep -c "LaTeX Warning: Reference" "$JOB.log" 2>/dev/null || true)
overfull=$(grep -c "Overfull .hbox" "$JOB.log" 2>/dev/null || true)

echo "built $DIR/$JOB.pdf"
echo
printf '  %-26s %s\n' "pages"                "${pages:-?}"
printf '  %-26s %s\n' "undefined citations"  "${undef:-0}"
printf '  %-26s %s\n' "undefined references" "${unref:-0}"
printf '  %-26s %s\n' "overfull hboxes"      "${overfull:-0}"
echo

# The limit excludes references and appendices, so the body page count is what
# is actually constrained. Report the total; where the body ends is a judgement
# the author makes when the paper is complete.
LIMIT=12
if [ -n "${pages:-}" ]; then
  if [ "$pages" -le "$LIMIT" ]; then
    echo "  Within ${LIMIT} pages even counting references and appendices."
  else
    echo "  NOTE: ${pages} total pages. The ${LIMIT}-page limit EXCLUDES references"
    echo "        and appendices -- check where the body ends before assuming overrun."
  fi
fi
