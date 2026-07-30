# Auto-Echo — Tutoring Session Log & Viva Study Guide

This file has two parts:

- **Part 1 — Live Session Log.** Grows as the tutoring session progresses. Each
  entry records one sub-concept (explained on the Novice → Intermediate → Expert
  ladder), the question asked, the student's answer, and the tutor's verification.
- **Part 2 — Question Bank.** 57 standalone viva questions, written up front.

> **Note.** Three questions in Part 2 (1.5, 2.1, 3.9) deliberately contain a false
> premise, because they encode misconceptions that are easy to acquire about this
> project — two of which appeared in the original curriculum brief. Spotting the
> false premise *is* the answer.

---

# Part 1 — Live Session Log

## Module 1 — The C Probe

### Concept 1.1 — Python ki jagah C kyun? (Why C, not Python)

**🟢 Novice.** Hummingbird ke wing beat ko haath wali stopwatch se time karne ki
koshish karo. Tumhara reaction time ~250 ms hai, wing beat ~20 ms. Tum bird ko
nahi, *khud ko* measure kar rahe ho. Instrument hamesha signal se tez hona chahiye.

**🟡 Intermediate.** Measured L1 hit = **1.53 ns** (`data/validation_report.md`).
Ek CPython bytecode dispatch ≈ **30–100 ns** — yaani instrument signal se 20–60×
slow. Isliye timing loop C mein hai: `src/autoecho/wss/wss_probe.c:364`, ek line —
`p = (void **)(*p);`. Python (`wss/__init__.py`) sirf orchestration karta hai:
sizes choose karna, `measure_wss()` call karna, ticks→ns convert karna. Hot path
ko kabhi touch nahi karta.

**🔴 Expert.** Speed se bhi bada reason: **memory layout control**. CPython mein
`list[i]` ek boxed `PyObject` ka pointer hai jo heap mein kahin bhi ho sakta hai —
addresses allocator decide karta hai, tum nahi. Poora experiment is baat par
depend karta hai ki slot *k* base se exactly `k × line_size` bytes par ho, kyunki
capacity infer hi isse hoti hai ki *kaunsa address kaunse cache set* par map karta
hai. Python yeh guarantee nahi de sakta. Perfect Python timer bhi ek aisa working
set measure karta jiska actual footprint tum state hi nahi kar sakte.

**❓ Question 1.1** — Ek colleague kehta hai: "NumPy use karo, uske inner loops toh
C mein hi hain." Do-part answer chahiye:
(a) Quantitative argument — apne actual L1 number aur bytecode dispatch cost se.
(b) Aur ek *second, independent* reason jo speed se bilkul alag ho.

**Student's answer:**
> (a) We can't measure a signal of 1.53 ns with Python as it can measure a signal
> within the range of 30–100 ns. Also NumPy is beneficial in continuous memory
> allocation rather than random memory allocation.
> (b) Nahi pata.

**Verification — (a): strong pass ✔️**

Core principle sahi pakda: instrument signal se coarser hai. Sharpening ke liye
ek number add karo — probe har measurement mein 2²⁰ = 1,048,576 hops karta hai:

| | Time |
|:---|:---|
| Asli signal (1,048,576 × 1.53 ns) | ~1.6 ms |
| Python loop (× ~50 ns/hop) | ~52 ms |

Yaani measurement **97% interpreter, 3% memory** hoti — hierarchy noise mein doob
jaati. Yeh "20–60× slow" se zyada convincing hai.

*Correction:* "NumPy continuous memory ke liye behtar hai" — instinct sahi,
wording imprecise. Precise: NumPy tab fast hai jab ek operation **poore array par
ek saath** apply ho (`arr * 2`) — Python sirf ek baar involved hota hai. **Pointer
chase vectorize ho hi nahi sakta**, kyunki hop *n+1* ko hop *n* ka *result*
chahiye. Isliye NumPy ka poora advantage yahaan **structurally inapplicable** hai;
loop Python mein hi chalega aur (a) wali problem wapas aa jayegi.

**Verification — (b): taught**

