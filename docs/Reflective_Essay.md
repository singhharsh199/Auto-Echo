# MSc Project — Reflective Essay

> **Formatting note (not part of the submission).** The QM+ template
> (`docs/Reflective Essay Template.dotx`) supplies the header block below and the
> required formatting: **Arial 11, single line spacing, single column, 5 pages max
> excluding references**. Paste the body of this document into that template
> rather than reformatting this file. At Arial 11 single-spaced, five A4 pages is
> roughly 3,000 words; the body below is ~2,800, leaving room for the header.
>
> Fields marked `[…]` need completing before submission.

**Project Title:** Auto-Echo: Automated Discovery of Cache-Hierarchy Structure from User-Space Latency Alone

**Student Name:** Harsh Raj Singh

**Student Number:** […]

**Supervisor Name:** […]

**Programme of Study:** MSc Advanced Computer Science

---

## 1. Introduction

Auto-Echo asks whether a program can discover its machine's cache hierarchy — how
many levels it has and how large each is — from timing alone, with no privileges
and no vendor tables. The research paper reports what the framework achieves and
what bounds it. This essay reports what the process taught me, which is a
different and in places less flattering account.

## 2. Strengths and weaknesses

### What worked

The strongest aspect of the project is that its central claims are **falsifiable
and were actually tested**, rather than argued. The clearest example is the
finding that page size, not cache size, decides whether a last-level cache is
visible. I did not infer that from the shape of a curve. I formed the hypothesis
that translation cost was masking the Intel L3, predicted that enlarging the page
would make the artefact disappear and the real cache appear, and ran the
experiment. The artefact vanished and the L3 resolved to within 1.5% of its
documented capacity. That is a controlled intervention, and it is worth more than
any amount of plausible reasoning about the same data.

The second strength is the decision to make the inference stage **exact rather
than merely convergent**. Replacing Lloyd's heuristic with an exact
one-dimensional dynamic program was, in terms of the numbers reported, worth
nothing: both reach the same level count on both machines. I chose to say so in
the paper rather than present the migration as an accuracy improvement, because
claiming otherwise would have been checkable and false. What it genuinely bought
was determinism and a guarantee that generalises beyond the two curves I happened
to measure — and being able to distinguish those two things clearly is something
I understood better at the end of the project than at the start.

### What did not

The most serious weakness is the **evidence base**: two machines, both consumer
laptop performance cores. I spent considerable effort trying to arrange access to
an AMD Zen part precisely because it would test the sharing behaviour that my
contention experiment isolates, and I was unable to obtain one. On my
supervisor's advice I stopped pursuing it and concentrated on strengthening the
evaluation of what I already had. I think that was the right call under time
pressure, but it leaves a genuine limitation rather than a resolved one, and the
paper states it as such.

The second weakness is one I created and then had to correct. For much of the
project I detected cache boundaries on the *aggregate* latency curve, which is
the minimum over repeated sweeps at each working-set size. The minimum is the
correct statistic for a latency, because interference can only add time. It is
the **wrong statistic for a boundary**, because in a noisy transition region a
lower envelope systematically drags the apparent end of a plateau inward. This
was not a small effect: it placed the Intel L3 at 13.9 MiB, a 30% under-read,
when nine of ten individual sweeps put it at 19.7 MiB — within 1.5% of nominal.
I found it only because I checked why one reported number disagreed with the
per-sweep spread. Had I not, I would have published a substantially wrong
headline result with no internal inconsistency to betray it.

I have thought about why I made that error, because the lesson generalises. I
had reasoned correctly about the statistic for one purpose and then reused it for
a different purpose without re-deriving whether the justification still applied.
The argument "interference can only add time" is about magnitudes; it says
nothing about locations. That is the kind of mistake that survives code review,
because the code is doing exactly what it was written to do.

A third weakness is narrower but worth recording. The framework reports the
Apple M1's L2 and its System-Level Cache as a single band and cannot separate
them. This is an honest limit of a one-dimensional latency sweep — two adjacent
tiers with similar latencies merge — and no amount of better inference recovers
information the measurement did not capture.

## 3. Theory and practice: where they diverged

The most instructive gap between theory and practice was **the failure that
started the project**. My first implementation followed the reference technique:
flush a cache line, write it, time the read back. It failed on Apple Silicon, and
my immediate explanation was architectural — ARM gives user space no cache-flush
instruction, so of course a flush-based method fails.

