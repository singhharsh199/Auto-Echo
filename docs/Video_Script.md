# Project Presentation Video — Script

**Auto-Echo** · Harsh Raj Singh · MSc Project · submission 19 Aug 2026, 10:00

---

## Constraints (MSc Project Guide §4.7.1 and Claire's email)

| | |
|:---|:---|
| Length | **10 min ± 10%** → target **10:00**, hard bounds 9:00–11:00 |
| Camera | **You must be visible.** Voice-over alone is *not acceptable*. Minimum: at the start introducing, at key transitions, and in the conclusion |
| Audio | **Do not speed up the audio** — the email states this costs marks |
| Upload | Video files are slow to upload *and* then process. A 1 GB file is ~30 min on standard broadband. Upload days early |

**Five items that must be covered** (all are marked):

1. Statement of the problem investigated
2. Description of the methods used
3. **A demonstration of practical/implementation work**
4. A summary of the work
5. **A presentation of results — both positive *and* negative**

Item 5 is an advantage here, not a burden: this project's negative results are among its strongest material. Section 4 of this script is built around them deliberately.

**Script length:** ~1,378 spoken words. At a measured presentation pace of ~135 wpm that is ~10:12 of speech; with the demo's natural pauses and the marked beats this lands near 10:00. **Do not rush to fit more in** — if you overrun, cut from §3 (Methods), not from §5 (Demo) or §6 (Results).

---

## Timing map

| Time | Segment | Shot |
|:---|:---|:---|
| 0:00–0:50 | The question | **ON CAMERA** |
| 0:50–2:05 | Why it's hard, and three lenses | Slides |
| 2:05–2:25 | Transition | **ON CAMERA** |
| 2:25–3:25 | The failure I started from | Slides |
| 3:25–5:05 | Methods | Slides |
| 5:05–5:20 | Transition | **ON CAMERA** |
| 5:20–7:20 | **Demonstration** | Screen capture |
| 7:20–9:05 | Results, positive and negative | Slides |
| 9:05–10:00 | Summary and contributions | **ON CAMERA** |

---

## `0:00` — The question · **ON CAMERA**

> Every program's performance depends on the shape of the cache hierarchy it runs on — how many levels of cache there are, and how large each one is.
>
> But that information is essentially invisible to ordinary software.
>
> Today, you get it by **asking someone**. You ask the operating system, through a library like `hwloc`. Or you use an architecture-specific instruction, like x86's `CPUID`. Or a vendor tool, like Intel's Memory Latency Checker.
>
> Every one of those presupposes that **somebody has already written the answer down.**
>
> My project asked: what if nobody has? Can a program discover the hierarchy *for itself* — from timing alone, with no privileges, no vendor tables, and no architecture-specific instructions?

**Delivery.** Speak slowly; this is the setup. Count the three tools on your fingers. After *"what if nobody has?"* — **pause two seconds**, then continue. Look at the lens, not the screen.

---

## `0:50` — Why it's hard, and three lenses · *slides*

> Three things make this hard.
>
> **The hardware actively hides the signal.** Prefetchers predict your access pattern and fetch data early, which flattens the very steps I need to detect.
>
> **The clock is too coarse.** Apple Silicon's timer ticks every 41.7 nanoseconds. An L1 cache hit takes about 1.5. The instrument is twenty-seven times coarser than the signal.
>
> **And the obvious tools aren't portable.** x86 has an instruction to evict a cache line. ARM gives user space nothing equivalent.
>
> So why measure at all, when `hwloc` will just tell you? I want to be careful here, because the honest answer is not that `hwloc` is wrong.
>
> Think of it as three lenses on the same machine. The **commercial** lens — the vendor's system report — names your processor, your cores, your memory, and **not one cache size**. The **software** lens — `hwloc` — is genuinely excellent: on my Intel machine it reports every cache correctly, and my own measurements confirm it.
>
> But its chain of trust ends at what the operating system was told. And that fails in two different ways.

**Slide.** Three-lens diagram, or Table I from the paper.

---

## `2:05` — Transition · **ON CAMERA**

> On my two machines, it failed in both of those ways. And to explain how, I need to start with something that didn't work.

---

## `2:25` — The failure · *slides*

> My first implementation followed the standard technique: flush a cache line, write to it, then time how long it takes to read back.
>
> It failed. And my first explanation was wrong.
>
> I assumed the problem was ARM — that Apple Silicon has no cache-flush instruction available to user space. So I tested that assumption: I ran the same code on an Intel machine, **with** a working flush instruction and a proper timer.
>
> It failed there too. Two tiers on a four-level machine, and the tier it labelled "L1" measured **178 nanoseconds** — two orders of magnitude above that core's true value.
>
> The real fault was structural. Writing to a line immediately before timing the read **pulls that line into L1** — so every measurement was a cache hit by construction. The flush did nothing, because the write simply put the line back.
>
> That mattered, because it meant no amount of per-architecture porting would have helped. The measurement *design* had to change.