**Core answer:** NumPy array sirf **values** (int64/float64/bool) store kar sakta
hai — **addresses nahi**. Pointer chase ko chahiye
`*(void **)slot = (void *)next;` (`wss_probe.c:347`) — har slot ke andar agle slot
ka *real memory address*. NumPy mein tumhe indices store karne padenge, aur tab
teen cheezein tootti hain:

1. **Hardware ko dependency dikhni band.** C: `p = *p;` — ek load, jiska result hi
   agla address hai; CPU ka load unit ek saaf dependent-load chain dekhta hai
   (isiliye `lfence` ki zaroorat nahi). Python: `i = arr[i]` = bounds check →
   PyObject unbox → address compute → load → box. CPU sirf interpreter bookkeeping
   dekhta hai; measurement ka theoretical foundation hi gayab.
2. **Alignment control khatam.** C maangta hai `posix_memalign(&p, 16384, size)`
   (`AE_ALIGN`, `wss_probe.c:137`). NumPy 16 KiB alignment maangne ka tarika nahi
   deta; non-aligned buffer par cache line do pages par straddle kar sakti hai aur
   "kitne distinct pages touch huye" wala hisaab bigad jaata hai.
3. **Huge pages impossible.** `VirtualAlloc(..., MEM_LARGE_PAGES, ...)` NumPy se
   maanga hi nahi ja sakta — matlab §5.3 ka poora huge-page result (jisne Intel ka
   20 MiB L3 unmask kiya) exist hi nahi karta.

**Yaad rakhne ka tareeka:** (a) kehta hai *"Python dheema hai"*. (b) kehta hai
*"chahe Python infinitely fast ho jaaye, tab bhi experiment invalid rahega"* —
kyunki tum aisa working set measure karoge jiska actual memory footprint tum state
hi nahi kar sakte. Yahi (b) ko (a) se independent banata hai.

---

### Side-note 1.1a — "CPython" kya hai? (student ne poocha)

**🟢 Novice.** **Python** = language (rules, grammar — ek specification).
**CPython** = us language ka ek *implementation* — woh actual program jo `.py`
file padhta aur chalata hai. Woh khud C mein likha gaya hai, isliye naam
"**C**Python". Analogy: "Hindi" language hai; Hindi *bolne wala insaan*
implementation hai. Doosre implementations: PyPy (JIT), Jython (JVM),
MicroPython.

**🟡 Intermediate.** Iska proof repo mein literally likha hai:
`src/autoecho/wss_probe_c.cpython-313-darwin.so` — filename mein "cpython-313"
(CPython 3.13) aur "darwin" (macOS) encoded hai. Confirmed: implementation =
CPython, version = 3.13.2. `wss_probe.c` mein 23 jagah CPython C-API use hua hai
(`#include <Python.h>`, `PyArg_ParseTuple`, `PyFloat_FromDouble`,
`Py_BEGIN_ALLOW_THREADS`, `PyErr_NoMemory`). Isliye `setup.py` ka
`python_requires=">=3.11"` sirf language version nahi — CPython C-API
compatibility ka statement hai. PyPy par yeh extension bina recompile ke load
nahi hoga.

**🔴 Expert.** "30–100 ns per bytecode dispatch" aata kahan se hai: `.py` →
bytecode → `ceval.c` ka eval loop. Har instruction par fetch + decode + dispatch
(often-mispredicted branch), stack se `PyObject*` operands, runtime type check,
`Py_INCREF`/`Py_DECREF` refcounting, aur naye objects ke liye heap allocation.
Python mein `x = 5` ek heap-allocated object hai (refcount + type ptr + value);
C mein `int x = 5` ek register hai. Yeh cost dynamic typing + refcounting +
interpretation ki honest price hai — data pipelines ke liye worth it, 1.53 ns
measure karne ke liye nahi. Related: `Py_BEGIN_ALLOW_THREADS`
(`wss_probe.c:353`) GIL release karta hai — GIL bhi CPython-specific hai — taaki
interpreter timing window ke andar interfere na kare.

---

### Side-note 1.1b — GIL kya hai, aur iska trade-off? (student ne poocha)

