# Auto-Echo — Viva Preparation Pack

Three parts, in order of urgency:

- **Part 1 — The 20-Minute Opening.** The complete script to deliver when the
  examiner says "introduce your project", with delivery cues, a cheat card of every
  number, and 35 anticipated questions with answers.
- **Part 2 — Tutoring Session Log.** Concepts worked through on the Novice →
  Intermediate → Expert ladder, with questions asked, answers given, and
  verification.
- **Part 3 — Question Bank.** 67 standalone viva questions across five modules.

> **Note.** Three questions in Part 3 (1.5, 2.1, 3.9) deliberately contain a false
> premise, because they encode misconceptions that are easy to acquire about this
> project — two of which appeared in the original project brief. Spotting the false
> premise *is* the answer.

---

# Part 1 — The 20-Minute Opening

**Structural decision: lead with the failure, not the success.** It signals
immediately that you can evaluate your own work critically, and it makes everything
that follows read as earned rather than asserted.

## Timing map

| Time | Section | Goal |
|:---|:---|:---|
| 0:00–2:00 | The question | Hook |
| 2:00–4:00 | Why it's hard | Show domain command |
| 4:00–6:30 | **The failure** | Establish honesty early |
| 6:30–11:00 | The method | The contribution |
| 11:00–15:30 | Results | Evidence |
| 15:30–18:00 | **Limitations** | Own them before they're asked |
| 18:00–20:00 | Contributions | Close |

---

## `0:00` — The question

> "Every program's performance depends on the CPU's cache hierarchy — how many
> levels there are, and how large each one is. But that information is essentially
> invisible to ordinary software.
>
> Today, you get it by **asking someone**. The operating system, through a library
> like `hwloc`. An architecture-specific instruction, like x86's `CPUID` leaf 4. Or a
> vendor tool, like Intel's Memory Latency Checker.
>
> Every one of those presupposes that **somebody has already written the answer
> down.**
>
> My question was: **what if nobody has?**
>
> Can a program discover the hierarchy *for itself* — from timing alone, with no
> privileges, no vendor tables, and no architecture-specific instructions?"

**Delivery.** Speak slowly; this is the setup. Count the three tools on your
fingers. After "what if nobody has?" **pause for two seconds** — that is the moment
the examiner engages.

**Trap to avoid.** Never call those tools "bad". They are *more accurate* than this
project on every machine they support. The correct framing is: *"Each is more
accurate than my tool on the hardware it supports — that's precisely the point."*

**Backup evidence if challenged on practical relevance.** The M1 has a ~8 MiB
System-Level Cache. `sysctl` reports nothing about it, `lstopo` shows nothing, and
ARM has no `CPUID` at all — yet it is visible in the latency curve. This can be
demonstrated live (see Part 2, Side-note V.2). It is justification from your own
data, not a hypothetical.

**Anticipated questions**

| Question | Answer |
|:---|:---|
| "Who actually needs this?" | "Portable software that tunes itself — cache-blocked kernels, database join buffers, auto-tuners like ATLAS. And any attempt to characterise a part nobody has documented." |
| "Isn't `hwloc` good enough?" | "It's more accurate than my tool on every machine it supports. But it *reads*; it doesn't measure. Its chain of trust ends at a table someone wrote. Mine doesn't need one." → **full treatment: "The one question you must not fumble", end of Part 1** |
| "What if the OS is lying, or you're in a VM?" | "Then the reference standard is wrong, and every tool that trusts it is wrong with it. A measurement-based tool at least fails *visibly* — the curve won't match the claim." |
| "When does a table genuinely not exist?" | The M1 SLC — demonstrable live. Absent from `sysctl` and `lstopo`, no `CPUID` on ARM, yet present in the curve. |

---

## Clarifications for Section `0:00`

Every term in the opening must be defensible on a follow-up. These are the seven
things most likely to be probed.

### Glossary — full forms

| Term | Full form | What it is |
|:---|:---|:---|
| **hwloc** | **h**ard**w**are **loc**ality | Library that maps machine topology |
| **lstopo** | **l**i**s**t **topo**logy | hwloc's visualiser (`ls` + topology) |
| **sysctl** | **sys**tem **c**on**t**ro**l** | Unix interface for reading/writing kernel parameters |
| **ARM** | **A**dvanced **R**ISC **M**achines | CPU architecture family (originally *Acorn RISC Machine*). RISC = **R**educed **I**nstruction **S**et **C**omputer |
| **CPUID** | **CPU ID**entification | x86 instruction that asks the CPU about itself |
| **MLC** | **M**emory **L**atency **C**hecker | Intel's measurement tool |
| **TLB** | **T**ranslation **L**ookaside **B**uffer | Cache of virtual→physical address translations |
| **SLC** | **S**ystem **L**evel **C**ache | Apple's undocumented shared cache |
| **DRAM** | **D**ynamic **R**andom **A**ccess **M**emory | Main memory |
| **rdtscp** | **R**ea**D T**ime **S**tamp **C**ounter and **P**rocessor ID | x86 timing instruction |
| **WSS** | **W**orking **S**et **S**ize | How much data a program touches at once |
| **MLP** | **M**emory **L**evel **P**arallelism | How many memory accesses can be in flight at once |
| **ISA** | **I**nstruction **S**et **A**rchitecture | A CPU's instruction vocabulary (x86-64, ARM64) |
| **MSR** | **M**odel **S**pecific **R**egister | Privileged CPU control register |
| **GIL** | **G**lobal **I**nterpreter **L**ock | CPython's single-thread lock |
| **PELT** | **P**runed **E**xact **L**inear **T**ime | Change-point detection algorithm |

### What "an architecture-specific instruction, like x86's CPUID leaf 4" means

**Architecture.** Each CPU family has its own **instruction vocabulary**. x86-64
(Intel/AMD) and ARM64 (Apple/Qualcomm) are two different languages; an instruction
from one does not run on the other.

**Architecture-specific.** `CPUID` is an **x86 instruction**. It does not exist in
ARM's vocabulary at all — executing it on ARM raises an illegal-instruction fault.

**Leaf.** `CPUID` works like a numbered form: put a number in the `EAX` register, run
`cpuid`, and the CPU fills in the answer registers.

| Leaf | Question | Answer |
|:---:|:---|:---|
| 0 | "Who made you?" | `GenuineIntel` |
| 1 | "Which model?" | family, model, stepping |
| **4** | **"Describe your caches"** | **level, type, line size, ways, sets** |

Leaf 4's official name is **Deterministic Cache Parameters**, and capacity follows as
`ways × partitions × line_size × sets`.

**Why it matters here:** this is not a measurement — it is the manufacturer's table
burned into silicon, which the CPU reads back. And because it is x86-only, the
objection *"just use CPUID"* fails outright on Apple Silicon.

### "Who actually needs this?" — in plain terms

*Analogy.* You are a travelling chef. Every kitchen has a different counter size, and
you need to know how much you can chop at once — too much and it spills, too little
and you waste time. You could ask the kitchen manager (hwloc) — but what if there is
no manager, or their notes are out of date? Then you measure by trying.

**Four real use cases:**

1. **Cache-blocked kernels (e.g. matrix multiplication).** Large matrix multiplies are
   split into **tiles** that must fit in cache. Tile too large → thrashing; too small
   → wasted cache. Choosing the tile size requires knowing the cache size — and code
   that ships to unknown machines must *discover* it.
2. **Database join buffers.** A join builds a hash table. If it fits in L2 the join is
   fast; if it spills to DRAM it can be ~100× slower. The database wants to size the
   buffer to the cache.
3. **Auto-tuners such as ATLAS** (**A**utomatically **T**uned **L**inear **A**lgebra
   **S**oftware), which runs experiments *at install time* on your machine to find the
   best parameters. Same philosophy: measure, don't assume.
4. **Research on undocumented hardware** — new chips, custom silicon, parts whose
   specifications were never published.

### "If hwloc is more accurate, why would anyone trust your tool?" ⭐

**The honest answer: for the job hwloc does, they shouldn't.** The two answer
different questions.

*Analogy.* A car's spec sheet says the fuel tank holds 50 litres. That is accurate —
more accurate than any measurement you could take. But if the question is *"how far
can I drive right now?"*, the spec sheet is useless; you need the fuel gauge and trip
computer, which measure the current situation.

| | What it tells you |
|:---|:---|
| **Spec sheet** (= hwloc) | How big the tank **is** — static, accurate, unchanging |
| **Trip computer** (= Auto-Echo) | How far you can **actually go** — dynamic, situational |

Concretely, from this project's own data:

| | hwloc says | Auto-Echo says |
|:---|:---|:---|
| Intel L3 | **20 MiB**, always | **19.7 MiB** quiet; **3.5 MiB** under load |
| On 4 KiB pages | **20 MiB**, always | unreachable — curve saturates first (§5.3) |
| M1 SLC | nothing | an 18 MiB-wide ramp in the curve |

**And the key point: hwloc's accuracy is *inherited*, not *earned*.** It is accurate
because the table is accurate. When the table is **missing** (the M1 SLC), or **true
but irrelevant** (a 20 MiB L3 you cannot reach), that accuracy does not help.

*Viva line:* **"hwloc is more accurate about the chip. My tool is more accurate about
the program."**

### "What if the OS is lying, or you're in a VM?" — in detail

**When this happens:**

1. **Cloud VMs.** The hypervisor may show the guest the host's full L3. hwloc reports
   "32 MiB L3" while you share it with seven other tenants and effectively have far
   less.
2. **Containers.** cgroups limit CPU, but `/sys` still exposes the *host's* caches —
   you may hold 0.5 of a CPU while hwloc describes the whole machine.
3. **Hypervisor CPUID masking.** Some hypervisors filter or synthesise CPUID leaves
   (to permit live migration), so cache information arrives wrong or absent.
4. **Firmware bugs.** ACPI tables with incorrect values — this genuinely occurs,
   particularly on new boards.

**Why it matters.** hwloc reports that source faithfully and **has no way to check
it** — it is a faithful reporter of a possibly-wrong source. A measurement-based tool
**fails visibly**: if the OS claims 32 MiB but the curve's knee is at 4 MiB, you have
a **contradiction you can see**, and you have learned something. hwloc alone gives
false confidence.

⚠️ **Honest caveat — say this.** *"That does not mean my tool is right in such a case.
It means the disagreement becomes detectable. And I should add that my own validation
scores against OS ground truth — so if the OS is lying, my accuracy metric is wrong
too. Two independent readings disagreeing tells me something is wrong; it does not
tell me which one is right."* This avoids an over-claim and shows you know the limits.

### "When does a table genuinely not exist?" — in plain terms

The Apple M1 has a cache called the **System Level Cache** — roughly **8 MB**, shared
between CPU and GPU. **Apple never documented it.**

| Source | What it says about the SLC |
|:---|:---|
| `sysctl` | nothing — not one entry |
| `lstopo` (hwloc) | nothing — there is nothing to read |
| `CPUID` | the instruction doesn't exist on ARM |
| **Your latency curve** | **an 18 MiB-wide ramp from ~12 to ~30 MiB** |

The cache **exists** — it was found by reverse engineering ([13]). Nobody wrote it
down.

So "the table doesn't exist" does not mean *"documentation is incomplete by
accident"*. It means **that entry was never written**. The same applies to new chips
before OS support lands, custom or embedded silicon, and pre-release parts under NDA.

**30-second live demo:**

```
$ lstopo
    L2 L#1 (12MB)
      L1d L#4-7 (128KB) + Core L#4-7
    NUMANode (8192MB)          ← straight from L2 to memory
```

*"There is an 8 megabyte cache between that L2 and memory. It isn't here. It is in my
curve."*

---

## `2:00` — Why it's hard

> "Three things make this hard.
>
> **First, the hardware actively hides the signal.** Prefetchers predict your access
> pattern and fetch data early, which flattens the very steps I need to detect.
>
> **Second, the clock is too coarse.** Apple Silicon's timer ticks every 41.7
> nanoseconds. An L1 hit is about 1.5. Timing a single access measures the timer, not
> the memory.
>
> **Third, the obvious primitives aren't portable.** x86 has `clflush` to evict a
> cache line. ARM gives user space nothing equivalent. So any method built on explicit
> flushing cannot cross architectures."

**The numbers behind each barrier**

| Barrier | Key figure | Solution (save it for the method section) |
|:---|:---|:---|
| Prefetching | — | Randomised pointer chase; removes the need for a flush entirely |
| Coarse timer | 41.7 ns tick vs 1.53 ns L1 = **27× coarser** | 2²⁰ hops per window → ~38,500 ticks → ±0.0026% |
| No portable flush | `clflush` is x86-only; nothing in ARM/macOS user space | WSS design overflows the cache *by construction* |

**A deliberate structural choice.** The dissertation's §2.4 lists **four** barriers;
the fourth is address translation (TLB). Mention only **three** here. The first three
*shaped the design* — they were known in advance. The fourth is a *finding*,
discovered when the Intel L3 vanished. Revealing all four now would spoil your best
result. §2.4 states this explicitly: *"The first three shape the probe's design; the
fourth bounds what it can resolve."*

**Delivery.** Move quickly — three points in two minutes. This is setup, not
argument. **Do not give the solutions yet**, or the method section will be empty.

**Anticipated questions**

| Question | Answer |
|:---|:---|
| "Why not just disable the prefetcher?" | "On Intel you can, via an MSR — but that needs ring 0, and the whole premise is unprivileged operation. On Apple Silicon there is no such control at all." |
| "How can you report 1.5 ns with a 41.7 ns clock?" | "I don't measure one access. I measure the total of 1,048,576 accesses — about 38,500 ticks — so ±1 tick is ±0.0026% on that total. Dividing by an exact integer adds no error." |
| "ARM has `DC CIVAC` for cache maintenance." | "It exists in the architecture, but macOS does not expose data-cache maintenance to user space — it traps. The design had to assume no flush primitive at all." |

---

## Clarifications for Section `2:00`

### What is `clflush`, and what does "evict a cache line" mean?

`clflush` = **C**ache **L**ine **FLUSH** — an x86 instruction.

**Novice.** A book sits on your desk (data in cache). `clflush` means *"put that book
back on the distant shelf."* Next time you need it, you must walk all the way to the
shelf — you cannot grab it from the desk.

**Intermediate.** You give it an **address**; the CPU removes the **cache line**
containing that address from **every cache level** — L1, L2, L3, across cores.

```c
_mm_clflush(ptr);     // in C
clflush [rax]         // in assembly
```

A **cache line** is the smallest unit a cache stores — never a single byte:

| Machine | Line size |
|:---|:---:|
| x86 (Intel/AMD) | **64 B** |
| Apple Silicon | **128 B** |

So "evict a cache line" = remove it from cache, forcing the next read to come from a
lower level or DRAM.

**Why anyone wants it.** To measure DRAM latency you need a *guarantee* the data is
not cached:

```c
clflush(addr);           // remove from cache
t0 = rdtscp();
value = *addr;           // now this MUST come from DRAM
t1 = rdtscp();           // → this is DRAM latency
```

Without a flush you cannot know where the data came from — L1, L3 or memory. **The
reference paper's method depended on exactly this**, which is what tied it to x86.

💡 **And this is where the WSS design wins.** It needs no flush at all: if the working
set is *larger than the cache*, the data is evicted **by construction** — there is
simply no room. Eviction comes from the geometry of the experiment, not from an
instruction.

### How does the hardware "actively hide the signal"?

**"Actively" is the operative word.** This is not random noise — it is the CPU's
*deliberate optimisation*. Making memory look fast is the CPU's job. Measuring how
fast it really is, is yours. **The two goals are in direct conflict.**

**Novice.** You want to time the walk to the shop, but a helpful friend keeps running
ahead and fetching things before you ask. Your stopwatch reads ~0 every time, and you
conclude the shop is next door. Wrong.

**Two mechanisms matter here.**

**(a) The prefetcher reads your pattern.**

| Access pattern | What the prefetcher does | What you actually measure |
|:---|:---|:---|
| Sequential (0,1,2,3…) | Learns it, fetches ahead | **Prefetch bandwidth**, not latency |
| Fixed stride (0,16,32…) | Detects the stride, fetches ahead | Wrong again |
| **Random chase** | **Cannot predict at all** | ✅ **True latency** |

If the prefetcher wins, latency looks **flat at every working-set size** — the
staircase vanishes and you would conclude the machine has no cache hierarchy.

**(b) Out-of-order execution overlaps accesses.**

The CPU has a 300-plus-entry reorder buffer. Given *independent* loads it runs 10–20
of them concurrently:

```
Independent loads:   [100ns]            ← 10 loads overlap
                     [100ns]               total still ~100 ns
                     [100ns]               → you measure "10 ns per access"
                     ...

Dependent chase:  [100ns] → [100ns] → [100ns] → ...
                  ← strictly sequential; no overlap is possible
                  → you measure the full 100 ns  ✅
```

This is why **MLP = 1** matters, and the pointer chase enforces it *in hardware*
rather than by convention.

### "ARM gives user space nothing equivalent" — stated precisely

Be precise here, or an examiner will correct you.

