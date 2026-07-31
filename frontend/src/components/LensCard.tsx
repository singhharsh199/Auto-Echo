import type { LensView, MachineIdentity } from "../data/lenses";
import { CacheStack } from "./CacheStack";

/**
 * One machine, seen through the lens currently selected.
 *
 * The card is deliberately uniform across all three lenses -- same identity
 * header, same fact list, same stack slot -- so that switching lenses reads as
 * the *same machine changing description*, not as three unrelated panels. The
 * only thing that moves is the content, which is what makes the comparison legible.
 */
export function LensCard({
  machine,
  view,
  /** Remounts the stack on lens change so its entrance animation replays. */
  animationKey,
}: {
  machine: MachineIdentity;
  view: LensView;
  animationKey: string;
}) {
  return (
    <article className="lensCard" style={{ "--machine": machine.color } as React.CSSProperties}>
      <header className="lensCard__head">
        <span className="lensCard__dot" aria-hidden="true" />
        <div>
          <h3 className="lensCard__name">{machine.name}</h3>
          <p className="lensCard__sub">{machine.sub}</p>
        </div>
      </header>

      <p className={`verdict verdict--${view.tone}`}>
        <span className="verdict__led" aria-hidden="true" />
        {view.verdict}
      </p>

      <dl className="lensFacts">
        {view.facts.map((f) => (
          <div className="lensFact" key={f.k}>
            <dt className="lensFact__k">{f.k}</dt>
            <dd className={`lensFact__v${f.flag ? ` lensFact__v--${f.flag}` : ""}`}>{f.v}</dd>
          </div>
        ))}
      </dl>

      <div className="lensCard__stack" key={animationKey}>
        <CacheStack blocks={view.stack} empty={view.stackEmpty} />
      </div>
    </article>
  );
}