**🟢 Novice.** GIL = **Global Interpreter Lock**. Kitchen mein 8 cooks aur 8
chopping boards, lekin **chaaku ek hi** — ek time par sirf ek cook chop kar sakta
hai. Cooks = threads, boards = CPU cores, chaaku = GIL. CPython mein ek time par
sirf **ek thread Python bytecode** chala sakta hai, chahe 10-core machine ho.
Isliye `threading` se CPU-bound Python kaam truly parallel nahi hota.

**🟡 Intermediate.** `wss_probe.c:353` `Py_BEGIN_ALLOW_THREADS` aur `:373`
`Py_END_ALLOW_THREADS` — "chaaku wapas rakh diya / wapas le liya". Beech mein
sirf plain C variables hain (`p`, `g_sink`, `best`, `c0`, `c1`) — ek bhi
`PyObject` nahi. **Golden rule:** BEGIN/END ke beech koi Python object touch nahi
karna. Agar galti se `PyFloat_FromDouble()` andar call ho jaata, toh refcount
race hota aur interpreter random, reproduce-karne-mein-mushkil crash deta.

**🔴 Expert — GIL exist kyun karta hai.** Reference counting ki wajah se.
`Py_INCREF`/`Py_DECREF` atomic nahi hain — machine level par *read → add → write*
teen steps hain. Do threads bina lock ke same refcount badhayein toh ek increment
kho jaata hai → object tab free ho jaata hai jab reference abhi zinda hai →
**use-after-free** (crash ya security bug). Teen solutions the: (1) per-object
lock — single-thread code 2× slow; (2) atomic refcounts — cache-line bouncing,
slow; (3) **ek global lock** — single-thread fast, C extensions simple. Guido ne
(3) chuna. GIL bug nahi, **deliberate trade-off** hai.

**Trade-off — kya milta hai:** single-threaded Python fast (koi per-object lock
overhead nahi); C extensions likhna aasaan (`wss_probe.c` ek bhi mutex use nahi
karta aur phir bhi safe hai); refcounting simple, predictable, GC pauses nahi.
**Kya khota hai:** CPU-bound threads parallel nahi chalte — 10-core machine par
bhi pure-Python CPU kaam 1 core jitna. **Escape routes:** `multiprocessing`
(alag process = alag GIL), GIL-releasing C extension (← yeh project), `asyncio`
(I/O-bound). Python 3.13 mein experimental free-threaded build (PEP 703) hai jo
GIL hata deta hai, par C extensions alag se compile karne padte hain.

**Is project ke liye trade-off (viva-relevant).** `measure_wss()` seconds tak
chalta hai (poora sweep ~3 min); GIL pakde rakhna poore interpreter ko freeze
karta, isliye release karna correct engineering hai. **Honest caveat:** release
karne ka matlab hai doosre Python threads chal *sakte* hain aur measurement mein
noise daal sakte hain — pipeline single-threaded hai isliye practically issue
nahi. **Key insight:** kyunki C code GIL release karta hai, koi sweep ko parallel
threads mein chala *sakta* hai — aur result **bilkul galat** aayega, kyunki woh
threads ek hi shared L3 par ek doosre ka data evict karenge. Tab tum hardware
latency nahi, ek doosre ki interference measure karoge. Yeh exactly wahi effect
hai jo §5.3.2 measure karta hai (8 workers ne detected L3 ko 19.7 MiB → 3.5 MiB
gira diya). Isliye probe **deliberately sequential** hai — yeh slowness nahi,
**correctness** hai, aur uska measured proof dissertation mein maujood hai.

---

### Concept 1.2 — Sequential vs Randomized Pointer-Chasing

**🟢 Novice.** Library ka **smart librarian** tumhe dekh raha hai. Book 1,2,3,4
maango toh woh pattern samajh kar book 5 pehle hi le aata hai — har book "instant"
milti hai aur tum galat conclusion nikaaloge ki desk infinite hai. Desk measure
karne ke liye **unpredictable** hona padega (book 400, 17, 933). Woh librarian =
**hardware prefetcher**.

**🟡 Intermediate.** `wss_probe.c` mein do alag properties: **randomness**
(Fisher–Yates, line 337) prefetcher ko pattern seekhne se rokti hai; **single
Hamiltonian cycle** (line 344, `% nslots`) chase ko chhote sub-loop mein phasne se
rokta hai. Dono alag kaam karte hain — inhe conflate mat karna.

