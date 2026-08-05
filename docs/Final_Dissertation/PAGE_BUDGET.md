# Page Budget — 12-page IEEE conference paper

Working plan for compressing `docs/Draft_Dissertation.md` (28,419 body words,
58 pages, single column) into the QMUL-required IEEEtran two-column paper.

**Requirement** (MSc Project Guide §4.3.1): two columns, **12 pages excluding
references and appendices**, IEEEtran template only. Deadline **19 Aug 2026**.

---

## Calibration — measured, not assumed

Built three IEEEtran documents from real dissertation prose and counted pages:

| Input | Output |
|:---|:---|
| 4,000 words | 4 pages |
| 8,000 words | 8 pages |
| 12,000 words | 12 pages |

**→ 1,000 words per full text page** (10pt, two-column, IEEEtran `conference`).

A single-column figure or table costs roughly **350–400 word-equivalents**
(about ⅓ column-page including caption and surrounding whitespace).

**Budget: 12,000 word-equivalents total.**

---

## The appendix lever

The page limit **excludes references and appendices**. This is the single most
important structural fact in the budget: depth that would blow the 12 pages can be
relocated rather than deleted.

The constraint is the guide's own wording — appendices hold *"detailed material that
is relevant but not crucial to the understanding of the main message"*. So an
appendix may **corroborate** a claim, but the paper must stand without it. Nothing
load-bearing moves.

---

## Allocation

| § | Section | Pages | Prose | Figs/Tables | From source | Ratio |
|:--|:--------|------:|------:|:------------|------------:|------:|
| — | Title, Abstract, Index Terms | 0.4 | 250 | — | 492 | 2.0× |
| I | Introduction | 1.1 | 900 | — | 1,355 | 1.5× |
| II | Related Work | 1.2 | 1,000 | — | 2,858 | 2.9× |
| III | Methodology | 2.6 | 1,900 | Fig. 1 | 4,611 | 2.4× |
| IV | **Evaluation** | **4.7** | **3,200** | Figs 2–4, Tables I–III | 16,669 | 5.2× |
| V | Discussion & Limitations | 1.2 | 1,000 | — | 3,513 | 3.5× |
| VI | Conclusion & Future Work | 0.8 | 650 | — | 681 | 1.0× |
| | **Total** | **12.0** | **8,900** | 4 figs + 3 tables ≈ 2,600 | **28,419** | **3.2×** |

Word-equivalents: 8,900 prose + 2,600 floats = **11,500 of 12,000** — ~4 % slack,
which IEEE papers invariably need.

Evaluation takes **39 % of the paper**, which is the correct weighting for a
results-driven contribution and matches the supervisor's instruction to make it the
strongest chapter.

---

## Figures and tables — the seven that earn their space

| Float | Content | Why it survives |
|:---|:---|:---|
| **Fig. 1** | Pipeline: probe → count → localise → validate | One diagram replaces ~600 words of methodology prose |
| **Fig. 2** | Latency curves, M1 and Intel on one log–log axis | The staircase *is* the result; nothing substitutes |
| **Fig. 3** | Intel 4 KiB vs 2 MiB huge pages | The TLB finding, shown rather than asserted |
| **Fig. 4** | Silhouette peak vs *k* | Evidence the count is chosen, not set |
| **Table I** | Three lenses × two machines | Carries the whole §1 narrative in one float |
| **Table II** | **Consolidated validation** (source Table 20) | **The single most important object in the paper** |
| **Table III** | Contention: detected L3 from quiet → loaded | The shared-cache finding, 3 rows |

Everything else — 8 figures, 21 tables — goes to appendix or is cut.

---

## What moves to appendices (free pages)