**❌ Wrong to say:** *"ARM has no cache-flush instruction."* It does:
- `DC CIVAC` — **D**ata **C**ache **C**lean and **I**nvalidate by **V**irtual
  **A**ddress to point of **C**oherency
- `DC IVAC` — Invalidate by VA

**✅ Correct:** the instruction **exists in the architecture, but whether user space
may execute it is decided by the OS.**

| Platform | Flush available to user space? | Mechanism |
|:---|:---|:---|
| **x86 (any OS)** | ✅ Always | `clflush` is unprivileged at the hardware level |
| **ARM Linux** | ⚠️ Usually | Governed by the `SCTLR_EL1.UCI` bit; Linux generally enables it |
| **ARM macOS** | ❌ Never | macOS does not expose data-cache maintenance to EL0 — it **traps** |

**The portability argument in full:**

```
1. The method requires a flush
2. Flush is:  always available on x86            ✅
              usually available on ARM Linux      ⚠️
              never available on Apple Silicon    ❌
3. Therefore the method works on x86 and fails on Apple Silicon
4. Therefore it is not portable
```

💎 **Why this mattered more than convenience.** It determined the whole design. §2.4
states it directly: *"This is why the WSS formulation is not merely a convenient
alternative to the reference method but **the only one of the two that can be made
portable at all**."*

**And it links back to Barrier 1** — the answer to the Section 2 check question:

> The pointer chase defeats the prefetcher **and** removes the need for a flush.
> **One solution, two barriers.** That is not a coincidence: the property that makes
> the chase unpredictable — a working set larger than the cache — is the same property
> that forces eviction automatically.

---

## `4:00` — The failure

> "My first implementation was a portable approximation of the reference paper's
> method: flush a line, write it, time the load back.
>
> **It failed on both architectures.** And when I investigated why, the reason was not
> what I expected.
>
> I had assumed the problem was ARM's missing `clflush` — an architectural
> limitation. So I ran the same baseline on Intel, *with* a working `clflush` and
> `rdtscp`. It still failed. Two tiers on a four-level machine — and the tier it
> labelled 'L1' measured **178 nanoseconds**, two orders of magnitude above that
> core's true 1.6-nanosecond L1.
>
> The real fault was structural. **Writing a line immediately before timing its read
> pulls it into L1, so every measurement is an L1 hit by construction.** The flush
> accomplishes nothing, because the store simply re-populates the line.
>
> That mattered, because it meant a per-architecture port would not have helped. The
> measurement *design* had to change — and the redesign had to satisfy three
> constraints at once: never write before reading, never time a single access, and
> never require a flush."

**Delivery.** This is your strongest section. Most candidates hide failure; you are
leading with it. Speak confidently, not apologetically. The key beat is that you
refuted **your own first explanation** — that is scientific maturity, and examiners
are listening for exactly it.

**Anticipated questions**

| Question | Answer |
|:---|:---|
| "Why not just fix the baseline?" | "Because the fault wasn't a bug, it was the design. Write-before-read guarantees an L1 hit *by construction* — no amount of fixing the flush repairs that. The remedy had to be a measurement that never writes before reading." |
| "Isn't 178 ns just `rdtscp` overhead? A better timer might rescue it." | "Partly — the absolute values are timer-dominated. But that's the second barrier, not the first. Even with a perfect timer, every access would still be an L1 hit, so you'd measure L1 precisely and never see L2, L3 or DRAM. Two tiers on a four-level machine is the structural failure; 178 ns is the timing failure on top of it." |
| "How do you know write-before-read is the cause?" | "Because I removed the confound. The 'x86-bound' explanation predicts it works where `clflush` exists. I ran it on Intel with a working `clflush` and `rdtscp` — the two conditions whose absence the explanation blamed — and it still failed. That falsifies the architectural account and leaves the structural one." |
| "Did you try the LOF filter the paper proposes?" | "Yes — §4 evaluates it directly. LOF flagged about 0.04% of samples, and 100% of the survivors still lay exactly on integer timer-tick multiples. That's direct evidence the failure is structural, not filterable noise." |
| "Why keep the failed baseline in the repository?" | "Because it's the evidence for the design decision. Deleting it would leave the redesign unmotivated. It ships as `--method samples` and is reproducible." |

---

## `6:30` — The method

> "The redesign has two layers, and I want to be precise about which one is my
> contribution.
>
> **The measurement layer is classical.** It's a working-set-size pointer chase,
> descending from Saavedra and Smith, and from McVoy and Staelin's `lat_mem_rd` in
> lmbench. Claiming it as novel would be indefensible.
>
> Each slot in a buffer holds the address of the next, linked into a single random
> Hamiltonian cycle. Because each load's address is the *result* of the previous
> load, the CPU cannot run ahead — so the prefetcher is defeated with **no flush
> instruction at all**. That solves barriers one and three together, and it's why the
> method is portable rather than x86-only.
>
> For the coarse clock, I time a million dependent hops in a single window and
> divide. I'm not measuring one access precisely; I'm measuring a total of about
> 38,000 timer ticks, where the ±1 tick quantisation is 0.003 percent.
>
> **The inference layer above it is the contribution.** Given a noisy latency curve,
> two questions must be answered with no prior knowledge of the machine: *how many*
> levels exist, and *where* each boundary lies.
>
> I answer them separately, because they have different sufficient statistics. *How
> many levels* is a property of the multiset of latency values — a machine with four
> plateaus has four modes regardless of where they fall. Order doesn't matter. *Where
> the boundaries are* is a property of the ordering, and order matters entirely.
>
> So counting is done by clustering the log-latencies, and localisation by
> change-point detection constrained to that count.
>
> The counting step uses **exact one-dimensional k-means by dynamic programming** —
> Fisher's 1958 result, known today as `Ckmeans.1d.dp`. This matters because in one
> dimension the optimal partition is provably *contiguous in sorted order*, which
> collapses the search space from a Stirling number of partitions to a choice of k−1
> split points, and admits an exact solution. So unlike Lloyd's algorithm, the
> partition returned is the **global optimum** for every candidate count —
> deterministic, with no seeding, no restarts, and no random state to report.
>
> The number of levels is then chosen by the Silhouette coefficient, which is not
> monotone in k and therefore has an interior maximum — meaning it can select a count
> **without a penalty term.** That's the point: the penalty parameter is exactly the
> per-machine tuning knob this project set out to eliminate."

**Delivery.** "Claiming it as novel would be indefensible" — say this line. Examiners
wait for it. Saying it first means it can never be used against you.

**Anticipated questions**

| Question | Answer |
|:---|:---|
| "Lloyd's gave the same answer — so what did the DP buy?" | "Nothing to the numbers, and I say so explicitly — the audit shows the migration changed no reported result. What it changed is the *status* of the claim: the count is no longer contingent on a solver's initialisation. It converts an empirical observation about two curves into a property of the algorithm." |
| "How do you know the DP is actually optimal?" | "I verified it against brute force — every partition enumerated exhaustively for small n, including all *non-contiguous* set partitions, which tests the contiguity lemma itself and not just the recurrence. 420 checks, zero mismatches." |
| "Why Silhouette rather than BIC or the gap statistic?" | "Two reasons. §5 *ranks* the estimators against each other, so scoring the mixture by BIC and k-means by Silhouette would confound the model with the criterion. And BIC is badly behaved here — within-plateau variance is extremely heterogeneous (the Intel L1 band spans 0.38 ns p5–p95, DRAM spans 26 ns), so a mixture is rewarded for adding narrow components inside a single physical plateau." |
| "Counting ignores order — isn't that discarding information?" | "Order isn't discarded by the pipeline; it's used at the stage where it's informative. *How many levels* is a property of the multiset — four plateaus give four modes wherever they sit. *Where the boundaries are* is a property of the ordering, and that's exactly what the change-point stage consumes." |
| "Why segment on log-latency?" | "Without the log, squared-error cost is dominated by the deep steps. The L1→L2 step is about 3 ns and the L2→DRAM step about 110 ns; on raw nanoseconds the inner hierarchy is invisible to the cost function. In log space both steps are comparable in magnitude." |
| "What's the complexity? Grønlund has O(n log n)." | "Mine is O(kn²). At 94–388 points the quadratic fill costs milliseconds, so the simpler recurrence is retained deliberately — I cite the sharper bound rather than pretending it doesn't exist." |
| "Why not just use PELT with a fixed penalty?" | "That's the knob I'm removing. Tables 9 and 13 show the *same* hand-set penalty giving different counts on the two machines — which is precisely the per-machine tuning constant the project exists to eliminate." |

---

## `11:00` — Results

> "I validated on two machines — an Apple M1 and an Intel Raptor Lake core. ARM64 and
> x86-64, the same code path on both.
>
> On the **M1**: three levels, all five estimators agreeing, both documented caches
> recovered within one octave.
>
> On the **Intel**: four levels, all three documented caches matched, with a mean
> absolute capacity error of 6.3 percent over ten sweeps.
>
> But the two most interesting results are the ones where something went **wrong**.
>
> **First — page size can hide an entire cache.** With the default 4 KiB pages, the
> Intel L3 was invisible. The curve saturated at 143 nanoseconds by about 4 megabytes
> and stayed flat — because once the working set exceeds the TLB's reach, every
> dependent load triggers a page-table walk whose own accesses miss to DRAM. The
> curve reaches DRAM latency *before* the L3 boundary is ever seen.
>
> Under a 2 MiB huge-page allocation, the same code recovers all four levels. So the
> binding constraint on user-space discovery of a deep hierarchy is **address
> translation, not the inference layer.** That's a controlled result, not an
> observation — it's the only variable I changed.
>
> **Second — a shared cache does not measure as its nominal size.** What a single
> core recovers of a shared L3 is the portion actually available to it. I tested that
> directly: under an eight-worker streaming load, the detected L3 falls from 19.7
> megabytes to 3.5. The quantity being measured is real — but it's *availability*,
> not capacity.
>
> Finally, I validated against prior art rather than only against myself. I built
> lmbench's `lat_mem_rd` and swept the same silicon. Both tools recover the same
> four-tier staircase, with an almost identical L1-to-L2 step — 3.0× for mine, 3.1×
> for lmbench.
>
> And then the stronger test: I applied my **inference layer** to lmbench's curve,
> with nothing seeded from my own result. It selects the correct level count, and
> recovers both TLB-unmasked capacities — L1 to within 17 percent, L2 to within 10.
> So it isn't only my probe that works; the inference generalises to another tool's
> data."

**Delivery.** "The two most interesting results are the ones where something went
wrong" — this phrase does a lot of work. It shows you are *interpreting* results, not
reciting them. Point at Fig. 7 for the huge-page result.

**Anticipated questions**

| Question | Answer |
|:---|:---|
| "Only two machines?" | "Yes — and both consumer laptop performance cores. An AMD Zen part is the highest-value addition, because its L3 is a per-CCX victim cache — a genuinely different topology — which would test whether the contention finding generalises or is a ring-LLC artefact." |
| "Couldn't the 3.5 MiB knee just be noise?" | "Three sweeps, all three gave 3.5 MiB with zero spread. And the direction is predicted, not fitted: more contention, smaller mappable share." |
| "Every latency rose under load — is the capacity comparison still valid?" | "The knee is a working-set *size*, and it is frequency-invariant. A uniform multiplier shifts every latency but cannot move the size at which a plateau ends. I report the uniform rise honestly and note that its magnitude exceeds what turbo range alone explains." |
| "The lmbench comparison is confounded — different OS, page size, stride." | "Agreed, and I say so. lmbench ran under WSL2 on 4 KiB pages at a 128-byte stride against my 64-byte line spacing. The L2-band divergence follows from the page size, and the decisive control — running my own tool inside that same WSL2 — was cheap and I did not take it. That's the first thing I'd do next." |
| "Why 3 sweeps on the M1 but 10 on the Intel?" | "The Intel run was repeated to ten after the L3 aggregation issue surfaced; the M1 was not. That's a genuine inconsistency in experimental power between the two headline results, and it's stated in §5.1." |
| "The M1 L1 is +23% off — isn't that a lot?" | "It's a soft-knee artefact, and it's directional rather than random. A random-access set moderately larger than the cache still enjoys high residency, so average latency rises gently past nominal. The onset estimator recovers 128 KiB exactly — but it's catastrophic elsewhere, so the bounded-error edge estimator remains the default." |
| "With the SLC, is it three levels or four?" | "Three is the reproducible answer. The L2 is 12 MiB and the SLC about 8 MiB — under one octave apart, roughly seven sample points at my density — so the method merges them. Forcing a finer split is stable across penalties 3 to 6, and is reported as a *candidate* sub-structure, not a headline level." |

---

## `15:30` — Limitations

> "I want to state the limits before you ask.
>
> **The hardware base is narrow.** Two machines, both consumer laptop performance
> cores. Every generalisation rests on n equals two, of one class. That is the binding
> constraint on this dissertation.
>
> **There are no inferential statistics.** The contention result is three sweeps
> against three, resting on effect size rather than a hypothesis test.
>
> **And one result I had to correct.** I originally reported the L3 at 13.9
> megabytes — a 30 percent under-read — and I built an explanation around it. That
> figure was substantially an artefact of **my own aggregation**. I was detecting the
> boundary on the minimum-over-sweeps curve. The minimum is the right statistic for a
> *latency*, because interference can only add time. It is the wrong statistic for a
> *knee*, because the lower envelope departs the plateau early. Detected per sweep,
> nine of ten give 19.7 megabytes — within 1.5 percent of nominal. I withdrew the
> original figure and the explanation I had built on it.
>
> **And a limitation of the tool itself.** The level count is stable on a quiet
> machine. But on a contaminated run, the same counter reported **seven levels on a
> four-level machine** — and nothing in the pipeline detects that condition. For a
> discovery tool, failing in a way the user cannot see is the most serious limitation
> I have."

**Delivery.** Counter-intuitive but decisive: this section is what separates a good
dissertation from an exceptional one. Deliver it confidently. You are not confessing
weakness — you are demonstrating that you can evaluate your own work. Make eye
contact here.

**Anticipated questions**

| Question | Answer |
|:---|:---|
| "If the aggregation was wrong, how did it reach a draft?" | "Because it was plausible and I had a mechanism ready to explain it — contention. That's the trap: a wrong number with a good story survives longer than a wrong number without one. It surfaced when I ran ten sweeps and looked at per-sweep detections rather than the aggregate." |
| "How would you fix the count instability?" | "A dispersion self-diagnostic. The condition is already detectable from data the pipeline computes — the contaminated run's L1 band spans 1.57–3.52 ns against 1.57–1.69 ns when quiet. A within-plateau spread check could flag or refuse such a run rather than publishing its count." |
| "What would a third machine buy you?" | "AMD Zen tests the one claim I cannot currently defend: that the shared-cache contention effect generalises across LLC topologies. Zen's per-CCX victim L3 is architecturally different from Intel's ring-shared L3. Either outcome — it reproduces or it doesn't — is a result." |
| "Why no statistics?" | "No good reason. With ten sweeps per condition, a rank test and bootstrap intervals are straightforward. It's the cheapest remaining improvement and I don't defend its absence." |

---

## `18:00` — Contributions and close

> "So the contribution is three things.
>
> **One:** a portable, flush-free measurement path, validated across two instruction
> set architectures.
>
> **Two:** an unsupervised inference layer that determines the **shape** of a
> hierarchy — not just its parameters given a known shape — with no per-machine
> tuning constant, and with the counting step solved exactly rather than
> heuristically.
>
> **Three:** two controlled experiments that delimit where the method works. The
> huge-page control isolates address translation as the binding constraint. The
> contention experiment shows that what you recover of a shared cache is
> availability, not capacity.
>
> The honest summary is that this is a **portable, low-resolution instrument** in a
> space whose high-resolution corner — eviction-set construction, from the
> side-channel literature — is already well mapped. It trades precision for the
> ability to be dropped onto hardware nobody has described yet.
>
> Thank you."

**Anticipated questions**

| Question | Answer |
|:---|:---|
| "Isn't this just lmbench with clustering bolted on?" | "The measurement is lmbench's, and I say so in §2.2. But lmbench gives you a curve and *you* read the knees off it — a human decides how many levels there are. My contribution is that nobody reads anything. And I validated that inference on lmbench's *own* curve, where it recovers the correct count without being told." |
| "Couldn't the side-channel people do this better?" | "For associativity and line size, yes — decisively. Eviction-set construction recovers set structure exactly. I say so in §2.3, and concede that the stride sweep §6 proposes is the weaker tool. The trade is that those methods are architecture-specific and assume a known target; mine buys portability with resolution." |
| "What would you do differently?" | "Run my own tool inside the WSL2 environment I had already built lmbench in. It would have removed the cross-check confound and given me a third platform, for one evening's work." |
| "Is this publishable?" | "As a workshop paper with the AMD data added, I think so — the inference-transfer result and the huge-page control are the parts that would carry it. Not without a third machine and statistics." |
| "Your biggest weakness in one sentence?" | "Two machines of the same class, so every generalisation rests on n = 2 — and I'd defend the work anyway, because the controlled experiments are valid on the machines I have, and the limits are stated rather than hidden." |

---

## Cheat card — memorise these