**🔴 Expert.** Asli property randomness nahi, **serialisation by data dependency**
hai. `p = *p` mein load *n+1* ka address load *n* ka result hai; CPU ka 300+ entry
reorder buffer 20 loads overlap kar *sakta* hai par kar *nahi* sakta. Yaani
**MLP = 1** — pure load-to-use latency. Independent random accesses se prefetcher
tab bhi harta, par CPU 10–20 accesses overlap kar leta aur tum `latency ÷ MLP`
measure karte (~1/10), plateaus squash ho jaate.

### Side-note 1.2a — "Hamiltonian cycle" kya hai? (student ne poocha)

**🟢 Novice.** Delivery route jo **har ghar par exactly ek baar** jaaye aur wapas
start par aaye. Naam William Rowan Hamilton se. Galat routes: kuch ghar do baar /
kuch bilkul nahi; ya sirf 10 gharon ka chhota loop.

**🟡 Intermediate.** `order[]` ek shuffled permutation hai (0..n-1, har number ek
baar). Chain: `order[0] → order[1] → … → order[n-1] → order[0]`. Woh `% nslots`
cycle **band** karta hai — guarantee ki har slot exactly ek baar visit hoga.

### Side-note 1.2b — "Prefetcher haara hua" ka matlab? (student ne poocha)

**🟢 Novice.** Prefetcher = hardware unit jo guess karta hai ki tum aage kya
maangoge aur data pehle hi cache mein le aata hai. **"Haara hua"** = guess nahi kar
paa raha, toh load ke waqt data cache mein nahi hota aur **poori asli latency**
bharni padti hai — **yahi humein chahiye**. Prefetcher jeeta toh staircase gayab.

**🔴 Expert.** Types: next-line, stride, stream — teeno random chase se haar jaate
hain. **Lekin** Apple M1 ka **DMP** (data memory-dependent prefetcher, Augury [46])
pointer-jaisi values follow karta hai — aur chase exactly wahi pattern hai. §2.4
mein honestly likha hai: M1 curves clean hain toh effect staircase flatten karne
jitna bada nahi — **observation hai, guarantee nahi**.

**❓ Question 1.2** — Agar proper cycle ke bajaye har slot mein *koi bhi* random
slot ka address daal do (addresses ab bhi random, prefetcher ab bhi haara hua):
(a) specifically kya galat hoga? (b) curve ke kaunse hisse mein dikhega, aur kyun?

**Student's answer:**
> Hamiltonian cycle kya h? prefetcher haara hua h se kya mtlb h?
> (a) pata nahi. (b) I think bade working set me problem dikhegi.

**Verification — (b): correct ✔️ / (a): taught**

**(b) sahi hai.** Reason yeh hai:

Proper cycle ke bina tum ek **random functional graph** bana rahe ho, jismein chase
**"ρ" (rho) shape** mein phas jaata hai — ek tail, phir ek chhota cycle jisse tum
kabhi bahar nahi nikalte. Random functional graph theory: repeat hone se pehle tum
sirf **≈ √(πn/2) ≈ √n distinct nodes** visit karte ho.

Concrete (M1, 128 B line):

| | Value |
|:---|:---|
| Intended working set | 16 MiB |
| Total slots (n) | 131,072 |
| Actually visited (√(πn/2)) | **~454 slots** |
| Actual memory touched | **~57 KiB** |

57 KiB M1 ke **128 KiB L1 mein fit ho jaata hai** — toh measurement ~1.5 ns (L1)
bologi jabki 16 MiB ke liye ~9 ns+ hona chahiye tha.

Isliye error **sirf bade sets par** dikhta hai:

| WSS | Intended | Actual (√n) | Fit kahan | Error |
|:---|:---|:---|:---|:---|
| 8 KiB | 8 KiB | ~1 KiB | dono L1 | nahi |
| 16 MiB | 16 MiB | ~57 KiB | intended DRAM, actual L1 | **bahut bada** |