| Source | Words | Destination |
|:---|---:|:---|
| §5.3.1 lmbench external cross-check | 2,053 | **App. B** — corroboration; paper keeps a 3-sentence summary |
| §5.4 estimator comparison (Table 21) | ~1,200 | **App. C** — supports "edge over onset" choice made in §III |
| §5.4 sampling-density robustness (Table 20) | ~900 | **App. C** |
| §3.2.1 full DP derivation and optimality audit | 1,533 | **App. A** — paper states the lemma + cites Fisher / Wang & Song |
| §5.1 ground-truth provenance detail | ~1,800 | **App. D** — paper keeps Table I only |
| Appendix A (Generative-AI statement) | 662 | **App. E** — required document, likely submitted separately |

Roughly **8,150 words** relocated rather than lost.

---

## What is cut outright

| Source | Words | Rationale |
|:---|---:|:---|
| Acknowledgements | 233 | Not part of a conference paper |
| §2.1 Memory echolocation | 212 | Folded into Related Work opening |
| §2.3 side-channel lineage | 869 → 150 | Compress to 3 sentences + citations; the "why not eviction sets" point survives |
| §3.4 hyperparameter table narrative | 687 → 120 | One sentence + a footnote |
| §5.3.2 methodological asides | ~600 | Keep the finding, drop the process narrative |
| Repeated provenance restatements across §5 | ~1,500 | Say each thing once |

---

## Per-section compression notes

**I. Introduction (900 words).** Lead with the Three Lenses. The two failure modes
are the whole motivation and must both appear: the M1's *incomplete* table and the
Intel's *complete-but-not-behavioural* one. Close with a numbered contributions list
— IEEE readers expect it and it costs ~80 words.

**II. Related Work (1,000 words).** Four short paragraphs: classical user-space
characterisation (lmbench, Yotov); side channels (one paragraph, ending on why
eviction-set precision is unavailable without target knowledge); topology tools
(hwloc, CPUID, MLC) and their shared dependence on a pre-written table;
unsupervised model selection. The novelty claim — *the inference layer, not the
measurement* — belongs at the end of this section.

**III. Methodology (1,900 words + Fig. 1).** Probe design: pointer chase, MLP = 1 by
construction, no fences needed, batch-amortised timing, runtime calibration. Then
count-then-localise: exact 1-D *k*-means via DP (state the contiguity lemma, cite,
defer the derivation), Silhouette for *k*, penalty-free `Dynp` for boundaries. The
baseline failure (§4, 894 words) compresses to **one paragraph** as design
motivation — it justifies the write-before-read constraint and earns its place.

**IV. Evaluation (3,200 words + 3 figs + 3 tables).** The star. Order:
1. Machines and ground-truth provenance — Table I, ~400 words
2. Both machines' results against Fig. 2 — ~700 words
3. **Table II, consolidated validation** — ~500 words. Five caches, five matches,
   two ISAs; hwloc verifies the reference standard; the SLC row is *not scorable*
   and is the row that justifies the method
4. The TLB finding with Fig. 3 — ~700 words. The controlled intervention
5. Contention with Table III — ~500 words. Capacity is a property of the running
   system, not the die
6. Robustness in brief — ~400 words, pointing at App. C

**V. Discussion & Limitations (1,000 words).** n = 2 machines of the same class;
no inferential statistics; huge-page dependence; soft-knee bias one-signed upward;
the macOS pinning caveat. State them plainly — this is where honesty scores.

**VI. Conclusion & Future Work (650 words).** Close the three-lens argument. Future
work names the AMD Zen experiment with its falsifiable per-CCX prediction — knowing
precisely what the next experiment is, and why, is what this section rewards.

---

## Build blockers to fix before drafting

1. **`pdflatex` silently drops `✓ ✗ − ≈`.** Verified: a torture-test document
   compiled with **zero errors** and the glyphs are simply absent from the output.
   Table II uses ✓ marks throughout. Fix by using `\checkmark` (amssymb),
   `$\times$`, `$-$`, `$\approx$` — *not* raw Unicode. Do not switch to XeLaTeX;
   IEEE expects pdflatex.
2. **The skeleton is still the unmodified IEEE demo.** `Final_Dissertation.tex` is
   byte-identical to `conference_101719.tex`.
3. **`scripts/build_final_pdf.sh` has no BibTeX pass** and does not report the page
   count — the one number that matters most here.