| Claim | Number |
|:---|:---|
| Timer vs L1 | 41.7 ns vs 1.53 ns (**27×**) |
| Hops per timing window | **2²⁰** ≈ 38,500 ticks, ±0.003% |
| Baseline failure | **2 tiers**; "L1" = **178 ns** vs true **1.6 ns** |
| M1 result | 3 levels, **2/2** caches, +23.0% / +16.1% |
| Intel result | 4 levels, **3/3** caches, mean error **6.3%** (10 sweeps) |
| 4 KiB pages | saturates at **143 ns** by ~4 MiB; L3 invisible |
| 2 MiB pages | ~**122 ns**; L3 recovered at **19.7 MiB** (−1.5%) |
| Contention | 19.7 → **3.5 MiB** (**−83%**) |
| lmbench L1→L2 step | **3.0× vs 3.1×** |
| Inference transfer | k = 4 correct; L1 **+16.7%**, L2 **−10.0%**, **2/3** |

---

## The one question you must not fumble

> *"If I can just run `lstopo` and see the whole hierarchy in one second, what is
> this project for?"*

Every examiner asks some version of this. A weak answer here undoes twenty minutes of
good work.

### Three answers that lose marks

| Tempting answer | Why it fails |
|:---|:---|
| "hwloc is inaccurate" | It isn't. It is **more** accurate than this project on every machine it supports. |
| "hwloc needs privileges" | It doesn't. It runs unprivileged, exactly as this project does. |
| "hwloc isn't portable" | It is **more** portable — it supports far more platforms than the two validated here. |

⚠️ **Note the exposure in §1.** The motivation paragraph currently says *"no
privileges, no per-architecture instructions"*. Against hwloc, "no privileges" is a
**null differentiator** — an examiner will simply reply "neither does hwloc". The real
differentiators live in §2.2 and §5.3, not in the motivation.

### The honest answers, strongest first

**1. hwloc reports what is *documented*; this project measures what is *there*.**
Demonstrable live. `lstopo` on the M1 shows `L2 (12MB)` and then straight to
`NUMANode` — yet a ~8 MiB System Level Cache sits between them. No `sysctl` entry, no
`CPUID` on ARM. And it is not invisible in the data: §5.2's curve shows an **18 MiB
-wide ramp** from ~12 to ~30 MiB where a machine with only L2 and DRAM would show a
sharp step. hwloc cannot simply add it, because there is no OS interface to read it
from — it would have to hardcode it per chip, which is exactly "a table someone
wrote".

**2. Topology is not behaviour.** `lstopo` reports the Intel L3 as 20 MiB. That is
true, and on 4 KiB pages it is also unreachable — §5.3 shows the curve saturating at
143 ns by ~4 MiB because page-walk cost arrives before the L3 does. hwloc reports
20 MiB regardless. *Line to use:* **"hwloc told me the L3 was twenty megabytes. My
measurement told me I couldn't reach it. Both were correct, and only one of them
changed my code."**

**3. Nominal vs effective capacity — deploy carefully.** Under an eight-worker load
the L3 a single core can map falls from 19.7 MiB to 3.5 MiB; hwloc still reports
20 MiB, because it is a static architectural fact. For choosing a cache-blocking
factor or sizing a join buffer, the *available* capacity is the number that matters,
and it cannot be looked up.
⚠️ **Do not oversell this.** The validation scores accuracy *against nominal ground
truth*, so the project's own success metric treats nominal as the target. Claiming
"nominal is the wrong target" creates an internal inconsistency an examiner may spot.
*Safe framing:* "The project targets nominal capacity and validates against it. What
the contention experiment revealed is that a shared cache's measurable capacity is
load-dependent — a finding about the limits of the method, and incidentally a
quantity hwloc cannot report at all." Present it as **discovered**, not as founding
motivation.

**4. The chain of trust can break — weakest; mention once.** New silicon before OS
support lands, VMs that do not pass through topology, emulated or embedded targets.
Real, but there is **no evidence for it in the dissertation**, so state it briefly and
move on.

### The concession that makes the rest credible

> "If your question is 'what caches does this machine have', and it's a documented,
> supported, quiet machine — **use hwloc. It's better than my tool at that job.** I'm
> not competing with it."

Examiners trust a candidate who concedes the obvious point. Refusing to concede makes
everything else sound like special pleading.

### The 60-second answer

> "Fair question — and if the machine is documented, hwloc is the better tool. I'm not
> competing with it.
>
> But hwloc doesn't measure anything. It reads what the OS and firmware expose, so its
> answer is only as complete as the table behind it. **Two things follow.**
>
> **First, that table can be incomplete.** This laptop has an 8 megabyte System Level
> Cache. `lstopo` shows L2 and then memory — nothing in between. `sysctl` has no entry
> for it, and ARM has no CPUID. But it's visible in my latency curve as an
> eighteen-megabyte-wide transition where there should be a sharp step. I can show you
> that in about thirty seconds.
>
> **Second, topology is not behaviour.** hwloc told me the Intel L3 was twenty
> megabytes. On the default four-kilobyte pages, my measurement showed I couldn't
> reach it — address-translation cost saturates the curve before the L3 boundary
> appears. Both statements are true. Only the measured one would change how you write
> the code.
>
> So hwloc answers *'what did the manufacturer put in this chip?'* My tool answers
> *'what can a thread actually observe here?'* Most of the time you want the first.
> When the table is incomplete, or when behaviour and topology disagree, you want the
> second."

---

**Rehearsal.** Time yourself. Most candidates overshoot. If you're at 24 minutes, cut
detail from Results (shorten the lmbench passage) — **never cut Limitations.**

**Before the viva.** Appendix A.3 declares that every reference was consulted by the
author, and the bibliography grew from 24 to 66 entries late in the project. Either
read them or amend the clause. If asked "have you read Vila et al.?", you need an
answer. That is an integrity question, not a technical one, and it carries more
weight.

---

# Part 2 — Tutoring Session Log

Concepts worked through on the Novice → Intermediate → Expert ladder, with the
question asked, the answer given, and verification.

**Score so far:** 1.1(a) ✔ · 1.2(b) ✔ · 1.3(a) ✔ · 1.3(b) ✔½ · 1.4 pending

## Module 1 — The C Probe

### Concept 1.1 — Why C rather than Python

**Novice.** Try timing a hummingbird's wingbeat with a hand-operated stopwatch. Your
reaction time is ~250 ms; the wingbeat is ~20 ms. You are measuring *yourself*, not
the bird. The instrument must always be faster than the signal.

**Intermediate.** The measured L1 hit is **1.53 ns** (`data/validation_report.md`). A
single CPython bytecode dispatch costs roughly **30–100 ns** — the instrument would
be 20–60× slower than the signal. So the timing loop lives in C:
`src/autoecho/wss/wss_probe.c:364`, one line — `p = (void **)(*p);`. Python
(`wss/__init__.py`) only orchestrates: choose sizes, call `measure_wss()`, convert
ticks to nanoseconds, assemble a DataFrame. It never touches the hot path.

**Expert.** More fundamental than speed is **memory layout control**. In CPython,
`list[i]` is a pointer to a boxed `PyObject` that may live anywhere on the heap — the
allocator decides addresses, not you. The entire experiment depends on slot *k*
sitting exactly `k × line_size` bytes from a page-aligned base, because capacity is
inferred from *which addresses map to which cache sets*. Python cannot guarantee
this. Even an infinitely fast Python timer would measure a working set whose true
footprint you could not state.

**Question 1.1** — A colleague says: "Write it in Python, just use NumPy — its inner
loops are compiled C anyway." Answer in two parts: (a) the quantitative argument,
using the real L1 figure and bytecode dispatch cost; (b) a second, *independent*
reason that has nothing to do with speed.

**Student's answer:**
> (a) We can't measure a signal of 1.53 ns with Python as it can measure a signal
> within the range of 30–100 ns. Also NumPy is beneficial in continuous memory
> allocation rather than random memory allocation.
> (b) Don't know.

**Verification — (a): strong pass ✔**

The core principle is right: the instrument is coarser than the signal. To sharpen
it, add a number — the probe performs 2²⁰ = 1,048,576 hops per measurement:

| | Time |
|:---|:---|
| Real signal (1,048,576 × 1.53 ns) | ~1.6 ms |
| Python loop (× ~50 ns/hop) | ~52 ms |

The measurement would be **97% interpreter, 3% memory** — the hierarchy drowns in
that noise. This is more convincing than "20–60× slower".

*Correction:* "NumPy is beneficial in continuous memory allocation" — right instinct,
imprecise wording. Precisely: NumPy is fast when one operation applies to a **whole
array at once** (`arr * 2`), so Python is involved only once. **A pointer chase
cannot be vectorised**, because hop *n+1* needs hop *n*'s result. NumPy's entire
advantage is therefore **structurally inapplicable**; the loop would run in Python
and you are back to problem (a).

**Verification — (b): taught**

**Core answer:** a NumPy array can only hold **values** (int64/float64/bool) — **not
addresses**. The chase requires `*(void **)slot = (void *)next;`
(`wss_probe.c:347`) — each slot holding the *real memory address* of the next. In
NumPy you would store indices instead, and three things break:

1. **The dependency becomes invisible to the hardware.** In C, `p = *p;` is one load
   whose result is the next address; the CPU's load unit sees a clean dependent chain
   (which is why no `lfence` is needed). In Python, `i = arr[i]` is bounds check →
   PyObject unbox → address computation → load → box. The CPU sees interpreter
   bookkeeping, and the theoretical foundation of the measurement disappears.
2. **Alignment control is lost.** C requests `posix_memalign(&p, 16384, size)`
   (`AE_ALIGN`, `wss_probe.c:137`). NumPy offers no way to request 16 KiB alignment;
   on a non-aligned buffer a cache line can straddle two pages, corrupting the count
   of distinct pages touched.
3. **Huge pages become impossible.** `VirtualAlloc(..., MEM_LARGE_PAGES, ...)` cannot
   be requested through NumPy — meaning the entire §5.3 huge-page result, which
   unmasked the Intel 20 MiB L3, would not exist.

**How to remember it:** (a) says *"Python is slow."* (b) says *"even if Python were
infinitely fast, the experiment would still be invalid"* — because you would measure
a working set whose actual memory footprint you cannot state. That is what makes (b)
independent of (a).

### Side-note 1.1a — What is CPython? (student asked)

**Novice.** **Python** is a *language* — rules, grammar, a specification. **CPython**
is one *implementation* of it: the actual program that reads and runs your `.py`
file. It is itself written in C, hence "**C**Python". Analogy: "Hindi" is a language;
a person *speaking* Hindi is an implementation. Other implementations: PyPy (JIT),
Jython (JVM), MicroPython.

**Intermediate.** The proof is in the repository:
`src/autoecho/wss_probe_c.cpython-313-darwin.so` — the filename literally encodes
"cpython-313" (CPython 3.13) and "darwin" (macOS). Confirmed: implementation =
CPython, version = 3.13.2. `wss_probe.c` uses the CPython C-API in 23 places
(`#include <Python.h>`, `PyArg_ParseTuple`, `PyFloat_FromDouble`,
`Py_BEGIN_ALLOW_THREADS`, `PyErr_NoMemory`). So `setup.py`'s
`python_requires=">=3.11"` is not merely a language-version statement — it is a
CPython C-API compatibility statement. The extension will not load on PyPy without
recompilation.

**Expert.** Where "30–100 ns per bytecode dispatch" comes from: `.py` → bytecode →
the eval loop in `ceval.c`. Per instruction: fetch, decode, dispatch (an
often-mispredicted branch), pop `PyObject*` operands from the stack, runtime type
check, `Py_INCREF`/`Py_DECREF` reference counting, and heap allocation for new
objects. In Python, `x = 5` creates a heap-allocated object with a refcount and type
pointer; in C, `int x = 5` is a register. That cost is the honest price of dynamic
typing plus reference counting plus interpretation — worth paying for data pipelines,
not for measuring 1.53 ns. Related: `Py_BEGIN_ALLOW_THREADS` (`wss_probe.c:353`)
releases the GIL, which is itself a CPython-specific mechanism.

### Side-note 1.1b — What is the GIL, and what is its trade-off? (student asked)

**Novice.** GIL = **Global Interpreter Lock**. A kitchen with 8 cooks and 8 chopping
boards but **only one knife** — only one cook can chop at a time. Cooks = threads,
boards = CPU cores, knife = GIL. In CPython only **one thread executes Python
bytecode at a time**, even on a 10-core machine. So `threading` cannot make CPU-bound
Python work truly parallel.

**Intermediate.** `wss_probe.c:353` `Py_BEGIN_ALLOW_THREADS` and `:373`
`Py_END_ALLOW_THREADS` — "put the knife down / pick it back up". Between them only
plain C variables appear (`p`, `g_sink`, `best`, `c0`, `c1`) — not a single
`PyObject`. **Golden rule:** you must not touch any Python object between BEGIN and
END. Calling `PyFloat_FromDouble()` inside would create a refcount race and cause
random, hard-to-reproduce interpreter crashes.

**Expert — why the GIL exists.** Reference counting. `Py_INCREF`/`Py_DECREF` are not
atomic — at machine level they are *read → add → write*. Two unlocked threads
incrementing the same refcount can lose an increment, so the object is freed while a
reference is still live: **use-after-free**, a crash or a security bug. Three
solutions existed: (1) a lock per object — makes single-threaded code ~2× slower;
(2) atomic refcounts — cache-line bouncing, slow; (3) **one global lock** —
single-threaded code stays fast and C extensions stay simple. Guido chose (3). The
GIL is not a bug; it is a **deliberate trade-off**.

**The trade-off — what you gain:** fast single-threaded Python (no per-object locking
overhead); simple C extensions (`wss_probe.c` uses no mutex at all and is still
safe); simple, predictable refcounting with no GC pauses. **What you lose:** CPU-bound
threads cannot run in parallel — on a 10-core machine, pure-Python CPU work still
gets one core. **Escape routes:** `multiprocessing` (separate process = separate
GIL), a GIL-releasing C extension (this project), `asyncio` for I/O-bound work.
Python 3.13 ships an experimental free-threaded build (PEP 703) that removes the GIL,
though C extensions must be compiled separately for it.

**The trade-off for this project (viva-relevant).** `measure_wss()` runs for seconds
(a full sweep takes ~3 minutes); holding the GIL that long would freeze the whole
interpreter, so releasing it is correct engineering. **Honest caveat:** releasing it
also *permits* other Python threads to run during measurement and add noise — moot
here because the pipeline is single-threaded. **Key insight:** because the C code
releases the GIL, someone *could* run sweeps in parallel threads — and the result
would be **completely wrong**, because those threads would evict each other's data
from the shared L3. You would measure mutual interference, not hardware latency. That
is exactly the effect §5.3.2 measures (8 workers drove the detected L3 from 19.7 MiB
to 3.5 MiB). The probe is therefore **deliberately sequential** — not slow, but
correct, with measured proof in the dissertation.

### Concept 1.2 — Sequential vs randomised pointer-chasing

**Novice.** A **smart librarian** is watching you. Ask for books 1, 2, 3, 4 and they
learn the pattern, fetching book 5 before you ask — every book feels instant, and
you wrongly conclude your desk is infinite. To measure the desk you must be
**unpredictable** (book 400, then 17, then 933). That librarian is the **hardware
prefetcher**.

**Intermediate.** Two distinct properties in `wss_probe.c` — do not conflate them:
**randomness** (Fisher–Yates, line 337) stops the prefetcher learning a pattern;
the **single Hamiltonian cycle** (line 344, `% nslots`) stops the chase falling into
a short sub-loop.

**Expert.** The deep property is not randomness but **serialisation by data
dependency**. In `p = *p`, load *n+1*'s address is load *n*'s result. The CPU's
300-plus-entry reorder buffer *could* overlap 20 loads, but cannot, because the
address is unknown until the previous load returns. That gives **MLP = 1** — pure
load-to-use latency. Independent random accesses would also defeat the prefetcher,
but the CPU would overlap 10–20 of them, so you would measure `latency ÷ MLP` — about
a tenth of the truth, with the plateaus squashed together.

### Side-note 1.2a — What is a Hamiltonian cycle? (student asked)

**Novice.** A delivery route that visits **every house exactly once** and returns to
the start. Named after William Rowan Hamilton. Wrong routes: visiting some houses
twice and others never; or looping forever around just 10 houses.

**Intermediate.** `order[]` is a shuffled permutation (0..n−1, each exactly once), so
the chain is `order[0] → order[1] → … → order[n−1] → order[0]`. The `% nslots`
**closes** the cycle, guaranteeing every slot is visited exactly once before any
repeat.

### Side-note 1.2b — What does "prefetcher defeated" mean? (student asked)

**Novice.** A prefetcher is hardware that guesses what you will read next and brings
it into cache early. **"Defeated"** means it cannot guess, so at load time the data
is *not* in cache and you pay the **real latency** — which is exactly what you want.
If the prefetcher wins, the staircase disappears.