Kyunki √n, n se bahut dheere badhta hai. **Curve ka shape:** thodi der upar jaata,
phir **flatten** — DRAM plateau kabhi aata hi nahi. Aur sabse khatarnaak: curve
**plausible dikhega** — koi crash nahi, koi error nahi, bas chupchaap galat. Isliye
`% nslots` sirf modulo nahi, **correctness guarantee** hai.

---

### Concept 1.3 — Coarse clock se fine signal (batch amortisation)

**🟢 Novice.** Stopwatch sirf poore seconds dikhati hai, kaam 40 ms ka hai. Ek baar
karo → "0 seconds", bekaar. 1000 baar karo → 41 seconds → divide → 41 ms. Stopwatch
utni hi coarse hai; tumne uski coarseness **amortise** kar di.

**🟡 Intermediate.** Apple Silicon timer 24 MHz = **~41.7 ns/tick** (exactly
`125/3`), aur L1 hit **1.53 ns** — timer **27× coarser**. Single access time karoge
toh 0 ya 1 tick milega, beech mein kuch nahi. Solution: `DEFAULT_MIN_HOPS = 1 << 20`
(`wss/__init__.py:44`) — 2²⁰ hops ek window mein, phir `(c1-c0)/hops`
(`wss_probe.c:363`). 2²⁰ × 1.53 ns ≈ 1.6 ms ≈ 38,500 ticks → granularity ka asar
1/38,500 → sub-nanosecond resolution.

**🔴 Expert.** Trick sirf tab valid hai jab per-hop cost window bhar mein
**stationary** ho. Agar cost drift kare toh tum drift ko chupchaap estimate mein
fold kar rahe ho.

**❓ Question 1.3** — (a) Skeptical examiner: *"clock 41.7 ns ka hai, tum 1.53 ns
kaise bol sakte ho? Yeh cheating hai!"* — ek line mein convince karo.
(b) Amortisation ke liye kaunsi assumption chahiye, aur codebase mein kaunsa design
decision use protect karta hai?

**Student's answer:**
> (a) I will increase the number of iterations, then will divide by that number to
> find 27 times finer latency.
> (b) Per hop cost should be stationary.

**Verification — (a): pass ✔️ (mechanism sahi, framing chahiye) / (b): half pass ✔️**

**(a)** Mechanism sahi hai, par examiner ko *justification* chahiye. Reframe:
❌ "Main ek access ko 1.53 ns precision se measure kar raha hoon."
✅ "Main ek access measure kar hi **nahi** raha — main **10 lakh accesses ka total**
measure kar raha hoon, aur woh total itna bada hai ki timer ki coarseness usmein
negligible ho jaati hai."

*Analogy:* Ek kaagaz ki sheet mm-ruler se naapo — impossible. 1000 sheets ka stack
= 52 mm → divide → 0.052 mm/sheet. Ruler improve nahi kiya; **signal-to-resolution
ratio** improve kiya.

| | Value |
|:---|:---|
| Total time (2²⁰ × 1.53 ns) | 1,604,321 ns ≈ 38,500 ticks |
| Timer uncertainty | ±1 tick = ±41.7 ns |
| **Relative error on total** | **±0.0026%** |

Key point: hop count ek **exact integer** hai — usse divide karne mein koi nayi
uncertainty add nahi hoti.

**(b)** Assumption **bilkul sahi** — per-hop cost stationary honi chahiye. Protection
mechanisms **teen** hain, teen alag threats ke liye:

| Threat | Kahan | Protection |
|:---|:---|:---|
| Cold-start transient (cold misses, TLB fill) | window **ke andar** | **Warm-up traversal** (`wss_probe.c:356`) — timing se pehle poora set ek baar traverse, taaki window ke start aur end ki cost same ho. *Sabse direct protection.* |
| Random interference (OS interrupt, background process) | ek window | **Min over 5 repeats** — interference sirf time *add* kar sakta hai, isliye minimum disturbed windows ko discard kar deta hai |
| Thermal drift over ~3 min | **poore sweep** mein | **Shuffled size order** (`wss/__init__.py:93`) — ascending order mein bade sizes hamesha last (garam die) hote, aur woh badhotri size ke saath *correlated* hoti → fake upward slope cache boundary lagta. Shuffle se drift systematic bias ki jagah random noise ban jaata hai. |