**Delivery.** This is your strongest section — you refuted your **own** hypothesis. Deliver it confidently, not apologetically.

---

## `3:25` — Methods · *slides*

> The redesign had to satisfy three constraints at once: never write before reading, never time a single access, and never require a flush.
>
> The solution is a **pointer chase**. I allocate a buffer, and link every cache line into a single random cycle, so each memory location contains the address of the next one. Then I just follow the chain.
>
> This solves all three problems at once. The addresses are random, so the prefetcher can't run ahead — and because a working set larger than the cache overflows it automatically, I never need a flush instruction at all.
>
> It also does something subtler. Each load's address is the *result* of the previous load, so the CPU physically cannot run them in parallel. That's what makes this a measurement of **latency** rather than bandwidth.
>
> For the coarse clock: I never time one access. I time **a million** dependent hops in a single window and divide. The total is about 1.6 milliseconds, so a one-tick error is 0.003 percent — and I'm dividing by an exact integer, so that adds nothing.
>
> One more piece matters. To turn those ticks into nanoseconds, the reference implementation reads the CPU's advertised frequency. I measure it instead, at runtime, against the operating system's clock — and on my Intel machine that turned out to matter. Windows advertises 2.4 gigahertz. The timer actually runs at 2.61. Had I trusted the label, every latency I report would have been eight point eight percent too high — and every *capacity* would still have been correct, so nothing in my own results would have contradicted anything. It would have been silently wrong.
>
> That gives me a curve: latency against working-set size. Flat where the data fits in a cache, stepping up where it doesn't.
>
> Then the machine learning has to answer two questions without being told the answer: **how many** levels are there, and **where** are the boundaries?
>
> Counting uses clustering with the silhouette criterion — chosen because, unlike the obvious alternatives, it isn't monotone, so it has a genuine optimum instead of always preferring more clusters. And I solve it *exactly*, by dynamic programming, rather than with the usual approximate algorithm — so the answer is provably optimal and identical every run.
>
> Localisation then takes that count and finds exactly that many change points. Nothing in this pipeline has a threshold I chose.

**Slide.** Pipeline diagram (Fig. 1), then the pointer-chase diagram, then a staircase curve.

---

## `5:05` — Transition · **ON CAMERA**

> Let me show you it actually running.

---

## `5:20` — **DEMONSTRATION** · *screen capture*

**This segment is explicitly assessed. Do not cut it.**

**(a) The probe — ~40 s.** Terminal, run the pipeline on a small sweep so it completes on camera:

```
python -m autoecho --method wss --max-mb 16 --output-dir data/demo_run
```

> Here's the framework running on this MacBook. It's sweeping working-set sizes, timing a million pointer hops at each one. No arguments about how many caches this machine has — it hasn't been told.

**(b) The output — ~30 s.** Open `validation_report.md`.

> And it produces this automatically: the discovered hierarchy, the level count agreed by five independent estimators, and validation against what the operating system reports. Recall, precision, and the error on every cache.

**(c) The dashboard — ~50 s.** Open the React dashboard.

> I also built an interactive dashboard over the results. Here's the latency curve — you can see the staircase directly, with the detected cache boundaries marked.

**(d) The three lenses — ~40 s.** Switch to the ArchLens section and step through the tabs.

> And this is the argument of the whole project in three clicks. Lens one, the vendor's system report: **no cache data at all**, on either machine. Lens two, `hwloc`: on the Intel it's complete and correct. On the M1 — watch this block — there's an eight-megabyte System-Level Cache that **exists in the silicon and is invisible to the operating system.** Lens three, my measurement: it's there.

**(e) Validation — ~35 s.** Switch to the validation panel.

> And the framework checks itself. Every detected boundary is matched against what the operating system reports, using optimal assignment, with a match declared when they agree within a factor of two. It reports recall, precision, and the error on every cache — so it tells you when it has failed, not just when it has succeeded. On this machine, both documented caches matched.

**Production note.** Record the demo separately and edit it in. Do a dry run first — if the live sweep is slow, pre-record it and narrate over the playback rather than waiting on camera. **Do not speed up the audio.** Speeding up *video* with your own voice over it is fine; altering the recorded audio is not.

---

## `7:20` — Results, positive and negative · *slides*