**Expert.** Next-line, stride and stream prefetchers are all defeated by a random
chase. **But** Apple's M1 contains a **data memory-dependent prefetcher** (Augury,
[46]) that follows pointer-like values — and the chase is exactly that pattern. §2.4
states this honestly: the M1 curves are clean, so the effect is not large enough to
flatten the staircase — but that is an **observation, not a guarantee**.

**Question 1.2** — If instead of a proper cycle you stored *any* random slot's
address in each slot (addresses still random, prefetcher still defeated): (a) what
specifically goes wrong? (b) where on the curve would it show, and why?

**Student's answer:**
> What is a Hamiltonian cycle? What does "prefetcher defeated" mean?
> (a) Don't know. (b) I think the problem would show at large working sets.

**Verification — (b): correct ✔ / (a): taught**

**(b) is right.** The reason:

Without a proper cycle you build a **random functional graph**, in which the chase
falls into a **"ρ" (rho) shape** — a tail leading into a small cycle it never
escapes. Random functional graph theory: before repeating, you visit only
**≈ √(πn/2) ≈ √n distinct nodes**.

Concretely (M1, 128 B line):

| | Value |
|:---|:---|
| Intended working set | 16 MiB |
| Total slots (n) | 131,072 |
| Actually visited (√(πn/2)) | **~454 slots** |
| Actual memory touched | **~57 KiB** |

57 KiB fits inside the M1's **128 KiB L1** — so the measurement would report ~1.5 ns
(L1 speed) when 16 MiB should give ~9 ns or more.

The error therefore appears **only at large working sets**:

| WSS | Intended | Actual (√n) | Both fit in | Error |
|:---|:---|:---|:---|:---|
| 8 KiB | 8 KiB | ~1 KiB | both L1 | none |
| 16 MiB | 16 MiB | ~57 KiB | intended DRAM, actual L1 | **enormous** |

because √n grows far more slowly than n. **Curve shape:** it would rise for a while
then **flatten** — the DRAM plateau would never appear. And most dangerously, the
curve would look **plausible**: no crash, no error, just silently wrong. That is why
`% nslots` is not merely a modulo — it is a **correctness guarantee**.

### Concept 1.3 — Measuring a fine signal with a coarse clock

**Novice.** Your stopwatch shows only whole seconds, and the task takes 40 ms. Time
it once → "0 seconds", useless. Do it 1000 times → 41 seconds → divide → 41 ms. The
stopwatch is just as coarse; you **amortised** its coarseness.

**Intermediate.** Apple Silicon's timer runs at 24 MHz = **~41.7 ns/tick** (exactly
`125/3`), against a **1.53 ns** L1 hit — **27× coarser**. Timing one access yields 0
or 1 tick and nothing between. Solution: `DEFAULT_MIN_HOPS = 1 << 20`
(`wss/__init__.py:44`), then `(c1-c0)/hops` (`wss_probe.c:370`). 2²⁰ × 1.53 ns ≈ 1.6
ms ≈ 38,500 ticks, so the granularity's effect is 1/38,500 — sub-nanosecond effective
resolution.

**Expert.** The trick is valid only if the per-hop cost is **stationary** across the
window. If it drifts, you silently fold the drift into the estimate.

**Question 1.3** — (a) A sceptical examiner says: *"The clock is 41.7 ns; how can you
report 1.53 ns? That's cheating."* Convince them in one line. (b) What assumption does
amortisation require, and which design decision in the codebase protects it?

**Student's answer:**
> (a) I will increase the number of iterations, then divide by that number to find a
> 27× finer latency.
> (b) Per-hop cost should be stationary.

**Verification — (a): pass ✔ (mechanism right, framing needed) / (b): half pass ✔**

**(a)** The mechanism is right, but the examiner wants a *justification*. Reframe:
✗ "I measure one access to 1.53 ns precision."
✓ "I am **not** measuring one access — I measure the **total of a million accesses**,
and that total is large enough for the timer's coarseness to be negligible."

*Analogy:* You cannot measure one sheet of paper with a millimetre ruler. Stack 1000
sheets → 52 mm → divide → 0.052 mm per sheet. You did not improve the ruler; you
improved the **signal-to-resolution ratio**.

| | Value |
|:---|:---|
| Total time (2²⁰ × 1.53 ns) | 1,604,321 ns ≈ 38,500 ticks |
| Timer uncertainty | ±1 tick = ±41.7 ns |
| **Relative error on the total** | **±0.0026%** |

Key point: the hop count is an **exact integer**, so dividing by it introduces no new
uncertainty.

**(b)** The assumption is **exactly right** — per-hop cost must be stationary. There
are **three** protecting mechanisms, for three different threats:

| Threat | Where | Protection |
|:---|:---|:---|
| Cold-start transient (cold misses, TLB fill) | **within** the window | **Warm-up traversal** (`wss_probe.c:356`) — one full traversal before timing, so the start and end of the window cost the same. *The most direct protection.* |
| Random interference (OS interrupt, background process) | one window | **Minimum over 5 repeats** — interference can only *add* time, so the minimum discards disturbed windows |
| Thermal drift over ~3 minutes | **across** the sweep | **Shuffled size order** (`wss/__init__.py:93`) — in ascending order the largest sizes are always measured last, on the hottest die, and that rise *correlates with size*, producing a fake upward slope that looks like a cache boundary. Shuffling converts systematic bias into random noise. |

### Concept 1.4 — Fences (and a false premise in the brief)

> ⚠️ The project brief asked: *"why did we need hardware fences (lfence/mfence) and
> RDTSC?"* — **there is no `lfence`, `mfence` or `sfence` anywhere in the codebase.**
> Not one. And *why there isn't* is the most elegant design point in the probe. (This
> is Q1.5 in Part 3.)

**Novice.** A fence is a rule: *"finish everything on this side of the line before
starting anything on the other side."* You need it when work **can** be done out of
order. But consider: you open an envelope, and inside is **the address of the next
envelope**. You cannot open envelope 2 first — its address is inside envelope 1.
Ordering enforces **itself**; no rule is required.

**Intermediate.** What the code has is a **compiler barrier** (`wss_probe.c:121`):
`#define COMPILER_BARRIER() __asm__ __volatile__("" ::: "memory")` — empty assembly
plus a memory clobber. It stops the **compiler** moving loads across the timer reads,
and costs **zero cycles** at runtime (no instruction is emitted). Line 115 states the
reasoning: *"a hardware fence is unnecessary because the pointer chase is already
fully serialised by data dependencies."*

**Expert — three distinctions:**

| | Who reorders | When | Remedy |
|:---|:---|:---|:---|
| Compiler | build time | during compilation | `COMPILER_BARRIER()` |
| CPU | run time | during execution | data dependency (already free) |

1. **A compiler barrier is not a hardware fence.** Two different adversaries. The
   chase handles the CPU; the compiler still needs handling.
2. **`__rdtscp`, not `rdtsc`** (line 65). The extra `p` means "let prior instructions
   retire, then read the counter". Plain `rdtsc` would need an `lfence` beside it —
   **so the fence decision was made in the instruction selection.**
3. **ARM does use `isb`, but it is not a memory fence** (line 77):
   `asm volatile("isb; mrs %0, cntvct_el0" ...)`. `isb` is an **I**nstruction
   **S**ynchronization **B**arrier, preventing the counter read being speculated
   across the timed region. Different problem, different instrument.

**Question 1.4** — Suppose you timed **independent random loads** instead of a
pointer chain: `for (i...) sum += buf[idx[i]];` (addresses still random, prefetcher
still defeated). (a) What now goes wrong that a fence would be needed to fix? (b)
Would the measured latency rise or fall, and why? *(hint: MLP)*

**Student's answer:** _model answer — this one was not attempted live, so what follows
is the target standard rather than a record of a given response._

> (a) The chain breaks. In `sum += buf[idx[i]]` the address of load *n+1* comes from
> `idx[i]`, which is already in a register — it does **not** depend on the *result* of
> load *n*. Nothing serialises the loads any more, so the out-of-order engine issues
> as many as its miss-handling resources allow, and the second `get_ticks()` can be
> reached while loads are still in flight. A hardware fence (`lfence` on x86, `dsb` on
> ARM) before the closing timestamp would be needed to make the timer bracket
> *completion* rather than *issue*.
>
> (b) It would **fall**, sharply — by roughly the achieved memory-level parallelism.
> I would be measuring throughput per access, not load-to-use latency.

**Verification — (a): pass ✔ / (b): pass ✔ — this is the right answer, and the reason
it is right is the single most important idea in the probe.**

**(a)** Correct, and note *what kind* of failure it is. The pointer chase gives
**MLP = 1 by construction**: `p = (void **)(*p)` means load *n+1* cannot even have its
address computed until load *n* has returned data. The hardware is not being *asked*
to behave; it is physically unable to do otherwise. Break the dependency and that
guarantee evaporates:

| | Pointer chase | Independent loads |
|:---|:---|:---|
| Address of load *n+1* | **result** of load *n* | `idx[i]`, already known |
| Concurrent misses | 1 | limited by MSHRs / line-fill buffers (~10–20) |
| Ordering | enforced by data dependency | nothing enforces it |
| Fence needed? | **No** — free | **Yes**, and it perturbs the measurement |

The fence is also not a *fix*. It corrects where the timestamps land, but it cannot
un-overlap the loads **inside** the loop. To recover true latency you must serialise,
and the only zero-cost way to serialise is the data dependency. That is the whole
argument: the pointer chase is not merely "a way to defeat the prefetcher" — it is the
mechanism that pins MLP to 1.

**(b)** Right, and be ready to quantify it. Measured latency ≈ true latency ÷ MLP. A
core sustaining ~12 concurrent misses would report the M1's 130.43 ns DRAM plateau as
roughly **11 ns** — around L2 speed.

The damage is worst exactly where the project needs precision. MLP can only be
exploited when there are misses to overlap, so the compression grows with depth: L1
(already ~1 cycle, no misses to overlap) barely moves, while DRAM collapses. The
staircase does not merely shift down — it **flattens**, and the L2/L3/DRAM boundaries
the pipeline exists to find are compressed towards each other or lost entirely.

> **The one-line viva answer:** *"Independent loads measure memory **bandwidth**;
> dependent loads measure memory **latency**. My staircase is a latency curve, so the
> dependency is not optional — it is the definition of the quantity."*

This is also why `lat_mem_rd` in lmbench [9] chases pointers, and why the absence of
fences in `wss_probe.c` is a design result rather than an omission (Q1.5, Q1.6).

### Side-note V.1 — What are hwloc, CPUID leaf 4, and Intel MLC? (for the opening)

In one line each:

| Tool | What it does | Where its answer comes from |
|:---|:---|:---|
| **hwloc / lstopo** | Maps machine topology | **Asks** the OS |
| **CPUID leaf 4** | CPU describes itself | A **table burned into silicon** |
| **Intel MLC** | **Measures** latency/bandwidth | Measures — but **assumes the shape** |

**hwloc / lstopo** [27] — an open-source topology library; `lstopo` is its visualiser
(Machine → Package → L3 → L2 → L1 → Core). **It measures nothing; it reads:** Linux
`/sys/devices/system/cpu/cpu0/cache/`, macOS `sysctl`, Windows
`GetLogicalProcessorInformationEx` — **the same three interfaces `validation.py` uses
for ground truth.** The difference: hwloc stops there; this project uses them to
*check* a measurement.

**CPUID leaf 4** [28] — an x86 **instruction**. Put a leaf number in EAX, execute
`cpuid`, and the CPU fills registers (leaf 0 = vendor, leaf 1 = family/model, **leaf
4 = Deterministic Cache Parameters**). Iterate subleaves 0,1,2,3…; each returns one
level: type, level, line size, associativity (ways), sets.
`capacity = ways × partitions × line_size × sets`. **Two limitations:** (i) it is not
a measurement but the **manufacturer's burned-in table**; (ii) it is **x86-only** —
`cpuid` does not exist on ARM. ARM's `CLIDR_EL1` / `CCSIDR_EL1` are **EL1
(kernel)** registers, unreadable from user space and not exposed on Apple Silicon.
**So the "just use CPUID" objection fails outright on Apple Silicon.**

**Intel MLC** [29] — Intel's free tool, which genuinely **does measure**. Still not a
competitor: (i) **Intel-only**; (ii) it **assumes the hierarchy's shape** — you tell
it to measure L2 latency, which requires already knowing L2 exists and how large it
is. It measures **parameters**; this project discovers the **shape**.

**Chain of trust — the core of the argument:**

```
hwloc/lstopo → OS interface → firmware(ACPI)/CPUID → manufacturer's table
CPUID leaf 4 ──────────────────────────────────────→ manufacturer's table
Intel MLC    → measures ✓ ... but shape assumed + Intel-only
Auto-Echo    → measures ✓ ... discovers shape ✓ ... needs no table
```

Every existing tool's chain terminates at a table somebody wrote. That is precisely
what the opening line means.

**Killer example, from your own data.** The M1 has a ~8 MiB **System Level Cache**
that **no OS interface reports** — `sysctl` silent, hwloc silent, no CPUID on ARM. It
exists (reverse-engineered, [13]) and **appears** in §5.2's latency curve as a merged
mid-band with L2. This is why §4.3's "expected levels" rule excludes the SLC — it is
not OS-reported.

**Trap:** never call these tools "bad" — they are *more accurate* than Auto-Echo on
their supported machines. Correct framing: *"Each is more accurate than my tool on
the hardware it supports — that's precisely the point. I'm asking what remains
recoverable when none of them applies."*

### Side-note V.2 — Live proof on your own machine (`sysctl` output)

The student tried `lstopo` → `command not found` (hwloc is not installed by default
on macOS; `brew install hwloc`). But no install is needed — what hwloc *reads* on
macOS can be seen directly, and it proves the dissertation's core argument live.

**Actual output (Apple M1, this machine):**

```
hw.perflevel0.l1dcachesize: 131072      # 128 KiB — P-core
hw.perflevel0.l1icachesize: 196608      # 192 KiB
hw.perflevel0.l2cachesize:  12582912    # 12 MiB
hw.perflevel1.l1dcachesize: 65536       # 64 KiB — E-core
hw.perflevel1.l2cachesize:  4194304     # 4 MiB
hw.cacheconfig: 8 1 4 0 ...             # 8 cores, 1 per L1, 4 share L2
hw.cachelinesize: 128
hw.l1dcachesize: 65536                  # ⚠ generic = E-CORE value
hw.l2cachesize:  4194304                # ⚠ generic = E-CORE value

grep for SLC / "system level cache"  →  NOTHING. Not one entry.
```

**Finding 1 — the SLC is literally invisible.** The M1's ~8 MiB System Level Cache
exists in silicon (reverse-engineered, [13]) and macOS says **nothing** about it.
Chain of trust: `hwloc → sysctl → this output`. So **hwloc cannot show it either** —
it isn't in the source. Yet the probe sees its effect in the latency curve (§5.2).
*Viva line:* "I can demonstrate this on my own machine. The M1 has an 8 MiB SLC.
`sysctl` reports nothing about it, so `hwloc` cannot either. My probe sees its effect
in the latency curve. That is the gap this project addresses."

**Finding 2 — a heterogeneous-die trap the code avoids ✔.** The generic
`hw.l1dcachesize` returns 65536 (**E-core**) while the probe runs on a **P-core**
(131072). Using the generic key would score the detected 157.5 KiB against 64 KiB →
**+146% error** instead of +23%, invalidating the whole M1 validation.
`validation.py` explicitly reads `hw.perflevel0.*` — the correct decision.
*Viva line:* "On a heterogeneous die the generic `sysctl` keys report the efficiency
cluster. Since the probe runs on a performance core, using them would have scored a
P-core measurement against E-core ground truth."

**Finding 3 — `hw.cacheconfig: 8 1 4`** = 8 cores, **1 core per L1 (private)**, **4
cores share L2 (cluster-wide)**. This confirms the basis of §5.3.2's contention
argument: shared caches contend, private ones do not. (The first `hw.cachesize` value
of 3.4 GB is memory, not a cache.)

**Confirmed later by `lstopo` itself:**

```
Machine (8192MB total)
  Package L#0
    NUMANode L#0 (P#0 8192MB)
    L2 L#0 (4096KB)                        ← E-cluster
      L1d L#0-3 (64KB)  + Core L#0-3       ← CPUs 0–3 are EFFICIENCY cores
    L2 L#1 (12MB)                          ← P-cluster
      L1d L#4-7 (128KB) + Core L#4-7       ← CPUs 4–7 are PERFORMANCE cores
```

Every documented figure matches (L1d 128 KiB, L2 12 MiB, line 128 B, **no L3**). And
critically: **CPUs 0–3 are E-cores on this machine.** Had the probe naively pinned to
CPU 0 on macOS it would have measured the E-core. It uses a QoS hint instead, and the
recovered errors (+23.0% / +16.1% against P-core figures, versus +146% / +248%
against E-core figures) prove empirically that the bias worked. This evidence is now
recorded in the dissertation (§3.1 and Table 5).

### Side-note V.3 — Intel `lstopo` output, and what it settled

Run natively on Windows (`hwloc-win64-build-2.14.0`):