---

### Side-note V.1 — hwloc, CPUID leaf 4, Intel MLC kya hain? (viva opening ke liye)

Ek line mein:

| Tool | Kya karta hai | Jawab kahan se |
|:---|:---|:---|
| **hwloc / lstopo** | Machine ka topology map | OS se **poochta** hai |
| **CPUID leaf 4** | CPU khud batata hai | Silicon mein **likhi table** |
| **Intel MLC** | Latency/bandwidth **measure** | Measure karta hai, par shape **pehle se maan leta** hai |

**hwloc / lstopo** [27] — open-source topology library; `lstopo` uska visualiser
(Machine → Package → L3 → L2 → L1 → Core). **Kuch measure nahi karta, sirf padhta
hai:** Linux `/sys/devices/system/cpu/cpu0/cache/`, macOS `sysctl`, Windows
`GetLogicalProcessorInformationEx` — **yeh wahi teen interfaces hain jo
`validation.py` ground truth ke liye use karta hai.** Farq: hwloc wahin rukta hai;
hum usse apne measurement ko *check* karte hain.

**CPUID leaf 4** [28] — x86 **instruction**. EAX mein leaf number daalo, `cpuid`
execute karo, CPU registers mein jawab bharta hai (leaf 0 = vendor, leaf 1 =
family/model, **leaf 4 = Deterministic Cache Parameters**). Subleaves 0,1,2,3… par
loop karo; har subleaf ek level deta hai: type, level, line size, associativity
(ways), sets. `capacity = ways × partitions × line_size × sets`.
**Do limitations:** (i) yeh measurement nahi, **manufacturer ki burned-in table**
hai; (ii) **x86-only** — ARM par `cpuid` exist hi nahi karta. ARM ke `CLIDR_EL1` /
`CCSIDR_EL1` **EL1 (kernel)** level par hain, user space se padhe nahi ja sakte,
aur Apple Silicon par expose hi nahi hote. **Isliye "bas CPUID use kar lo" wala
objection Apple Silicon par kaam hi nahi karta.**

**Intel MLC** [29] — Intel ka free tool jo **sach mein measure** karta hai. Phir bhi
competitor nahi: (i) **Intel-only**; (ii) **hierarchy ka shape pehle se maan leta
hai** — tum use bolte ho "L2 ki latency naapo", jiske liye pehle se pata hona
chahiye ki L2 hai aur kitna bada. Woh **parameters** measure karta hai; hum **shape
discover** karte hain.

**Chain of trust (poore argument ka core):**

```
hwloc/lstopo → OS interface → firmware(ACPI)/CPUID → manufacturer's table
CPUID leaf 4 ──────────────────────────────────────→ manufacturer's table
Intel MLC    → measures ✓ ... but shape given + Intel-only
Auto-Echo    → measures ✓ ... discovers shape ✓ ... koi table nahi chahiye
```

Har existing tool ki chain aakhir mein ek aisi table par khatam hoti hai jo kisi ne
pehle likhi hai — bas yahi opening line ka matlab hai.

**💎 Killer example (apne hi data se).** M1 mein ~8 MiB **System Level Cache** hai
jise **koi OS interface report nahi karta** — `sysctl` chup, hwloc chup, aur ARM par
CPUID hai hi nahi. Woh cache exist karta hai (reverse-engineered, ref [13]) aur
§5.2 ke latency curve mein L2 ke saath merged mid-band ke roop mein **dikhta** hai.
Isiliye §4.3 ke "expected levels" rule mein SLC count nahi hota — kyunki woh
OS-reported nahi hai.

**⚠️ Trap:** In tools ko "kharab" mat kehna — woh apni supported machines par
Auto-Echo se **zyada accurate** hain. Sahi framing: *"Each is more accurate than my
tool on the hardware it supports — that's precisely the point. I'm asking what
remains recoverable when none of them applies."*

---

### Side-note V.2 — LIVE PROOF apni hi machine par (`sysctl` output)