That explanation was wrong, and I only discovered it because I tested it. I ran
the same baseline on an x86 machine *with* a working `clflush` and a proper
`rdtscp` timer. It failed there too, reporting a mean "L1" latency of 178 ns
against that core's true 1.6 ns. The real fault was structural: writing a line
immediately before timing its read pulls that line into L1, so every measurement
was an L1 hit by construction and the flush accomplished nothing. Refuting my own
first hypothesis was the single most valuable half-day of the project, because
had I accepted it I would have spent weeks writing per-architecture flush code
for a design that could never have worked.

A second divergence concerns what theory says a measurement *is*. Textbook
treatments describe cache capacity as a fixed property of the die, and for
private caches that is roughly what I measured. For the *shared* L3 it is simply
not true. Under an eight-core streaming load the same silicon yielded a detected
L3 of 3.5 MiB instead of 19.7 MiB — a five-fold difference with no
within-condition spread. What a single core recovers of a shared cache is not the
cache's capacity but the share the rest of the system has left it. This changed
how I think about the whole exercise: the number is a property of the running
system, not of the hardware, and reporting it without its load condition would be
meaningless.

A third, smaller divergence taught me something about the tools themselves. I
assumed a compiler would faithfully execute a timed loop. It will not, if the
loop has no observable effect. A single misplaced `volatile` — writing
`volatile void *` where `void *volatile` was required — lets an optimiser delete
the entire measured loop and report physically impossible latencies near zero.
The output looks clean. Nothing crashes. I now treat any measurement that returns
a suspiciously good number as a bug report until proven otherwise.

## 4. Legal, social, ethical and sustainability issues

### Legal

The framework operates entirely within its own address space, requires no
elevated privileges, and reads no data belonging to any other process, so its
normal operation raises no question under the Computer Misuse Act 1990. Two
narrower points required attention. First, the Intel measurements were taken on
a machine belonging to someone else; I obtained the owner's explicit permission
both to run the experiments and to enable the privilege required for large-page
allocation, and I record that in the paper's acknowledgements rather than leaving
it implicit. Second, the external cross-check used lmbench, which is GPL-licensed.
I ran it as a separate program and reported its output; I did not link against it
or incorporate its code, so no derivative-work obligation arises. The project's
own dependencies (NumPy, scikit-learn, ruptures) are permissively licensed.

### Ethical

This is the area that most repays honest reflection, because the project sits
closer to offensive security than its framing suggests. The measurement primitive
— timing memory access to infer the state of the memory hierarchy — is the same
primitive underlying cache side-channel attacks, and my own related-work section
cites Prime+Probe, Flush+Reload and, on the very hardware I measured, the Augury
and GoFetch prefetcher attacks.

The defensible distinction is that Auto-Echo characterises *its own* machine
using *its own* memory, and never observes another process. But I do not think
that distinction is as comfortable as it first appears. Constructing eviction
sets — the reconnaissance step of a serious cache attack — begins with exactly
the kind of hardware characterisation this tool automates, and I have made that
characterisation portable, unprivileged and robust on hardware the vendor has not
documented. Publishing it lowers the cost of that reconnaissance step.

Two considerations lead me to think publication is nonetheless justified. The
information recovered is, for the overwhelming majority of hardware, already
public: vendor datasheets and `hwloc` report it more precisely than I can. The
genuinely novel capability applies to *undocumented* hardware — which is also
precisely where the defensive and performance value lies, since it is where no
alternative exists. And the tool recovers capacities and level counts, not the
associativity and set structure an attacker actually needs; the paper says
explicitly that eviction-set construction is the better instrument for that, and
does not attempt it. I would not, however, describe the work as free of dual-use
concern, and I think a reflective account that claimed otherwise would be
dishonest.

A second ethical dimension is academic. I used generative AI during this project,
and the accompanying statement records where and how. Two specific risks required
active management rather than declaration alone: the tendency of such tools to
produce plausible but fabricated citations, and the temptation to accept a
generated explanation without verifying it against the code or data. Every result
reported in the paper came from an execution I ran.

### Social

The clearest social argument for the work is that it removes a dependency. Every
existing route to cache-hierarchy information requires something granted by
someone else — a vendor's documentation, an operating system's descriptors,
administrative privilege, or an architecture-specific instruction. A measurement
that requires none of these is available to a developer with an unfamiliar
machine, a researcher characterising hardware nobody has documented, and anyone
outside the set of people with vendor relationships or specialist tooling.