> So — the results. Both the positive and the negative, because the negative ones are where I learned most.
>
> **On the Apple M1**, all five estimators agree on three levels. It recovers L1 and L2, and it responds to capacity out to **13.9 megabytes** against a documented L2 of twelve. The only thing that can explain the difference is that undocumented System-Level Cache. **The operating system does not report it, `hwloc` does not report it — and measurement finds it.**
>
> **On the Intel machine**, the same code recovers the full four-level hierarchy: L1, L2, L3 and DRAM, with all three documented caches matched — the L2 and L3 to within one and a half percent.
>
> Across both machines: **five documented caches, five matches**, on two different instruction sets, from one code path with no per-machine configuration.
>
> Now the negative results.
>
> **First — that Intel result is conditional, and the condition is the sharpest thing I found.** Under the machine's *default* page size, the twenty-megabyte L3 is not just hard to detect. It's **unreachable**. Address translation saturates the curve at 143 nanoseconds before the working set ever gets near the cache. The tool reports a boundary at three and a half megabytes that isn't a cache at all — it's an artefact of the translation system. Enable two-megabyte pages, and the artefact vanishes and the real L3 appears. **Page size, not cache size, decided whether a cache was visible.**
>
> **Second — a shared cache doesn't have a fixed size.** With eight cores streaming data, the same twenty-megabyte L3 measures **three and a half**. An eighty-three percent under-read. What one core recovers of a shared cache isn't its capacity; it's the share the rest of the system left it.
>
> **And third**, the honest limit: on the M1 I cannot separate the L2 from that System-Level Cache. They merge into one band. A one-dimensional latency sweep can't split two adjacent tiers with similar latencies, and no amount of better inference recovers information the measurement never captured.
>
> I should also be clear about the evidence base. Two machines, both consumer laptops, is a narrow foundation for a claim about architectures. And the two aren't strictly comparable — the M1 uses a larger memory page than the Intel, so it faces a quarter of the address-translation pressure. That means I can't attribute the M1's cleaner deep curve to its architecture alone. Part of it may simply be the page size — and macOS won't let me change it to find out.
>
> The next experiment I'd run is an AMD processor, because its last-level cache is organised differently — private to each group of cores rather than shared across all of them. That gives a falsifiable prediction: loading cores in the *same* group should reproduce my contention result, and loading a *different* group should not. Whichever way that came out, it would tell me whether I measured cache sharing or just a busy machine.

---

## `9:05` — Summary · **ON CAMERA**

> So, to summarise.
>
> I built a framework that discovers a machine's cache hierarchy from user space, using nothing but timing. No privileges, no vendor tables, no architecture-specific instructions. It works on both ARM and x86 from a single code path, and every documented cache on both machines was recovered within a factor of two.
>
> But the result I'd point to isn't the accuracy. It's this: a lookup table can only tell you what a cache **is**. It can't tell you what your program can actually **use** — because that depends on your page size, and your machine's load, and how many other cores are competing for it.
>
> On the Apple M1, measurement found a cache that no interface reports. On the Intel machine, it found a cache that is perfectly documented, entirely correct — and unreachable.
>
> Neither of those is visible to a table. That's the case for measuring.
>
> Thank you.

**Delivery.** Slow down for the last three paragraphs. Hold eye contact for *"That's the case for measuring."* Pause a beat before *"Thank you."*

---

## Production checklist

- [ ] **Camera** at start (0:00–0:50), transitions (2:05, 5:05), conclusion (9:05–10:00) — the stated minimum
- [ ] Rehearse once with a timer; adjust §3 (Methods) if over 11:00
- [ ] Record demo separately; **dry-run the live sweep** before recording
- [ ] Do **not** alter recorded audio speed
- [ ] Check final duration is **9:00–11:00**
- [ ] Check file size and estimate upload time (~1 GB ≈ 30 min, then processing)
- [ ] **Upload at least 2 days early** — late penalties apply to the *whole project*

## Numbers used (all verified against the dissertation)

| Claim | Value |
|:---|:---|
| Timer coarseness | 41.7 ns tick vs ~1.53 ns L1 = 27× |
| Baseline failure | 178 ns "L1", 2 tiers on a 4-level machine |
| Batch window | 2²⁰ hops ≈ 1.6 ms → ±0.0026% |
| M1 | 3 levels; L1 157.5 KiB (+23.0%); L2+SLC 13.9 MiB (+16.1%); 2/2 matched |
| Intel | 4 levels; L1 55.7 KiB (+16.0%); L2 1.2 MiB (−1.5%); L3 19.7 MiB (−1.5%); 3/3 matched |
| 4 KiB masking | saturates ~143 ns by 4–5 MiB; ~3.5 MiB artefact; recall 2/3 |
| Contention | L3 19.7 → 3.5 MiB under 8 streaming workers = −83% |