```
Machine (6928MB total) + Package L#0
  NUMANode L#0 (P#0 6928MB)
  L3 L#0 (20MB)
    L2 L#0 (1280KB) + L1d L#0 (48KB) + L1i L#0 (32KB) + Core L#0
      PU L#0 (P#0)                     ← SMT pair on one physical core
      PU L#1 (P#1)
    ... Cores L#1–L#5, identical                    ← six PERFORMANCE cores
    L2 L#6 (2048KB)                                 ← shared E-cluster L2
      L1d L#6 (32KB) + Core L#6 + PU L#12 (P#12)
      ... Cores L#7–L#9                             ← four EFFICIENCY cores
```

**1. Every documented figure confirmed.** L1d **48 KiB**, L2 **1280 KiB = 1.25 MiB**
per P-core, L3 **20 MiB** shared — exactly Table 4. Also confirms "6 performance + 4
efficiency cores".

**2. The pending question is answered: CPU 0 *is* a performance core on this Intel
part.** `Core L#0` carries the P-core caches (48 KiB L1d, 1280 KiB L2) and hosts
`P#0`/`P#1`. So `SetThreadAffinityMask(..., 1)` → logical CPU 0 → a P-core. The C
comment *"CPU 0 is a performance core on hybrid Intel"* is **verified, not assumed**.

**3. The two platforms number their cores in opposite orders — a genuinely
interesting asymmetry.**

| | CPUs 0–3 | Highest CPUs |
|:---|:---|:---|
| **Intel i5-13450HX** | **Performance** cores (P#0–P#11) | Efficiency (P#12–P#15) |
| **Apple M1** | **Efficiency** cores | Performance (4–7) |

So pinning to CPU 0 gives a P-core on Intel and an **E-core on the M1**. That is
exactly why the Apple path uses a performance-cluster QoS hint instead of an affinity
mask. *The pinning strategy is correct on both platforms, but for platform-specific
reasons rather than by one portable rule* — a good answer if asked "why doesn't the
probe just pin to core 0 everywhere?"

**4. SMT detail that strengthens §5.3.2.** P-cores carry SMT (`Core L#0` hosts `P#0`
*and* `P#1`); E-cores do not. The contention experiment pins workers to logical CPUs
2–9 = physical cores 1–4, leaving the probe's own physical core (`P#0` + `P#1`)
entirely idle. So the measured effect is **last-level-cache contention, not SMT
interference** within the probing core.

**5. ⚠️ An honest limit on the "incomplete table" argument.** On the Intel part
`lstopo` reports a **complete** hierarchy — L1d, L2, L3, memory, with no hidden tier.
There is no Intel equivalent of the M1's SLC. **So the incompleteness argument applies
to the M1 and *not* to the Intel machine.** What justifies measurement on the Intel
part is the *separate* finding that a documented 20 MiB L3 can be behaviourally
unreachable (§5.3). Do not over-generalise the SLC story to both machines — an
examiner who has seen this output will catch it.

*(Recorded in the dissertation as Table 5's `hwloc` column, plus three new paragraphs
in §5.1 and a precision fix in §5.3.2.)*

---

# Part 3 — Question Bank

## Module 1 — The C Probe (Pointer-Chasing)

**1.1** A colleague suggests rewriting the probe in Python with NumPy, arguing
that NumPy's inner loops are C anyway. Give the quantitative argument for why
this cannot work, using the L1 latency you actually measured and a realistic
figure for CPython bytecode dispatch.

> **Answer.** The argument is a **signal-to-instrument** argument, and it is lost
> before NumPy is even reached.
>
> **The arithmetic.** The signal is an L1 hit at **1.53 ns** (M1, §5.2). One CPython
> bytecode dispatch — fetch opcode, switch dispatch through the eval loop, unbox,
> `Py_INCREF`/`Py_DECREF`, re-box — costs **~30–100 ns**, and a single `a[i]` on a
> Python object involves several. Taking the *most* generous figure:
>
> | | Cost | Ratio to signal |
> |:---|---:|---:|
> | L1 hit (the thing being measured) | 1.53 ns | 1× |
> | One optimistic bytecode dispatch | ~30 ns | **~20×** |
> | Realistic per-iteration Python cost | ~100 ns | **~65×** |
>
> The instrument is 20–65× more expensive than the signal. Worse, it is *not
> constant*: the interpreter's own cost varies with refcount traffic and allocator
> state, so it does not even subtract cleanly. Every plateau would be buried under a
> variable ~100 ns pedestal, and the L1/L2 step — 1.53 → 9.19 ns on the M1, a
> difference of **7.7 ns** — would be far inside the noise.
>
> **Why NumPy specifically does not rescue it.** Two independent reasons:
>
> 1. **Wrong access pattern.** NumPy is fast on *vectorised operations over
>    contiguous memory with predictable strides* — precisely the pattern this probe
>    must **avoid**, because it is what the stride prefetcher was built to serve.
>    Fancy indexing `a[idx]` is a **gather**: NumPy issues those loads
>    *independently*, so MLP ≫ 1 and the measurement becomes bandwidth, not latency
>    (see Q1.4 in Part 2). NumPy gives you exactly the wrong thing, quickly.
> 2. **The dependency cannot be expressed.** "Load, wait for the result, use that
>    result as the next address" is inherently serial. There is no vectorised
>    formulation — the only way to write it is a Python-level loop, which returns
>    you to the interpreter overhead above.
>
> **The framing that wins the mark:** *"The timed region must contain nothing but
> the loads. In C the loop body compiles to a single `ldr` on ARM / `mov` on x86. In
> Python the loop body is the interpreter — I would be measuring CPython, not the
> memory hierarchy."*

**1.2** The probe links slots into a *single Hamiltonian cycle* rather than a
random graph of pointers. What specific failure occurs if you build a random
graph instead, and at which end of the working-set range would you notice it?

> **Answer.** A random graph makes the **effective working set collapse to
> O(√n)**, so the probe would silently measure a far smaller region than it
> allocated.
>
> **The mechanism.** If each slot points at a *uniformly random* slot, the result is
> a **random functional graph**, not a permutation. Such a graph decomposes into
> "rho" shapes — a tail running into a cycle — and for *n* nodes the expected cycle
> length is **Θ(√n)**, not *n*. A chase entering that cycle stays in it forever.
>
> **The numbers.** At the top of the sweep, 512 MiB at a 128 B stride is
> *n* ≈ 4.2 million slots. Expected cycle ≈ √(4.2 × 10⁶) ≈ **2,000 slots** ≈ 256 KiB
> of touched memory — against 512 MiB allocated, a factor of **2,000× too small**.
> That fits comfortably in the M1's L2.
>
> **What the curve would look like.** Latency would rise normally out of L1 and then
> **stop rising** — flattening at whatever level the √n footprint happens to fit
> into, and never reaching DRAM. You would conclude the machine has an enormous
> last-level cache and no main memory. The staircase would lose its deepest and most
> important step.
>
> **Where you would notice it: the large end, and only there.** At small working-set
> sizes the whole buffer fits in L1 regardless of how it is linked, so a corrupted
> cycle is invisible; the bug appears exactly where the interesting caches are. This
> is what makes it dangerous — a smoke test on a small buffer passes.
>
> **What the Hamiltonian cycle guarantees.** A Fisher–Yates permutation [5] (seeded
> xorshift64, so every sweep is reproducible) visits **every slot exactly once per
> traversal**, so *effective WSS ≡ allocated WSS* by construction. It has a second
> benefit stated in §3.1: building the cycle **writes every slot**, which pre-faults
> every page before timing begins, keeping page-fault cost out of the timed window.

**1.3** Randomisation defeats the stride prefetcher. Does it defeat *all*
prefetchers? Discuss with reference to Apple's data memory-dependent prefetcher
(Augury, [46]) and explain why your M1 results are still defensible.

> **Answer.** **No — and this is a genuine, named threat to the method on Apple
> Silicon specifically.** The honest answer scores better than a confident one.
>
> **What randomisation does defeat.** Next-line, stream and stride engines [44],
> [45] all work by detecting a *constant delta* between successive addresses. A
> random permutation has no such delta, so they cannot run ahead. This is the
> standard defence and the one lmbench relies on.
>
> **What it does not defeat.** A **data memory-dependent prefetcher (DMP)** does not
> look at the address *sequence* — it inspects the *values being loaded*, identifies
> ones that look like pointers, and prefetches them. Vicarte et al. (**Augury**,
> [46]) demonstrated exactly such a unit on the Apple M1; Chen et al. (**GoFetch**,
> [47]) later weaponised it against constant-time cryptography.
>
> **Why this is uncomfortable rather than academic:** a pointer chase is *precisely*
> the access pattern a DMP targets — the loaded value **is** the next address. The
> probe's core assumption (accesses are serialised and unprefetchable) is therefore
> under direct threat on the very machine that produced the M1 results.
>
> **Why the results are still defensible — four points, strongest first:**
>
> 1. **The staircase is itself the evidence.** If the DMP were running ahead
>    effectively, deep latencies would be *depressed* and the plateaus would blur.
>    The M1 curves (§5.2, Fig. 5) show clean, well-separated plateaus with a sharp L1
>    knee and a DRAM plateau at **130.43 ns** — a value consistent with an
>    un-prefetched DRAM access. A working DMP would have pulled that down markedly.
> 2. **It validated.** Both OS-documented caches were recovered within the
>    factor-of-two tolerance (2/2, 100 % recall), which a substantially prefetched
>    curve would not achieve.
> 3. **The assumption is tested, not assumed.** The claim is empirical — I can point
>    at the measured curve rather than at a datasheet.
> 4. **The limit is stated, not hidden.** §5.5 records this explicitly as an
>    empirical observation *on one part*, not a guarantee. The DMP is documented to
>    require an observable pattern and to have bounded depth, but I do not rely on
>    that.
>
> **The sentence to have ready:** *"Randomisation defeats stride prefetchers by
> construction and appears to defeat the M1's DMP in practice — but 'appears to' is
> the honest verb, and §5.5 says so."*

**1.4** Explain why `stride` must be at least `sizeof(void *)`, and what class of
bug the guard at `wss_probe.c:281` prevents. Why is this a security-relevant
check and not merely a correctness one?

> **Answer.** The guard prevents an **out-of-bounds heap write** (CWE-787) reachable
> from pure Python.
>
> **The mechanism.** Cycle construction stores a pointer into each slot:
>
> ```c
> char *slot = base + order[k] * (size_t)stride;
> *(void **)slot = (void *)next;          /* an 8-byte store */
> ```
>
> The allocation is sized `alloc_bytes = nslots * stride` where
> `nslots = size_bytes / stride`. The **last** slot begins at `(nslots-1) * stride`,
> and an 8-byte store there ends at `(nslots-1) * stride + 8`. If
> `stride < sizeof(void *)`, that end address exceeds `alloc_bytes` — the final store
> **runs off the end of the buffer**. The comment at line 280 says exactly this: *"a
> sub-pointer stride would overflow the last slot's 8-byte store."*
>
> A sub-pointer stride is also incoherent on its own terms: consecutive slots would
> **overlap**, so writing slot *k*'s pointer would corrupt slot *k+1*'s, and the
> chase would follow a mangled graph.
>
> **Why it is a security check.** `measure_wss` is a **CPython C extension**, and
> `stride` arrives from Python through `PyArg_ParseTuple` (line 271). It is therefore
> **untrusted input crossing a language boundary** — from a memory-safe language into
> one with no bounds checking. Without the guard, ordinary Python code
> (`measure_wss(4096, 1, ...)`) triggers an out-of-bounds write in native code, with
> all the usual consequences: heap-metadata corruption, a crash, or in the worst case
> a controllable write primitive. Memory-safety invariants that C *assumes* must be
> **enforced at the boundary**, because the caller's language does not enforce them.
>
> Note the guard's placement is deliberate: it sits with the other argument
> validation (line 275 checks `stride <= 0`, `size_bytes < stride`, `hops <= 0`,
> `repeats <= 0`) **before** any allocation or arithmetic — validate first, then act.

**1.5** *"The probe uses `lfence` and `mfence` to stop the out-of-order engine
reordering loads across the timer reads."* Evaluate this statement.

> **Answer.** **The statement is false on the facts, and the reason it is false is
> the most elegant point in the probe.**
>
> **Factually:** there is no `lfence`, `mfence` or `sfence` anywhere in the
> codebase — `grep` returns nothing. What line 361/367 actually places around the
> timed loop is a **compiler barrier**, `COMPILER_BARRIER()`.
>
> **Why no hardware fence is needed.** A fence exists to impose ordering where the
> hardware is otherwise free to reorder. In this loop the hardware has **no such
> freedom**:
>
> ```c
> for (Py_ssize_t h = 0; h < hops; h++) {
>     p = (void **)(*p);      /* the address of the next load IS this load's result */
> }
> ```
>
> The out-of-order engine cannot issue load *n+1* early, because it does not know
> *where to load from* until load *n* returns. The chase is **fully serialised by
> data dependency** — the comment at line 115 states precisely this. There is nothing
> for a fence to prevent.
>
> **Why adding one would be actively harmful.** An `lfence` inside the loop would add
> real cycles to **every one of the 2²⁰ hops**, and those cycles land *inside the
> timed window* — contaminating the very quantity being measured. You would be
> reporting "L1 latency plus fence overhead" and calling it L1 latency.
>
> **Where partial credit is due.** The ARM path *does* execute a barrier — `isb`
> before `mrs cntvct_el0` (line 77) — but that is an **instruction**-synchronisation
> barrier guarding the *counter read*, not a memory fence guarding the loads (Q1.8).
> And on x86 the ordering guarantee is bought by choosing `__rdtscp` over `rdtsc`
> (Q1.7). So the *fence decision was made twice* — once in the access pattern, once
> in the instruction selection — and neither produced an `lfence`.
>
> **The reframing to offer:** *"The absence of fences is not an oversight; it is the
> consequence of choosing an access pattern that enforces its own ordering — at zero
> cost."*

**1.6** Distinguish a **compiler barrier** from a **hardware fence**. Which does
`wss_probe.c` use, what does it compile to, and why is the other one unnecessary
*here* when it is mandatory in most microbenchmarks?

> **Answer.** They defeat **two different adversaries acting at two different
> times**, and conflating them is the classic error.
>
> | | Adversary | Acts at | Remedy | Runtime cost |
> |:---|:---|:---|:---|:---|
> | **Compiler barrier** | the optimiser | **build** time | `COMPILER_BARRIER()` | **zero** |
> | **Hardware fence** | the out-of-order engine | **run** time | `lfence` / `dsb` | real cycles |
>
> **Which the code uses:** the compiler barrier only (lines 119–121):
>
> ```c
> #if defined(_MSC_VER)
> #define COMPILER_BARRIER() _ReadWriteBarrier()
> #else
> #define COMPILER_BARRIER() __asm__ __volatile__("" ::: "memory")
> #endif
> ```
>
> **What it compiles to: nothing.** The asm template is the empty string, so **no
> instruction is emitted**. Its entire effect is on the optimiser: the `"memory"`
> clobber declares that this statement may read or write any memory, so GCC/Clang
> must not move memory operations across it and must materialise pending stores.
> Zero instructions, zero cycles, full ordering — against the compiler.
>
> **Why the hardware fence is unnecessary *here*:** the data dependency has already
> serialised the CPU (Q1.5). The probe gets CPU ordering **for free from its access
> pattern** and therefore only has to pay for compiler ordering — which is also free.
>
> **Why it is mandatory in most microbenchmarks:** the typical benchmark times
> independent work — independent loads, stores, or an arithmetic kernel — where no
> dependency chain exists. There the CPU genuinely *can* overlap the timed work with
> the timer reads, so a real fence is the only way to make the timestamps bracket
> completion. (This is exactly the scenario of Q1.4 in Part 2.)
>
> **The trap to avoid:** do **not** conclude "so the barrier is unnecessary too". The
> compiler barrier is **mandatory**. Without it, `-O3` is free to hoist the entire
> chase out of the timed region, or delete it outright (Q1.9). The CPU is handled;
> the compiler still is not.

**1.7** Why `__rdtscp` rather than `rdtsc`? What does the extra `p` buy you, and
what would you have to add alongside `rdtsc` to get the same guarantee?

> **Answer.** Because `rdtsc` is **not serialising**, and `rdtscp` is *partially*
> serialising.
>
> **The problem with `rdtsc`.** It is an ordinary instruction to the out-of-order
> engine, which may execute it **before preceding instructions have retired**. The
> timestamp can therefore be taken *too early*, so `c1 - c0` under-reports the true
> elapsed time — the measurement is biased **fast**, in the direction that flatters
> the result and is hardest to notice.
>
> **What the `p` buys.** `rdtscp` waits until **all previous instructions have
> retired** before reading the counter. (It also returns the processor ID, which is
> why the code passes `&aux` at line 65 — a useful side benefit, since a changed ID
> would reveal a mid-measurement core migration.)
>
> **What you would add alongside plain `rdtsc`:**
>
> | Idiom | Effect | Cost |
> |:---|:---|:---|
> | `lfence; rdtsc` | drains prior *loads*; the modern idiom | cheap |
> | `cpuid; rdtsc` | fully serialising; the classic idiom | heavy, **variable** latency, clobbers `eax/ebx/ecx/edx` |
>
> `cpuid` is the historically standard answer but a poor one for a timer: its own
> latency is variable, so it injects noise into the quantity being measured.
>
> **The point that connects this to Q1.5:** choosing `__rdtscp` **is** choosing not
> to need an `lfence` there. When an examiner asks "where are your fences?", the
> answer is that one of them was **subsumed into the instruction selection** and the
> other into the access pattern.
>
> **Precision worth volunteering:** `rdtscp` orders *prior* instructions but does not
> stop *later* ones being hoisted above it. Strictly, a trailing `lfence` would close
> that. The probe does not need one because the closing `COMPILER_BARRIER()` and the
> final `g_sink = (void *)p` (line 368) force the dependent chain to have completed
> before anything observable follows.

**1.8** The ARM path executes `isb` before `mrs cntvct_el0`. Is that a memory
fence? If not, what is it, and what would go wrong without it?

> **Answer.** **No, it is not a memory fence.** Naming it correctly is the mark.
>
> ```c
> asm volatile("isb; mrs %0, cntvct_el0" : "=r"(v) :: "memory");
> ```
>
> **What `isb` is:** an **I**nstruction **S**ynchronisation **B**arrier. It flushes
> the pipeline and guarantees that everything before it is complete before anything
> after it is fetched and executed. It orders the **instruction stream**.
>
> **What ARM's actual memory barriers are:** `dmb` (Data Memory Barrier — orders
> memory accesses) and `dsb` (Data Synchronisation Barrier — waits for them to
> complete). `isb` is **neither**.
>
> **What goes wrong without it.** `mrs x0, cntvct_el0` reads the virtual counter, and
> the ARM architecture explicitly permits the CPU to execute that read
> **speculatively and early** — hoisting it above the code you intend to bracket. The
> timestamps would then not delimit the loop: `c0` could be sampled after the loop
> had begun, or `c1` before it finished. Symptoms are noisy deltas and occasionally
> **impossibly small** ones. The ARM Architecture Reference Manual recommends `isb`
> around counter reads for exactly this reason.
>
> **The instructive contrast with x86:**
>
> | | Ordering the *counter read* | Ordering the *loads* |
> |:---|:---|:---|
> | x86 | built into `__rdtscp` (retire-then-read) | data dependency |
> | ARM | **explicit `isb`** — `mrs` has no such semantics | data dependency |
>
> Same problem, different instrument, because the two ISAs put the guarantee in
> different places. The `"memory"` clobber on the asm statement additionally stops
> the *compiler* moving accesses across the read — the compiler-barrier concern of
> Q1.6, handled inline here.

