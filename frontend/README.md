# Auto-Echo dashboard

Interactive front end for the memory-hierarchy latency metrics produced by
`python -m autoecho`. It reads the pipeline's own outputs — it does not
re-measure anything, and it never hard-codes a result.

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

## Where the numbers come from

`scripts/build-data.mjs` reads, for each machine, from `../data/<dir>/`:

| File | Used for |
|---|---|
| `wss_curve.csv` | the reported curve (minimum over repeats) |
| `wss_curves_all.csv` | per-sweep traces and the min–max envelope |
| `validation_report.md` | levels, capacities, ground truth, estimator tables |

It emits `src/data/dataset.json`, which the app imports directly — so there is no
runtime CSV or Markdown parsing, and the build fails loudly if a report changes
shape. `predev` and `prebuild` run it automatically; run `npm run prep` by hand
after a new sweep.

`src/data/dataset.json` is generated and therefore gitignored.

## Adding a machine

Append one entry to `MACHINES` in `scripts/build-data.mjs` and re-run `npm run prep`.
Nothing else needs to change — the machine switcher, cards, chart and tables are
all driven off that list:

```js
{ id: "zen4", dir: "amd_zen4", name: "AMD Ryzen 7 7700X", arch: "x86-64",
  core: "Zen 4", lineSize: "64 B", color: "#CC79A7", status: "validated" },
```

Every field must come from that machine's own `validation_report.md` — `core` and
`lineSize` are reported in §5.1 of the dissertation and must not be guessed. The
on-screen series colour is assigned by `src/lib/series.ts`, so `color` here is only
a fallback for a machine that has no token yet.

## What the dashboard shows

- **Level cards** — inferred capacity, median and p5–p95 latency per discovered
  level, joined to the OS ground truth with the signed capacity error.
- **Memory mountain** — pointer-chase latency against working-set size on log–log
  axes, with the detected cache regions shaded, the inferred capacities marked,
  and the min–max spread across sweeps as a band. Individual sweeps can be
  overlaid to inspect run-to-run variance.
- **Overlay all** — every measured machine's curve on one axis, the interactive
  form of Fig. 10 in the dissertation.
- **Validation** — recall, precision, F1 and mean absolute capacity error, plus
  the per-cache ground-truth table.
- **Level-count estimators** — each independent counter's mean, standard
  deviation and modal count, plus change-point penalty sensitivity.

The view is deep-linkable: `?machine=intel`, `?machine=intel&compare=1`.

## Design notes

Series colours are the project's own Okabe–Ito palette from `compare_curves.py`
(M1 `#0072B2`, Intel `#D55E00`), so the dashboard and the dissertation figures
read as one system. Cache-band tints mirror the shaded regions in
`memory_mountain.png`. Both light and dark themes follow the viewer's OS setting.

## Stack

Vite · React · TypeScript · Recharts · Tailwind CSS v4.
