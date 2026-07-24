# Prompt for Claude — close the M1 ↔ Intel presentation asymmetry (dissertation parity)

> **How to use:** run in the Auto-Echo repo root (any machine — this is dissertation-only,
> no hardware needed; the figure and data already exist in the repo). Paste everything from
> `─── PROMPT ───` down.

---

─── PROMPT ───

You are editing the **Auto-Echo** MSc dissertation (`docs/Draft_Dissertation.md`) to make the
two real test machines — **Apple M1** (§6.2) and **Intel i5-13450HX** (§6.3) — symmetric in
presentation **only where the asymmetry is an oversight**, and to leave untouched every
asymmetry that reflects a real scientific difference.

## The gap (from a parity audit)

The two machines are already treated identically for build/tests, per-core ground truth, the
memory-mountain figure (Fig. 5 vs Fig. 8), and the hierarchy / estimator-comparison /
penalty-sensitivity tables (Tables 1, 3, 4 vs 5, 6, 7). **The one unjustified gap is the
model-selection (Elbow-vs-Silhouette) result:**

- The **M1** has **both** a figure (**Fig. 6**) and a table (**Table 2**, "Elbow and
  Silhouette agree", both → k = 3).
- The **Intel** has **neither** — even though `data/intel_i5_13450hx/model_selection.png`
  already exists and shows the *more informative* result: **Elbow k = 2 vs Silhouette k = 4
  (they DISAGREE)**, which is the visual evidence for the "unstable x86 level count" finding
  and, therefore, why the Intel is "measured" not "validated".

## ⚠️ INTEGRITY RULE — do NOT equalise these (they are correct as-is)

Leave every **scientific** asymmetry exactly as it is — forcing them to match would be
dishonest:
- §6.2 heading "— validated" vs §6.3 heading "— measured";
- M1 recall & precision **100%** vs Intel **66.7%**;
- M1 count unanimous (std 0) vs Intel unstable (2–5);
- the `clflush` naive baseline (x86-only) and the huge-page control (x86-only).

Your job is **presentation parity for the model-selection result ONLY.** Do not touch results,
statuses, or numbers anywhere else.

## Tasks

1. **Embed the Intel model-selection figure** in §6.3, in the position that mirrors where §6.2
   places Fig. 6 (right after the Intel model-selection / estimator discussion). Source file:
   `data/intel_i5_13450hx/model_selection.png`. Write a caption that emphasises that here the
   Elbow (**k = 2**) and Silhouette (**k = 4**) **disagree** — the direct visual evidence for
   the unstable x86 level count, in deliberate contrast to the M1's agreement in Fig. 6.

2. **Add an Intel model-selection table** mirroring the M1's **Table 2** (read Table 2 first
   and match its structure/columns), placed in the matching position in §6.3. Values from the
   committed `data/intel_i5_13450hx/validation_report.md`, Section 2: Change-point cost-knee
   **2**, K-Means + Silhouette **4** (score 0.885), K-Means + Elbow **2**, GMM + Silhouette
   **5** (0.842), DBSCAN **4**. Title it to mirror Table 2 but state that the estimators
   **disagree** (vs the M1's agreement).

3. **Renumber consistently.** Inserting a figure and a table shifts later numbers. After
   inserting, renumber every subsequent **`Fig. N`** and **`Table N`** (e.g. the cross-machine
   overlay Fig. 9 → Fig. 10; the Apple M5 placeholder Table 8 → the next number), then
   **`grep -nE "Fig\. [0-9]|Table [0-9]" docs/Draft_Dissertation.md`** and fix **every**
   in-text reference. Leave no dangling, duplicated, or out-of-order number.

4. **(Recommended) Add a one-line convention note** to §6.1 explaining the
   **validated / measured / to-be-measured** status vocabulary, so a reader sees the remaining
   M1 ↔ Intel differences are deliberate, not omissions.

5. **Rebuild the PDF and verify.** The source uses two glyphs (`→`, `≈`) the serif math font
   lacks, so build from a temp copy that renders them as math:
   ```
   python3 - <<'PY'
   import re
   s = open("docs/Draft_Dissertation.md", encoding="utf-8").read()
   s = s.replace("→", r"$\rightarrow$").replace("≈", r"$\approx$")
   s = re.sub(r"(\$\\(?:rightarrow|approx)\$)(\d)", r"\1 \2", s)
   open("/tmp/diss_build.md","w",encoding="utf-8").write(s)
   PY
   pandoc /tmp/diss_build.md -o Draft_Dissertation.pdf --pdf-engine=xelatex \
     --toc --toc-depth=3 --resource-path=docs -V geometry:margin=1in -V fontsize=11pt \
     -V mainfont="STIX Two Text" -V monofont="Menlo" \
     -V colorlinks=true -V linkcolor=RoyalBlue -V urlcolor=RoyalBlue
   ```
   (On Windows use `-V mainfont="Cambria"` instead of STIX/Menlo.) Confirm the build is clean
   (no "Missing character" / image-not-found warnings) and open the PDF to check the new figure
   and table render.

6. **Commit** the dissertation source + rebuilt PDF.

## Acceptance
- §6.3 now has an embedded Intel model-selection **figure AND table**, symmetric with §6.2's
  Fig. 6 + Table 2.
- All `Fig.`/`Table` numbers are sequential and **every** reference resolves (grep-verified).
- **No scientific asymmetry changed** — verify §6.3 heading is still "measured", Intel recall
  still 66.7%, count still "unstable", etc.
- PDF rebuilds clean.

─── END PROMPT ───