**1.9** Explain the difference between `void *volatile g_sink` and
`volatile void *g_sink`. Which does the code use, what does `-O3` do if you get
it wrong, and how would you *detect* that you had got it wrong from the output
alone?

> **Answer.** This is the most dangerous line in the file, because getting it wrong
> produces **clean, plausible, physically impossible data** instead of a crash.
>
> **The distinction — read the declaration right-to-left from the identifier:**
>
> | Declaration | Reads as | What is volatile |
> |:---|:---|:---|
> | `void *volatile g_sink` | "`g_sink` is a **volatile pointer** to void" | the **pointer object itself** |
> | `volatile void *g_sink` | "`g_sink` is a pointer to **volatile void**" | only the **pointee** |
>
> **Which the code uses:** `static void *volatile g_sink;` (line 129) — the volatile
> *pointer*. Lines 125–128 document the trap explicitly.
>
> **Why it must be that one.** Because `g_sink` is volatile, every store
> `g_sink = (void *)p` is an **observable side effect** the compiler is obliged to
> emit. Emitting it requires the value of `p`. Producing `p` requires the whole
> dependent chase. The volatile store is what **anchors the loop to reality**.
>
> **What `-O3` does if you write `volatile void *` instead.** The pointer variable is
> then an ordinary non-volatile static, written but never read:
>
> 1. The store `g_sink = p` is **dead** → dead-store elimination removes it.
> 2. With the store gone, `p` is unused → the loop `for (h...) p = *p;` computes
>    nothing observable.
> 3. **Dead-code elimination deletes the entire measured loop.** GCC is particularly
>    willing to do this.
>
> You are then timing an empty region between two `get_ticks()` calls.
>
> **How to detect it from the output alone — three independent signatures:**
>
> 1. **Physically impossible latency.** Reported values near **~0 ns**. Anything
>    below roughly 0.3 ns/hop is beneath the reciprocal-throughput floor of a single
>    load on any real core — no machine can beat it, so the loop cannot be running.
> 2. **A staircase with no steps.** Latency **flat and independent of working-set
>    size**: the same figure at 4 KiB as at 512 MiB. The entire phenomenon the probe
>    exists to observe would have vanished, which is far more diagnostic than the
>    absolute value.
> 3. **Invariance across machines.** The number would not change between the M1 and
>    the Intel machine, because it reflects loop overhead rather than any hardware.
>
> **The framing:** *"A crash tells you something is wrong. This bug tells you
> nothing — it hands you a beautiful flat line. That is why the declaration carries a
> four-line comment rather than none."*

**1.10** The timer on Apple Silicon ticks every ~41.7 ns; you report L1 hits of
~1.53 ns. Explain how measuring something 27× smaller than your clock's
resolution is legitimate, and state the assumption that makes it valid.

> **Answer.** The premise contains a hidden false assumption: **I never measure a
> single access.** Correct that and the objection dissolves.
>
> **What is actually timed.** One timed window contains
> `DEFAULT_MIN_HOPS = 1 << 20` = **1,048,576 hops** (`wss/__init__.py:44`), and the
> per-access figure is `(c1 - c0) / hops` (`wss_probe.c:370`).
>
> | | Value |
> |:---|---:|
> | Total timed interval (2²⁰ × 1.53 ns) | 1,604,321 ns ≈ **1.6 ms** |
> | In ticks of a 41.7 ns clock | ≈ **38,500 ticks** |
> | Quantisation uncertainty | ±1 tick = ±41.7 ns |
> | **Relative error on the total** | **±0.0026 %** |
>
> **Why the division adds nothing.** `hops` is an **exact integer** chosen by the
> program, not a measured quantity. Dividing a measurement with ±0.0026 % error by an
> exact constant leaves ±0.0026 % error. No precision is invented.
>
> **The analogy for the examiner.** You cannot measure one sheet of paper with a
> millimetre ruler. Stack 1,000 sheets, measure 52 mm, divide → 0.052 mm per sheet.
> You did not improve the ruler; you improved the **signal-to-resolution ratio**.
>
> **The assumption that makes it valid: per-hop cost must be *stationary* across the
> window.** Amortisation reports a mean; if the cost drifts within the window, the
> drift is silently folded into that mean and is invisible in the output. Three
> mechanisms protect it, against three distinct threats:
>
> | Threat | Scope | Protection |
> |:---|:---|:---|
> | Cold-start transient (compulsory misses, TLB fill) | **within** a window | **Warm-up traversal** (`wss_probe.c:356`) — one full pass before timing, so start and end of the window cost the same |
> | Random interference (interrupt, background process) | one window | **Minimum over 5 repeats** — interference only *adds* time, so the minimum discards disturbed windows |
> | Thermal / DVFS drift over the ~3-minute sweep | **across** the sweep | **Seed-shuffled size order** (`wss/__init__.py:93`) — see Q1.11 |
>
> **The one-line answer:** *"I am not claiming 1.53 ns resolution on a single event.
> I am claiming 0.0026 % resolution on a 1.6 ms interval, then dividing by an exact
> integer."*

**1.11** Sweep order is seed-shuffled (`wss/__init__.py:93`) rather than
ascending. What systematic bias does this remove, and what would the corrupted
staircase have looked like?

> **Answer.** It removes the **confounding of working-set size with elapsed time**.
>
> **The bias.** A full sweep takes ~3 minutes. Over that period the die heats,
> DVFS may lower the clock, and thermal throttling may engage — so **later
> measurements are taken on a slower machine**. In ascending order, "later" and
> "larger" are *perfectly correlated*. Drift caused purely by time therefore appears
> as latency that **increases monotonically with working-set size** — which is
> precisely the signature of a real cache boundary. The confound is not noise; it is
> a systematic effect wearing the costume of the signal.
>
> **What the corrupted staircase would look like.** Two failure modes, both
> plausible enough to be believed:
>
> 1. **A spurious extra step** at the large end, read as a deeper cache level that
>    does not exist — a false positive, which would damage the precision metric.
> 2. **An inflated DRAM plateau** — the true plateau tilted upward, so the reported
>    DRAM latency is a hardware figure contaminated with thermal history.
>
> **Why it is worse than ordinary noise:** it is **reproducible**. Repeating the
> sweep in the same ascending order reproduces the same false step, so the usual
> defence — "run it again and see if it persists" — actively *confirms* the artefact.
>
> **What shuffling achieves.** It does not remove drift; it **decorrelates drift from
> size**, converting systematic bias into random noise. Noise is then exposed by the
> min–max band across sweeps, whereas bias would not have been. The permutation is
> drawn from `np.random.default_rng(seed)` with a fixed default seed (42), so the
> order is **randomised but reproducible**, and results are sorted by size for output.
>
> This is the experimental-design point of the probe: *randomise the assignment order
> so that a nuisance variable cannot masquerade as the treatment effect.*

**1.12** The probe reports the **minimum** over five repeats. Justify this against
the obvious alternative (the mean). What does the minimum hide, and where in the
dissertation is that cost acknowledged?

> **Answer.** The justification is that measurement error here is **one-sided**.
>
> **Why the minimum.** For a microbenchmark, every source of interference — a timer
> interrupt, a context switch, a competing thread, an SMT sibling, a migration —
> can only **add** time. Nothing makes a load complete faster than the hardware
> permits. The observed value is therefore *true latency + non-negative noise*, so
> the **minimum is the best estimator of the underlying floor**, and it converges to
> it as repeats increase. Standard lmbench practice [9].
>
> **Why not the mean.** The mean estimates "latency on this machine under whatever
> system noise happened during this run" — a property of the *environment*, not of
> the *hardware*, and not reproducible across machines or days. With one-sided
> contamination the mean is biased upward by construction, and a single 10 ms
> scheduler event across five repeats moves it substantially.
>
> **What the minimum hides: variability.** A lower envelope says nothing about how
> often the machine is disturbed, or how it behaves under contention. Two machines
> with identical minima can differ sharply in practice. §3.1 (step 5) and §5.5
> acknowledge this, which is why the reported figures are **never quoted bare** —
> they carry a **min–max band across independent sweeps**.
>
> **The point worth volunteering, because it shows estimator-level understanding:**
>
> > The minimum is the right statistic for a **latency** and the **wrong** statistic
> > for a **boundary**.
>
> §5.3 documents this concretely. Detecting on the *aggregate* minimum-over-sweeps
> curve pulls the Intel L3 knee inward to **13.9 MiB (−30.4 %)**, whereas **9 of the
> 10 individual sweeps put it at 19.7 MiB (−1.5 %)**. A lower envelope biases a
> *knee* inward, because in the noisy L3→DRAM transition the minimum systematically
> favours the faster, smaller-looking side. The correction was to detect **per sweep**
> and take the **median across sweeps** (`scripts/capacity_ci.py`) — the minimum
> remains correct for the latency column, and the two must not be conflated.
>
> Volunteering that you *found and fixed* this is worth more than defending the
> minimum in the abstract: it shows the estimator was interrogated, not assumed.

**1.13** Runtime calibration measures the tick rate against the OS monotonic
clock. Why is this *more* correct than reading the nominal CPU frequency from
`/proc/cpuinfo`, as the reference paper does — even on a machine where the TSC is
invariant?

> **Answer.** Three independent reasons, and the third is the decisive one because I
> have a **measured counterexample**.
>
> **1. Portability.** `/proc/cpuinfo` is Linux-only; the paper itself concedes this
> [1]. Auto-Echo runs on macOS and Windows, where the file does not exist. Any
> approach that starts by parsing it cannot make the cross-platform claim.
>
> **2. It reads the wrong quantity.** The `cpu MHz` field reports the **current core
> clock**, which is turbo- and DVFS-scaled and changes moment to moment. But
> `rdtsc`/`cntvct` advance at the **invariant** reference rate, which is deliberately
> *decoupled* from core frequency — that decoupling is exactly what makes the counter
> usable as a timebase. Applying a core-clock figure to an invariant-TSC counter is a
> **category error**: two different clocks.
>
> **3. Even on an invariant TSC, the nominal figure need not equal the tick rate.**
> This is the counterexample. On the i5-13450HX:
>
> | | Value |
> |:---|:---|
> | Windows advertises (P-core **base** clock) | **2.40 GHz** |
> | Runtime calibration measures (invariant TSC) | **0.383 ns/tick = 2.61 GHz** |
> | **Discrepancy** | **8.8 %** |
>
> Both figures are correct; they describe different clocks. Had the framework taken
> the advertised 2.40 GHz, **every latency in §5.3 would be inflated by 8.8 %**:
>
> | Level | Reported | Would have been |
> |:---|---:|---:|
> | L1 | 1.57 ns | 1.71 ns |
> | L3 | 20.81 ns | 22.64 ns |
>
> **Why that error would have been undetectable.** Detected **capacities** are
> working-set sizes and **never pass through the tick conversion**, so they would be
> untouched — the validation against OS ground truth would still pass at 100 %
> recall. The error would sit **entirely in the latency column**, where no internal
> consistency check could expose it, and where a plausible-looking wrong number is
> considerably more dangerous than an obviously wrong one.
>
> **How calibration works.** `calibrate()` counts hardware ticks over **~50 ms** of
> the OS monotonic clock (`clock_gettime` on POSIX, `QueryPerformanceCounter` on
> Windows) and divides. It **measures** the real rate rather than assuming one, needs
> no configuration, and is correct on any platform. On Apple Silicon the exact
> rational from `mach_timebase_info` (125/3 ≈ 41.667 ns) is used directly; an
> independent calibration run reproduced that value to four significant figures,
> confirming the mechanism the x86/Windows paths rely on.
>
> **The framing:** *"Runtime calibration is not a portability convenience — it is a
> correctness requirement, and my own Intel machine supplies the 8.8 % counterexample
> that proves it."*

---

## Module 2 — The ML Pipeline (Change-Point & Clustering)

**2.1** *"The productive pipeline uses PELT to detect the cache boundaries."*
Evaluate this statement, and explain what PELT is actually used for in this
project.

> **Answer.** **False as stated, and the correction is the design's central move.**
>
> **What the productive path actually does** (`analysis.py:248`):
>
> ```python
> k, _ = cluster_level_count(curve, max_k=kmax, algorithm="kmeans")
> return rpt.Dynp(model="l2", min_size=min_size).fit(signal).predict(n_bkps=k - 1)
> ```
>
> `Dynp` — dynamic programming — is asked for **exactly `k − 1` breakpoints**, where
> `k` came from the clustering stage. It is **count-constrained** and therefore
> **penalty-free**.
>
> **Why that matters.** PELT [6] takes a **penalty** parameter: raise it and you get
> fewer segments, lower it and you get more. A penalty is a **hand-tuned threshold in
> disguise**, and the project's headline claim is that the pipeline is
> *zero-configuration and threshold-free*. Had PELT chosen the boundaries, that claim
> would be false — the reported level count would be a consequence of a number the
> author picked.
>
> **Where PELT is genuinely used:** as a **sensitivity instrument**, not a producer of
> results. `penalty_sensitivity()` sweeps the penalty across 1.0 – 10.0 and reports how
> the recovered count varies (Tables 5 and 10). On the Intel huge-page run the count is
> **4 at every penalty from 1.0 to 10.0** — evidence that the segmentation is not
> balanced on a knife-edge. The `--penalty` CLI flag honours an explicit value for
> exactly this diagnostic.
>
> **The division of labour to state crisply:**
>
> | Stage | Tool | Chooses |
> |:---|:---|:---|
> | Count the levels | K-Means + Silhouette | **how many** |
> | Localise the boundaries | `Dynp`, given that count | **where** |
> | Sensitivity check only | PELT, penalty swept | *nothing reported* |
>
> **The trap:** if you concede PELT is productive, the examiner's next question is
> "so what penalty did you choose, and why not a different one?" — and there is no
> good answer to it. The correct answer is that the question does not arise.

**2.2** State the contiguity lemma for 1-D *k*-means and prove it in two or three
lines. Why does it collapse the search space from a Stirling number to a binomial
coefficient?