Student ne `lstopo` chalane ki koshish ki → `command not found` (hwloc macOS par
default nahi; `brew install hwloc`). Lekin install ki zaroorat nahi — hwloc macOS
par **jo padhta hai** woh seedha dekha ja sakta hai, aur usse dissertation ka core
argument live prove ho jaata hai.

**Actual output (Apple M1, is machine par):**

```
hw.perflevel0.l1dcachesize: 131072      # 128 KiB — P-core
hw.perflevel0.l1icachesize: 196608      # 192 KiB
hw.perflevel0.l2cachesize:  12582912    # 12 MiB
hw.perflevel1.l1dcachesize: 65536       # 64 KiB — E-core
hw.perflevel1.l2cachesize:  4194304     # 4 MiB
hw.cacheconfig: 8 1 4 0 ...             # 8 cores, 1/L1, 4 share L2
hw.cachelinesize: 128
hw.l1dcachesize: 65536                  # ⚠️ generic = E-CORE value
hw.l2cachesize:  4194304                # ⚠️ generic = E-CORE value

SLC / "system level cache" grep  →  KUCH NAHI. Ek bhi entry nahi.
```

**Finding 1 — SLC literally invisible.** M1 ka ~8 MiB System Level Cache silicon
par maujood hai (reverse-engineered, ref [13]) aur macOS uske baare mein **ek shabd
nahi** bolta. Chain of trust: `hwloc → sysctl → yeh output`. Toh **hwloc bhi SLC
nahi dikha sakta** — source mein hai hi nahi. Aur probe usse latency curve mein
dekh leta hai (§5.2, L2 ke saath merged mid-band).
*Viva line:* "I can demonstrate this on my own machine. The M1 has an 8 MiB SLC.
`sysctl` reports nothing about it, so `hwloc` cannot either. My probe sees its
effect in the latency curve. That is the gap this project addresses."

**Finding 2 — heterogeneous-die trap, jise code ne pakda ✅.** Generic
`hw.l1dcachesize` = 65536 (**E-core**), jabki probe **P-core** par chalta hai
(131072). Generic key use karte toh detected 157.5 KiB ko 64 KiB ke against score
karte → **+146% error** instead of +23%, aur poora M1 validation galat hota.
`validation.py` explicitly `hw.perflevel0.*` padhta hai — sahi decision.
*Viva line:* "On a heterogeneous die the generic `sysctl` keys report the efficiency
cluster. Since the probe runs on a performance core, using them would have scored a
P-core measurement against E-core ground truth."
**📌 ACTION:** Dissertation mein yeh likha nahi hai. §5.3 mein Windows per-core
oracle fix ka poora paragraph hai, par macOS ne bhi wahi problem solve ki aur woh
mention nahi hai — do sentences add karne layak, free credit.

**Finding 3 — `hw.cacheconfig: 8 1 4`** = 8 cores, **1 core per L1 (private)**,
**4 cores share L2 (cluster-wide)**. Yeh §5.3.2 ke contention argument ka aadhaar
confirm karta hai: shared caches contend karte hain, private nahi. (Pehla
`hw.cachesize` value 3.4 GB cache nahi, **memory** hai.)

---

# Part 2 — Question Bank

## Module 1 — The C Probe (Pointer-Chasing)

**1.1** A colleague suggests rewriting the probe in Python with NumPy, arguing
that NumPy's inner loops are C anyway. Give the quantitative argument for why
this cannot work, using the L1 latency you actually measured and a realistic
figure for CPython bytecode dispatch.

**1.2** The probe links slots into a *single Hamiltonian cycle* rather than a
random graph of pointers. What specific failure occurs if you build a random
graph instead, and at which end of the working-set range would you notice it?

**1.3** Randomisation defeats the stride prefetcher. Does it defeat *all*
prefetchers? Discuss with reference to Apple's data memory-dependent prefetcher
(Augury, [46]) and explain why your M1 results are still defensible.

**1.4** Explain why `stride` must be at least `sizeof(void *)`, and what class of
bug the guard at `wss_probe.c:281` prevents. Why is this a security-relevant
check and not merely a correctness one?

**1.5** *"The probe uses `lfence` and `mfence` to stop the out-of-order engine
reordering loads across the timer reads."* Evaluate this statement.

