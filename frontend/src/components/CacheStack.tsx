import type { StackBlock } from "../data/lenses";

/**
 * The memory hierarchy as a proportional stack, small and fast at the top.
 *
 * Block height is proportional to `log2(capacity)`, which is the same axis the
 * main chart uses. On a linear scale a 20 MiB L3 is 400x a 48 KiB L1 and every
 * inner level collapses to a hairline; on a log scale all four tiers stay
 * legible while the ordering and the rough ratios survive. A floor of
 * `min-height` guarantees the label fits regardless of the arithmetic.
 *
 * A `ghost` block is drawn as a dashed outline rather than a filled one: it is
 * hardware that exists but which the current lens cannot see. That is the whole
 * argument of the section, so it is a visual state rather than a footnote.
 */

/** DRAM is unbounded, so it gets a fixed weight instead of a computed one. */
const DRAM_WEIGHT = 8;

function weightOf(block: StackBlock): number {
  if (block.capacityKiB == null) return DRAM_WEIGHT;
  // log2 of a sub-1 KiB capacity would go negative; nothing in this project is
  // that small, but clamping keeps a bad datum from inverting the layout.
  return Math.max(1, Math.log2(block.capacityKiB));
}

export function CacheStack({ blocks, empty }: { blocks: StackBlock[]; empty?: string }) {
  if (blocks.length === 0) {
    return (
      <div className="stack stack--empty">
        <span className="stack__void" aria-hidden="true" />
        <p className="stack__emptyText">{empty}</p>
      </div>
    );
  }

  return (
    <ol className="stack" aria-label="Memory hierarchy as reported by this lens">
      {blocks.map((b, i) => (
        <li
          key={b.label}
          className={`blk blk--${b.tone}${b.ghost ? " blk--ghost" : ""}`}
          style={{ flexGrow: weightOf(b), "--i": i } as React.CSSProperties}
        >
          <div className="blk__row">
            <span className="blk__label">{b.label}</span>
            <span className="blk__cap">{b.capacity}</span>
          </div>
          {b.note && <p className="blk__note">{b.note}</p>}
          {b.ghost && (
            <span className="blk__tag">
              <GhostIcon />
              not in the descriptor
            </span>
          )}
        </li>
      ))}
    </ol>
  );
}

/** Struck-through eye: present in silicon, absent from what the OS will tell you. */
function GhostIcon() {
  return (
    <svg viewBox="0 0 16 16" fill="none" aria-hidden="true" className="blk__icon">
      <path
        d="M1.6 8S3.9 3.9 8 3.9c1 0 1.9.24 2.7.63M14.4 8s-2.3 4.1-6.4 4.1c-1 0-1.9-.24-2.7-.63"
        stroke="currentColor"
        strokeWidth="1.3"
        strokeLinecap="round"
      />
      <circle cx="8" cy="8" r="1.9" stroke="currentColor" strokeWidth="1.3" />
      <path d="M2.5 13.5 13.5 2.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  );
}