> **Answer.**
>
> **Lemma.** For points on the real line, every optimal *k*-means partition is
> **contiguous in sorted order**: no cluster's convex hull contains a point assigned
> to another cluster.
>
> **Proof (by exchange).** Suppose not. Then there exist $x_a < x_b < x_c$ with
> $x_a, x_c \in C_1$ and $x_b \in C_2$. Since $x_b$ lies between two members of
> $C_1$, it lies within $C_1$'s span, and because $C_1$'s centroid $\mu_1$ is a convex
> combination of its members, $\mu_1$ also lies in $[x_a, x_c]$. Moving $x_b$ from
> $C_2$ to $C_1$ changes the objective by
> $(x_b-\mu_1)^2 - (x_b-\mu_2)^2$ plus the (non-positive) effect of recentring both
> clusters. Because the assignment step of *k*-means assigns each point to its
> **nearest** centroid at optimum, and $\mu_1$ is nearer to $x_b$ than $\mu_2$
> whenever $x_b$ separates two $C_1$ members while $\mu_2$ lies outside $[x_a,x_c]$,
> the exchange **strictly decreases** the within-cluster sum of squares. So the
> assumed partition was not optimal. ∎
>
> **The combinatorial collapse.** Without the lemma, an optimal partition could be
> *any* partition of $n$ items into $k$ non-empty blocks — a **Stirling number of the
> second kind** $S(n,k)$, which grows super-exponentially ($k^n/k!$ to leading order).
> With it, a partition is fully determined by **where you cut the sorted sequence**,
> so it is a choice of $k-1$ cut positions from $n-1$ gaps:
>
> $$S(n,k) \;\longrightarrow\; \binom{n-1}{k-1}$$
>
> For the Intel curve ($n = 202$, $k = 4$): $S(202,4) \approx 10^{119}$ against
> $\binom{201}{3} = 1{,}313{,}400$. And the binomial structure is not merely smaller —
> it has **optimal substructure**, so DP solves it exactly without enumerating it at
> all.
>
> **The framing:** *"One-dimensionality is not a simplification I assumed; it is a
> property of the data — latency is a scalar — and the lemma converts it into an
> exactness guarantee."*

**2.3** Given that lemma, explain the dynamic-programming recurrence in
`_exact_1d_kmeans`. What do the prefix-sum arrays `cs` and `cs2` buy you, and
what would the complexity be without them?

> **Answer.**
>
> **The recurrence.** Let $D[c][j]$ be the minimal within-cluster sum of squares for
> partitioning the first $j$ sorted points into $c$ clusters, and $w(i,j)$ the SSE of
> the single segment $x_i \dots x_{j-1}$. By the contiguity lemma the last cluster
> must be a **suffix** $x_i \dots x_{j-1}$, so:
>
> $$D[c][j] \;=\; \min_{c-1 \le i < j} \Big( D[c-1][i] \;+\; w(i,j) \Big),
> \qquad D[0][0] = 0$$
>
> In the code this is the inner loop, vectorised over all candidate splits $i$ at once:
>
> ```python
> seg  = cs2[j] - cs2[i] - (s * s) / m        # SSE of xs[i:j], O(1) per candidate
> vals = cost[c - 1, i] + np.maximum(seg, 0.0)
> cost[c, j], split[c, j] = vals[best], i[best]
> ```
>
> `split` records the arg-min so the assignment is recovered by **backtracking** from
> $D[k][n]$, and one fill of the table yields **every** $k$ from 1 to `kmax` — which is
> why the whole model-selection scan costs a single pass rather than one run per $k$.
>
> **What the prefix sums buy.** $w(i,j)$ is computed from the identity
>
> $$\mathrm{SSE}(i,j) \;=\; \sum x^2 \;-\; \frac{\left(\sum x\right)^2}{j-i}$$
>
> With `cs` (prefix sums of $x$) and `cs2` (prefix sums of $x^2$), both sums are a
> **single subtraction**, so $w(i,j)$ is **$O(1)$** instead of $O(j-i)$.
>
> | | Cost of $w(i,j)$ | Total |
> |:---|:---|:---|
> | With prefix sums | $O(1)$ | **$O(k n^2)$** |
> | Without | $O(n)$ | $O(k n^3)$ |
>
> At $n = 202$, $k_{\max} = 8$: ~$3\times10^5$ operations versus ~$6\times10^7$ — the
> difference between instant and noticeable, and the reason the exact solver is
> affordable enough to be the *default* rather than an opt-in.
>
> **One implementation detail worth volunteering:** `np.maximum(seg, 0.0)` clamps the
> segment cost at zero. The identity above is algebraically non-negative, but in
> floating point a near-zero-variance segment (an L1 plateau, where every point is
> almost identical) can produce a **small negative** value through catastrophic
> cancellation. Un-clamped, that would make the DP prefer spurious extra clusters
> inside a flat plateau — a numerical artefact masquerading as a cache boundary.

**2.4** Lloyd's algorithm reached the *same answer* as the exact DP at the
selected *k* on both machines. If the result is identical, what did the migration
actually buy — and why does the dissertation say so explicitly rather than
claiming an accuracy improvement?

> **Answer.** It bought a **guarantee**, not a number — and saying so is the point.
>
> **What the audit found** (`scripts/verify_kmeans_optimality.py`, Table 1):
>
> | Machine | Lloyd optimal at | Lloyd sub-optimal at | Selected $k$: Lloyd | Selected $k$: exact |
> |:---|:---|:---|:---:|:---:|
> | Apple M1 | $k$ = 2,3,4,7,8 | $k$ = 5 (+2.9 %), 6 (+1.4 %) | **3** (sil. 0.894) | **3** (sil. 0.894) |
> | Intel i5 | $k$ = 2,3,4,5 | $k$ = 6 (+2.0 %), 7 (+0.4 %), 8 (+0.5 %) | **4** (sil. 0.935) | **4** (sil. 0.935) |
>
> Lloyd **did** miss the global optimum — but only at $k \ge 5$, beyond where the
> Silhouette peaked on either machine. So the selected answer was unchanged.
>
> **What the migration bought, precisely — three things, none of them accuracy:**
>
> 1. **Optimality becomes a theorem, not an observation.** Lloyd is a local-search
>    heuristic; it agreed *here*, on *these two* curves. The DP is provably optimal
>    on **every** input, so the claim generalises to the next machine, which is what a
>    method paper must be able to say.
> 2. **Determinism.** No seeding, no `n_init` restarts, no `random_state`. Two runs on
>    the same curve are **bit-identical by construction rather than by convention** —
>    which matters because §5 reports standard deviations across sweeps, and any
>    solver-induced variance would contaminate a *hardware* variability measurement.
> 3. **One removed hyperparameter.** `n_init` and `max_iter` are tuning knobs, and the
>    project's claim is zero-configuration. Deleting them is a claim-level improvement.
>
> **Why the dissertation states this rather than claiming accuracy.** Because claiming
> an accuracy improvement would be **false**, and trivially checkable — the selected
> $k$ and the Silhouette scores are identical to three decimal places in Table 1.
> Overclaiming here would cost more credibility than the honest version gains, and the
> honest version is the stronger methodological point anyway: **the value of an
> exactness guarantee is that you no longer have to check.** Reporting that Lloyd
> happened to agree is itself evidence that the migration was audited rather than
> assumed.

**2.5** Both the clustering objective and the segmentation objective are
monotonically non-increasing in *k*. Explain why this means neither can select
its own *k*, and enumerate the three families of solution to that problem.

> **Answer.**
>
> **The monotonicity.** Within-cluster sum of squares (and segmentation cost) can
> never increase when $k$ does: any $k$-partition is achievable by a $(k{+}1)$-solver
> that simply splits one cluster and re-optimises, so
> $\mathrm{cost}(k{+}1) \le \mathrm{cost}(k)$. At $k = n$ the cost reaches **exactly
> zero** — every point is its own cluster.
>
> **Why that forbids self-selection.** "Choose the $k$ that minimises the objective"
> therefore always returns $k = n$. The objective measures **fit**, and fit alone
> cannot distinguish structure from memorisation — it is the classical
> overfitting problem in its purest form. On the Intel curve that answer would be
> "202 memory levels", which is not merely wrong but *degenerate*: the criterion has
> no interior optimum to find.
>
> **The three families of solution:**
>
> | Family | Mechanism | Instance | Cost |
> |:---|:---|:---|:---|
> | **1. Penalise complexity** | add a term growing in $k$ and minimise the sum | PELT penalty; BIC; AIC | introduces a **hyperparameter** — the penalty *is* the answer |
> | **2. Find a knee** | look for where marginal improvement collapses | Elbow method; cost-knee | knee detection is itself heuristic and often ambiguous |
> | **3. Use a non-monotone criterion** | score a property that *worsens* if $k$ is too large | **Silhouette**; Gap statistic | needs a criterion that genuinely has an interior maximum |
>
> **What this project does.** Family 3 for the count (Silhouette), then Family 1's
> tool used *without* its penalty — `Dynp` given the count from Family 3 — for the
> boundaries. Family 1 (PELT) appears only as a sensitivity check, and Family 2
> (Elbow, cost-knee) only as independent cross-checks, where they visibly under-count
> on the Intel part (both return 2 against an expected 4).
>
> **The framing:** *"An objective that is monotone in its own parameter cannot choose
> that parameter. So I did not ask it to — I chose a criterion that is not monotone."*

**2.6** Why is the Silhouette coefficient able to select *k* without a penalty
term when inertia cannot? What property of the Silhouette is doing the work?

> **Answer.** Because the Silhouette is **not monotone in $k$** — it has a genuine
> **interior maximum** — and that non-monotonicity is intrinsic rather than imposed.
>
> **The mechanism.** For point $i$, with $a(i)$ its mean distance to its own cluster
> and $b(i)$ its mean distance to the nearest *other* cluster:
>
> $$s(i) = \frac{b(i) - a(i)}{\max\{a(i),\, b(i)\}} \in [-1, 1]$$
>
> The score is the mean of $s(i)$. The crucial feature is that it balances **two
> competing quantities**:
>
> | As $k$ increases | $a(i)$ (cohesion) | $b(i)$ (separation) | Silhouette |
> |:---|:---|:---|:---|
> | too few clusters | large (mixed levels) | large | low |
> | **correct $k$** | **small** | **large** | **maximal** |
> | too many clusters | small | **collapses** — a plateau split in two puts a near-identical cluster right next door | low |
>
> Inertia only ever measures $a(i)$, which improves without limit. The Silhouette
> measures $a$ *against* $b$, and $b$ **degrades** once you split real plateaus.
> Over-clustering is punished by the criterion's own structure, so no external penalty
> is needed. That is precisely what "threshold-free" means here.
>
> **The evidence it is working.** On the Intel huge-page curve the Silhouette peaks
> **sharply** at $k = 4$ with 0.933, up from 0.885 on 4 KiB pages — the recovered L3
> plateau makes the partition genuinely better separated, and the criterion registers
> it. A peak, not a plateau or a monotone climb.
>
> **The honest caveat to volunteer:** the Silhouette's freedom from a penalty is
> bought at the price of a different assumption — that every observation should count
> equally. Q2.7 is that bill arriving.

**2.7** The Silhouette weights every observation equally. Explain precisely why
that is a threat to this project's central claim, and describe the experiment in
§5.4 that tests it. Was the threat realised?