**1.6** Distinguish a **compiler barrier** from a **hardware fence**. Which does
`wss_probe.c` use, what does it compile to, and why is the other one unnecessary
*here* when it is mandatory in most microbenchmarks?

**1.7** Why `__rdtscp` rather than `rdtsc`? What does the extra `p` buy you, and
what would you have to add alongside `rdtsc` to get the same guarantee?

**1.8** The ARM path executes `isb` before `mrs cntvct_el0`. Is that a memory
fence? If not, what is it, and what would go wrong without it?

**1.9** Explain the difference between `void *volatile g_sink` and
`volatile void *g_sink`. Which does the code use, what does `-O3` do if you get
it wrong, and how would you *detect* that you had got it wrong from the output
alone?

**1.10** The timer on Apple Silicon ticks every ~41.7 ns; you report L1 hits of
~1.53 ns. Explain how measuring something 27× smaller than your clock's
resolution is legitimate, and state the assumption that makes it valid.

**1.11** Sweep order is seed-shuffled (`wss/__init__.py:93`) rather than
ascending. What systematic bias does this remove, and what would the corrupted
staircase have looked like?

**1.12** The probe reports the **minimum** over five repeats. Justify this against
the obvious alternative (the mean). What does the minimum hide, and where in the
dissertation is that cost acknowledged?

**1.13** Runtime calibration measures the tick rate against the OS monotonic
clock. Why is this *more* correct than reading the nominal CPU frequency from
`/proc/cpuinfo`, as the reference paper does — even on a machine where the TSC is
invariant?

---

## Module 2 — The ML Pipeline (Change-Point & Clustering)

**2.1** *"The productive pipeline uses PELT to detect the cache boundaries."*
Evaluate this statement, and explain what PELT is actually used for in this
project.

**2.2** State the contiguity lemma for 1-D *k*-means and prove it in two or three
lines. Why does it collapse the search space from a Stirling number to a binomial
coefficient?

**2.3** Given that lemma, explain the dynamic-programming recurrence in
`_exact_1d_kmeans`. What do the prefix-sum arrays `cs` and `cs2` buy you, and
what would the complexity be without them?

**2.4** Lloyd's algorithm reached the *same answer* as the exact DP at the
selected *k* on both machines. If the result is identical, what did the migration
actually buy — and why does the dissertation say so explicitly rather than
claiming an accuracy improvement?

**2.5** Both the clustering objective and the segmentation objective are
monotonically non-increasing in *k*. Explain why this means neither can select
its own *k*, and enumerate the three families of solution to that problem.

**2.6** Why is the Silhouette coefficient able to select *k* without a penalty
term when inertia cannot? What property of the Silhouette is doing the work?

**2.7** The Silhouette weights every observation equally. Explain precisely why
that is a threat to this project's central claim, and describe the experiment in
§5.4 that tests it. Was the threat realised?

**2.8** Why is segmentation performed on **log**-latency rather than raw
nanoseconds? Work through what happens to the L1→L2 step versus the L2→DRAM step
under a squared-error cost if you omit the log.

**2.9** BIC is the natural criterion for a Gaussian mixture, yet the project
scores the GMM by Silhouette instead. Give both reasons, and explain the
variance-heterogeneity argument with reference to the Intel L1 and DRAM bands.

**2.10** DBSCAN needs no *k*, which sounds ideal here. Why is it relegated to a
cross-check rather than promoted to the productive path? What does this reveal
about what "threshold-free" actually claims?

**2.11** The counting step is order-ignoring and the localisation step is
order-respecting. Defend this division of labour on the grounds of *sufficient
statistics*, and rebut the objection that discarding order throws away
information.

**2.12** Grønlund et al. [60] give an O(n log n) algorithm for the same problem;
the code implements O(kn²). Is that a defect? Justify your answer with the actual
input sizes.

**2.13** A hostile examiner says: "Your level count is stable with std 0.00, but
that is one run on a quiet machine." How do you respond, and what does
`data/intel_l3_quiesced/` show?

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
AI-generated description. The bibliography grew from 24 to 67 entries very late in
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