There is a counterweight that I do not think the project can dismiss. A robust,
unprivileged method of determining a machine's cache geometry is also a **device
fingerprinting** vector. Cache-hierarchy structure is reasonably discriminating
between machine models, does not change over a device's lifetime, and — unlike
most fingerprinting signals — cannot be cleared, spoofed by the user, or
withheld by a privacy setting. I did not build a fingerprinting tool and the
latency sweep is far too slow to run covertly in a web page, but the technique
generalises in that direction, and honesty requires acknowledging it.

### Sustainability

The project's direct environmental cost is negligible: a full sweep is minutes of
single-core CPU time, with no model training, no GPU and no cluster. The
indirect argument is more interesting and, I think, more substantial. A DRAM
access costs on the order of a hundred times the energy of an L1 hit, so software
that maps its working set onto the cache hierarchy correctly does less DRAM
traffic and consumes measurably less energy for the same work. Tools that make
cache structure discoverable therefore have a real, if indirect, efficiency
benefit — and the benefit is largest exactly where documentation is absent, which
is the case this project addresses.

A second sustainability argument concerns hardware lifespan. Machines outlive
their vendors' documentation. A characterisation method that needs no vendor
cooperation helps keep older or undocumented hardware usable and tunable, which
is a small contribution to extending device lifetimes rather than replacing them.
I want to be careful not to overstate either argument: neither effect is measured
in this work, and both are offered as reasoning rather than as findings.

## 5. Further work

Three extensions follow directly from the results, in descending order of value.

An **AMD Zen** measurement is the most discriminating next experiment, and the
one I most regret being unable to run. Intel's last-level cache is shared across
all cores over a ring interconnect, which is why eight streaming workers drove my
recovered capacity down five-fold. Zen's L3 is instead a victim cache private to
each core complex. That yields a falsifiable prediction: workers pinned to the
probe's own complex should reproduce the under-read, while workers on a different
complex should leave its slice largely intact. Confirming it would establish that
the experiment measures cache *sharing* rather than general system load; failing
to confirm it would bound the finding to ring-based caches. Either result is
informative, which is what makes it worth running.

A **page-size control on Apple Silicon** would resolve the one confound I could
not eliminate. The M1 uses 16 KiB base pages against the Intel's 4 KiB, so for
any working set it faces a quarter of the translation pressure, and I therefore
cannot attribute the M1's cleaner deep curve to its architecture rather than its
page size. macOS on ARM64 rejects the superpage flags that would allow the
comparison, so this is blocked by the platform rather than by effort.

**Direct instrumentation** would confirm two mechanisms I can currently only
infer. Performance counters exposing DTLB-miss and page-walk-cycle events would
verify the translation explanation independently of the page-size manipulation,
and the `APERF`/`MPERF` register pair would settle whether the uniform 2.2×
slowdown I observed under load is entirely a core-frequency effect — my own data
cannot, because the invariant timer that makes the measurement trustworthy is by
construction blind to core frequency.

## 6. What I would have done with more time

I would have **broadened the hardware base before deepening the analysis**. In
hindsight I invested heavily in refining the inference stage — exact clustering,
estimator comparisons, sampling-density robustness — while the evaluation rested
on two machines of the same class. A third machine of a genuinely different
character would have strengthened the central claim more than any of that
refinement did. I understood this late, and by then the hardware was not
available.

I would also have **retained raw data more systematically**. The 4 KiB-page Intel
run demonstrates the project's sharpest finding, but I recorded its outputs
without keeping the underlying curve, and the machine was borrowed and is no
longer accessible. The finding is reported as measured and flagged as not
independently re-derivable, which is the honest treatment, but it should not have
been necessary. A discipline of committing raw measurements at the moment they
are taken, rather than the artefacts derived from them, would have cost nothing
at the time.

Finally, I would have built the **dispersion self-diagnostic** the contention
experiment exposed the need for. I ran what I intended as a quiet control and
only established afterwards, from the spread of its own measurements, that
something had been competing with the probe throughout. The framework had all the
information needed to detect that at the time and did not report it. A check that
flags anomalous within-run dispersion would have turned a retrospective
correction into a warning at the point of measurement, and it is a small piece of
engineering with a disproportionate effect on trustworthiness.