> **Answer.** This is the sharpest internal threat in the dissertation, and it is
> raised by the author rather than left for the examiner.
>
> **The threat, stated precisely.** The Silhouette averages $s(i)$ over points, so a
> cluster's influence is proportional to **how many points fall in it**. But the
> number of points in a level is fixed by the **sweep's geometric grid**, not by the
> hardware: a level spanning more octaves receives proportionally more samples. So in
> principle the selected $k$ could be an artefact of **the experimenter's chosen
> resolution** — which would make the headline claim ("the count is chosen by the
> data") circular, because the count would partly reflect a decision the author made.
>
> This is a **sharper** threat than the change-point penalty sensitivity, because the
> penalty is never used productively whereas the sampling grid always is.
>
> **The experiment (Table 20, `scripts/sampling_density_sweep.py`).** Re-run the probe
> **end to end** at 5, 10 and 20 points per octave on both machines — not
> subsampled, so each row is an independent sweep — and check whether the selected
> count moves:
>
> | Machine | Points/octave | Curve points | Selected $k$ | Silhouette |
> |:---|:---:|:---:|:---:|:---:|
> | Apple M1 | 5 | 94 | **3** | 0.912 |
> | Apple M1 | 10 | 182 | **3** | 0.898 |
> | Apple M1 | 20 | 348 | **3** | 0.896 |
> | Intel i5 | 5 | 104 | **4** | 0.929 |
> | Intel i5 | 10 | 202 | **4** | 0.934 |
> | Intel i5 | 20 | 388 | **4** | 0.932 |
>
> **Was the threat realised? No.** The selected count is **invariant** across a
> **four-fold** change in density on both machines, spanning 94–388 points. Note the
> 20-points-per-octave Intel row in particular: it lies *above* the original source
> grid, so it **could not have been subsampled** from the §5.3 curve — it closes the
> one gap an earlier version of the table had.
>
> **How to present it:** *"I identified a way my own criterion could have produced a
> circular result, designed the experiment that would expose it, ran it at four times
> the density, and the count did not move. The threat is real in principle and
> refuted in practice on these two machines."* Note the final clause — it is refuted
> **on this hardware**, not in general.

**2.8** Why is segmentation performed on **log**-latency rather than raw
nanoseconds? Work through what happens to the L1→L2 step versus the L2→DRAM step
under a squared-error cost if you omit the log.

> **Answer.** Because an $\ell_2$ cost on raw nanoseconds optimises for the **deepest**
> boundary and is nearly blind to the shallow ones.
>
> **The arithmetic, on the real M1 numbers** (1.53 → 9.19 → 130.43 ns):
>
> | Step | Raw difference | Squared (∝ cost reduction) | Log₂ difference |
> |:---|---:|---:|---:|
> | L1 → L2 | 7.66 ns | ~59 | **2.59 octaves** |
> | L2 → DRAM | 121.24 ns | ~14,700 | **3.83 octaves** |
> | **Ratio** | **15.8×** | **≈ 250×** | **1.5×** |
>
> **What goes wrong without the log.** A squared-error segmenter allocates breakpoints
> where they reduce cost most. On raw values the L2→DRAM transition is worth roughly
> **250×** more than L1→L2. Given a limited budget of breakpoints, the optimiser
> spends them **inside the DRAM region** — splitting a single physical plateau to
> shave its residual variance — while leaving the entire L1→L2 boundary unplaced. The
> L1 cache, the fastest and most important level, becomes the **cheapest to ignore**.
>
> **What the log fixes.** Caches are laid out **multiplicatively** — each level is
> some factor larger and slower than the last — so the physically meaningful quantity
> is a **ratio**, not a difference. Taking logs converts ratios to differences, so a
> 6× step costs the same whether it happens at 1.5 ns or at 130 ns. The cost function
> is then matched to the structure of the phenomenon.
>
> ```python
> signal = np.log(np.maximum(y, LOG_FLOOR_NS)).reshape(-1, 1)   # analysis.py:287
> ```
>
> `LOG_FLOOR_NS = 1e-6` guards $\log(0)$, which would be $-\infty$ and would poison the
> whole DP table. It is a **numerical guard, not a tuning knob** — no measurable
> latency approaches it, so it never binds on real data.
>
> **The one-line answer:** *"Latency spans two orders of magnitude and cache sizes are
> geometric, so the log is not a transform applied to the data — it is the space the
> data actually lives in. The reported capacity errors are quoted in octaves for the
> same reason."*

**2.9** BIC is the natural criterion for a Gaussian mixture, yet the project
scores the GMM by Silhouette instead. Give both reasons, and explain the
variance-heterogeneity argument with reference to the Intel L1 and DRAM bands.

> **Answer.** Two reasons, one methodological and one empirical. Concede the premise
> first — **BIC genuinely is the natural criterion** for a likelihood model, and this
> is a deliberate trade rather than an oversight.
>
> **Reason 1 — holding the criterion fixed isolates the model.** §5 *ranks* five
> estimators against one another. K-Means has **no likelihood**, so scoring it by BIC
> would require assuming an implied spherical, equal-variance Gaussian that the data
> does not support. Scoring the mixture by BIC while scoring K-Means by Silhouette
> would then **confound the model with the criterion**: a difference in the ranking
> could be caused by either, and the comparison could not attribute it. Since the
> comparison of interest is *model vs model*, the criterion is held constant.
>
> **Reason 2 — BIC is badly behaved on this data specifically.** Within-plateau
> variance is **extremely heterogeneous across levels**:
>
> | Intel band | p5–p95 spread |
> |:---|---:|
> | L1 | **0.38 ns** (1.57–1.69, tight) |
> | DRAM | **26 ns** (62.66–128.36, wide) |
>
> That is a **68-fold** difference in dispersion between two components of the same
> mixture. A Gaussian mixture free to fit components of such disparate variance is
> **rewarded by BIC** for placing several narrow components inside one physically
> single plateau: each narrow component buys a large likelihood gain for a fixed
> parameter penalty, so the penalty never bites where it should. The failure mode is
> not hypothetical — the mixture already shows it, returning a **modal five** levels
> against an expected four on the Intel part.
>
> **Why the Silhouette resists this.** It is a **geometric** criterion, scoring
> separation relative to cohesion rather than likelihood-per-parameter. Splitting a
> plateau places two near-identical clusters adjacent to each other, which **collapses
> $b(i)$** and drives the score down — regardless of how much likelihood the split
> bought.
>
> **The concession that makes it credible:** the dissertation states that reporting
> GMM+BIC as a *further independent cross-check* remains a reasonable extension (§6).
> That is the right posture — the choice is defended, not claimed to be the only
> defensible one.

**2.10** DBSCAN needs no *k*, which sounds ideal here. Why is it relegated to a
cross-check rather than promoted to the productive path? What does this reveal
about what "threshold-free" actually claims?

> **Answer.** Because **DBSCAN does not remove the free parameter — it relocates it**,
> and relocating it makes it *worse*, not better.
>
> **What DBSCAN trades.** It derives the cluster count from density instead of taking
> it as input, but in exchange it requires:
>
> | Parameter | Meaning | Units |
> |:---|:---|:---|
> | `eps` | neighbourhood radius | **the data's own units** — log-nanoseconds here |
> | `min_samples` | points needed to form a dense region | count |
>
> `eps` is the killer. It is **dimensioned in latency**, so a value tuned on the M1
> (L1 ≈ 1.53 ns, DRAM ≈ 130 ns) encodes that machine's specific latency ratios. Ship
> it to a machine with a different spread and it silently splits or merges levels.
> `k`, by contrast, is *dimensionless* — and the project does not even supply it, since
> the Silhouette selects it.
>
> **So the exchange is a bad one:**
>
> | | K-Means + Silhouette | DBSCAN |
> |:---|:---|:---|
> | Free parameters | `max_k = 8` (a **search bound**, not a threshold) | `eps` **and** `min_samples` |
> | Units | dimensionless | **latency-valued** |
> | Portable across machines? | yes | no — `eps` must be retuned |
>
> Adopting DBSCAN would put a hand-tuned, machine-specific, latency-dimensioned
> constant on the **productive** path — destroying exactly the claim the design exists
> to support.
>
> **What it reveals about "threshold-free".** The claim is **not** "this pipeline has
> no constants". `max_k = 8`, `min_size = 3` and `LOG_FLOOR_NS = 1e-6` all exist. The
> claim is narrower and defensible:
>
> > No constant whose value **determines a reported result** is set by hand. `max_k`
> > bounds a search the Silhouette resolves inside; `min_size` is a structural
> > minimum; `LOG_FLOOR_NS` is a numerical guard that never binds on real data. None
> > of them, moved, changes the answer — whereas `eps` and a PELT penalty *are* the
> > answer.
>
> **Why keep DBSCAN at all?** Because it is a genuinely **independent** cross-check:
> it reaches the count by a different mechanism (density, not variance), so its
> agreement is informative rather than circular. It returns **3 on the M1 and 4 on the
> Intel part**, matching the productive path at every sampling density in Table 20 —
> which is worth much more as corroboration than it would be worth as a producer.

**2.11** The counting step is order-ignoring and the localisation step is
order-respecting. Defend this division of labour on the grounds of *sufficient
statistics*, and rebut the objection that discarding order throws away
information.

> **Answer.** The two stages ask **different questions**, and each uses exactly the
> statistic sufficient for its own.
>
> | Stage | Question | Sufficient statistic | Order needed? |
> |:---|:---|:---|:---|
> | **Count** (K-Means) | *How many distinct latency regimes exist?* | the **multiset** of latency values | **no** |
> | **Localise** (`Dynp`) | *At which working-set size does each regime end?* | the **sequence** in WSS order | **yes** |
>
> **Why counting does not need order.** "How many plateaus are there?" is a question
> about the **distribution** of latency values, not their arrangement. The M1's values
> cluster around 1.53, 9.19 and 130 ns; that there are three modes is visible in a
> histogram with the *x*-axis thrown away entirely. The multiset is therefore
> **sufficient** for the count — and using only a sufficient statistic is a virtue,
> not a loss, because anything beyond it can only add variance.
>
> **Why localisation does need order.** "Where is the L2 boundary?" is inherently a
> statement about position along the WSS axis, so `Dynp` operates on the ordered
> signal and returns **contiguous segments** in sweep order.
>
> **Rebutting the objection — three points, strongest last:**
>
> 1. **Nothing is discarded from the pipeline**, only from *one stage*. The order is
>    still present and is used by the stage whose question requires it. The count is
>    handed to `Dynp`, which then applies it in the ordered domain.
> 2. **Robustness.** An order-ignoring counter is immune to a class of failure an
>    order-respecting one is not. A single anomalous point — an interrupt landing
>    mid-window — is one more sample in a cluster, not a candidate breakpoint. The
>    contaminated run of §5.3.2 shows the cost of this failing: the ensemble's
>    order-respecting members become the least stable.
> 3. **The independence argument, which is the real payoff.** Because the counter
>    never sees order and the localiser never chooses the count, the two cannot
>    conspire. §5.3's report makes this explicit: the change-point cross-check *"uses
>    the cost-knee criterion, which is **not** seeded by the Silhouette k, so its
>    agreement is genuine rather than circular."* Had one stage done both jobs, every
>    agreement between them would be self-confirmation.
>
> **The framing:** *"This is not a pipeline that discards order. It is a pipeline in
> which order is used exactly once, by the stage that needs it — which is what makes
> the cross-checks independent."*

**2.12** Grønlund et al. [60] give an O(n log n) algorithm for the same problem;
the code implements O(kn²). Is that a defect? Justify your answer with the actual
input sizes.

> **Answer.** **No** — and the justification must be quantitative, not a shrug.
>
> **The actual inputs:**
>
> | Machine | $n$ (curve points) | $k_{\max}$ | $O(k n^2)$ operations |
> |:---|---:|---:|---:|
> | Apple M1 | 182 | 8 | ~2.6 × 10⁵ |
> | Intel i5 | 202 | 8 | ~3.3 × 10⁵ |
> | Densest sweep (Table 20) | 388 | 8 | ~1.2 × 10⁶ |
>
> A million vectorised NumPy operations is **milliseconds**. Against that, the probe
> itself takes **~3 minutes** per sweep: 2²⁰ hops × 5 repeats at every one of ~200
> sizes. The inference stage is therefore **four to five orders of magnitude** below
> the measurement stage — asymptotically irrelevant at these sizes, since the constant
> factors and the $O(n)$ term dominate long before $n$ grows enough for $n^2$ to bite.
>
> **When it *would* become a defect.** $n$ is set by the sweep's octave span and
> points-per-octave. To reach $n \sim 10^5$ — where $n^2$ starts to hurt — you would
> need ~5,000 points per octave, which would take **days** to measure. The
> measurement cost grows with $n$ too, and grows *faster in wall-clock*, so the
> analysis can never become the bottleneck by this route.
>
> **The engineering judgement to state:** optimising a millisecond stage that sits
> behind a three-minute stage is **premature optimisation**, and it would cost
> something real. The $O(kn^2)$ DP is ~40 lines, readable, and auditable against
> brute-force enumeration — the test suite verifies it against **exhaustive
> enumeration including non-contiguous partitions**, which tests the contiguity lemma
> itself. Grønlund's algorithm relies on the objective's **concave Monge / totally
> monotone** structure (SMAWK-style search), which is materially harder to implement
> correctly and to verify. For a dissertation whose claim is *provable optimality*,
> a correct-and-checkable implementation is worth more than an asymptotic improvement
> that no input reaches.
>
> **The framing:** *"I cite Grønlund because the better bound exists and I should be
> seen to know it. I did not implement it because at $n = 202$ it would trade
> auditability for a saving I cannot measure."*

**2.13** A hostile examiner says: "Your level count is stable with std 0.00, but
that is one run on a quiet machine." How do you respond, and what does
`data/intel_l3_quiesced/` show?

> **Answer.** **Concede it immediately and completely — the examiner is right, and the
> dissertation already says so in stronger terms than the question does.**
>
> **The concession.** The std 0.00 in Table 13 is a property of a **quiet machine**,
> not of the part. It says the estimator is reproducible under favourable conditions.
> It does **not** say the estimator is robust.
>
> **What `data/intel_l3_quiesced/` shows — and it is worse than the examiner
> suggests.** That directory holds a three-sweep *unloaded* run captured as the matched
> control immediately before the loaded run of §5.3.2. It is **not** the clean §5.3
> baseline, and its own dispersion gives it away:
>
> | | `intel_l3_quiesced` | `intel_ci` (§5.3, genuinely quiet) |
> |:---|:---|:---|
> | L1 band, p5–p95 | **1.57–3.52 ns** | 1.57–1.69 ns |
> | Deepest band | 21.96–**116.71 ns** | 14.53–25.70 ns |
> | Levels per sweep | **5, 5, 4** | 4 in 10/10 |
> | L3 knee | 13.9, 9.85, 9.85 MiB | 19.7 MiB (9/10) |
> | Silhouette count | modal **7**, mean 5.33, **std 1.25** | mean 4.00, **std 0.00** |
> | Ensemble rank | **last of five** | first of five |
>
> Something was competing with the probe throughout. So on a contaminated run the
> productive counter **over-counts** — modal seven against an expected four — and
> becomes the **least stable member of its own ensemble**, precisely inverting its
> ranking on a quiet machine.
>
> **Why this strengthens rather than weakens the submission — four points:**
>
> 1. **It is reported, not buried.** The run is committed, the numbers are in Table 18,
>    and the limitation is carried into §5.5. It would have been trivially easy to keep
>    only the good run.
> 2. **The terminology is corrected.** The dissertation states that "quiescent" names
>    an **intent** rather than a verified state, which is why the row is labelled *by
>    run* rather than by condition. That is a level of precision the examiner's
>    question has not yet reached.
> 3. **A quiet reference is shown alongside it.** The ten-sweep `intel_ci` run is
>    presented as the genuinely quiet comparator, so the reader can see both.
> 4. **It generalises the §5.3.2 finding.** Contention degrades not only the recovered
>    *capacity* (a sixfold under-read of the shared L3) but the *level count* itself.
>    Both are properties of the running system rather than of the die — which is the
>    third lens's whole point (§1, §5.4).
>
> **The sentence to have ready:** *"You are right, and I would go further: I have a run
> that shows exactly the failure you are describing, it is in the repository, and it
> is in the dissertation as a limitation rather than an appendix. What I claim is that
> the count is stable on a quiet machine and that I can tell you when it is not."*

---

## Module 3 — Hardware Quirks & Edge Cases

**3.1** Compute the TLB reach of a 96-entry L1 DTLB under 4 KiB pages and under
2 MiB pages. Use the result to explain why the Intel L3 was invisible at 4 KiB.

**3.2** Explain the causal chain from "working set exceeds TLB reach" to "the
latency curve saturates before the L3 boundary". Why does a page-table walk cost
so much more than a cache miss?

**3.3** The 4 KiB Intel run reported a knee at ~3.5 MiB. The dissertation calls
this a *TLB-transition artefact, not a cache*. What evidence distinguishes an
artefact from a real cache boundary here?

**3.4** macOS on Apple Silicon uses 16 KiB base pages against x86's 4 KiB. Derive
the consequence for the number of pages touched by a 16 MiB working set, and
explain why this confounds the M1-versus-Intel comparison.

**3.5** Why can the huge-page control not be applied to Apple Silicon? Name the
specific API, the specific failure, and explain why this is reported as a
*finding* rather than as unfinished work.

**3.6** Explain why a *shared* L3 measures smaller than its nominal capacity from
a single probing core. Why does this not affect the L1 and L2 measurements?

**3.7** Under an eight-worker load the detected L3 fell from 19.7 MiB to 3.5 MiB,
and *every* latency rose by ~2.2×. Explain why the capacity conclusion survives
the second effect, and state the property that makes the argument work.

**3.8** The dissertation attributes that uniform 2.2× rise to DVFS but declines to
claim the magnitude is accounted for. Why? What does this SKU's turbo range imply,
and what instrument would settle it?

**3.9** *"The probe pins itself to a single core on all three platforms, so core
migration cannot affect the measurements."* Evaluate this statement with
reference to `pin_and_boost()`.

**3.10** The headline Intel L3 was corrected from 13.9 MiB to 19.7 MiB. Explain
the aggregation error that caused the original figure, and state the general
principle about which statistic is appropriate for a *latency* versus a
*boundary*.

**3.11** Distinguish the two competing biases on a detected capacity: the
soft-knee bias and the contention bias. Which caches does each affect, in which
direction, and why is the *sign* of the total not fixed?

**3.12** Why does a random-access pointer chase produce a *soft* knee rather than
a sharp step at the nominal capacity? Use the residency argument with real
numbers from the M1 L1.

---

## Module 4 — The Big Picture (Architecture & Data Flow)

**4.1** Trace one number — the Intel L1 capacity — from the C probe all the way
to a pixel in the browser. Name every file and every format transition.

**4.2** Why does the dashboard consume a build-time JSON bundle rather than
fetching the CSVs at runtime? Give at least two distinct justifications.

**4.3** `predev` and `prebuild` invoke `build-data.mjs` automatically. What class
of bug does that npm lifecycle hook prevent, and what would the failure look like
to a user?

**4.4** The dashboard reads `data/` — the same directory holding the committed
experimental evidence. Explain the trap this creates for a user running the
pipeline, and how `AUTOECHO_RUN` resolves it.

**4.5** Why is the frontend written in vanilla CSS rather than a utility
framework? Frame the answer in terms of what the project needed to control.

**4.6** Series colours come from `lib/series.ts`, not from `machine.color` in the
dataset. Explain the reason, and the accessibility property that had to be
preserved when the palette changed.

**4.7** The view is deep-linkable (`?machine=intel&compare=1`). Why does that
matter for a dissertation artefact specifically?

**4.8** `src/autoecho/probe/`, `preprocessing.py` and `clustering.py` implement a
method the project *rejected*. Justify keeping them in the submitted repository.

**4.9** What separates the eight scripts in `scripts/` from the modules in
`src/autoecho/`? State the criterion you would apply to a ninth script.

**4.10** The C extension is imported at module scope in `wss/__init__.py`, wrapped
in a `try` that re-raises with installation instructions. Critique this design —
what is gained, and what is the cost?

**4.11** Explain the role of `docs/pandoc-header.tex` and why the PDF build was
not reproducible before it existed. What does that episode illustrate about
"reproducible" as a claim?

**4.12** If an examiner unzipped this repository on a fresh Linux machine with no
network, what would work and what would fail? Be specific.

---

## Module 5 — The Project Journey

**5.1** The initial commit (`b62d9e0`) contained saved web-page JavaScript
bundles. Commit `c6bf394` removed them. Why does this matter beyond tidiness, and
what does it tell an examiner about how the repository was worked?

**5.2** Commit `30410e1` is the pivot: "implement high-precision WSS
pointer-chasing probe … to replace sample-based baseline". Explain what was wrong
with the baseline, and why the fix required a *new measurement design* rather
than a bug fix.

**5.3** The failed baseline is still in the repository and still documented in §4.
Argue for and against keeping a negative result in a submitted dissertation.

**5.4** The baseline's failure was originally diagnosed as "x86-bound" (it needed
`clflush`, ARM has none). That diagnosis was later withdrawn. What refuted it, and
what was the corrected explanation?

**5.5** Commit `f97cc8a` migrated from Lloyd's *k*-means to the exact DP. The
audit showed no reported result changed. Explain why the migration was still
worth making, and why the *audit* mattered more than the migration.

**5.6** Commit `e2a4dc3` removes a `random_state` argument. Why was that argument
meaningless after the DP migration, and what would leaving it in have implied?

**5.7** Trace the L3 result across its three states: masked at 4 KiB → recovered
at 13.9 MiB → corrected to 19.7 MiB. What changed at each step, and which change
was a *measurement* improvement versus an *analysis* correction?

**5.8** Commit `99cbff5` relocated eight scripts into `scripts/`. Name the
non-obvious thing that move silently broke, and explain how you would detect such
breakage systematically rather than by inspection.

**5.9** The final refactor (black, ruff, type hints, docstrings) changed no
numerical result. How would you *prove* that claim to a sceptical examiner rather
than asserting it?

**5.10** During that refactor, an automated fix would have added `strict=True` to
every `zip()` call. One site would then have raised at runtime. What does this
illustrate about the limits of automated refactoring?

**5.11** `.coverage` — a binary SQLite file — is currently tracked in git.
Explain why build artefacts in a submitted repository are a problem, and identify
two others that are correctly excluded by `.gitignore`.

**5.12** Appendix A declares that no reference was included on the basis of an
AI-generated description. The bibliography grew from 24 to 66 entries very late in
the project. Explain the integrity obligation this creates and how you discharged
it.

**5.13** The dissertation withdrew at least three claims it had previously made
(the "x86-bound" diagnosis, "within a fifth", the fixed sign of the edge bias).
Argue that this *strengthens* rather than weakens the submission, and identify the
principle at work.

---

## Cross-cutting questions

**X.1** State the single most consequential limitation of this project in one
sentence, then defend the work anyway.

**X.2** Where does Auto-Echo sit relative to `hwloc`, Intel MLC, and eviction-set
construction? Give the axis along which it wins and the axis along which each of
them wins.

**X.3** If you had one more week and one more machine, what exactly would you run,
and which claim in the dissertation would it most strengthen?

**X.4** An examiner asks: "Isn't this just lmbench with clustering bolted on?"
Answer in under sixty seconds.
