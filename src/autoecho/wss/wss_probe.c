/*
 * Auto-Echo: Working-Set-Size (WSS) pointer-chasing probe.
 *
 * Cross-platform: Linux / macOS / Windows on x86-64, plus ARM64 (Apple Silicon
 * and ARM Linux). Measures the average latency of a data-dependent pointer
 * chase over a buffer of a given working-set size. As the buffer grows past
 * each cache level's capacity the average latency steps up; that staircase is
 * what makes the levels separable (cf. lmbench lat_mem_rd, Yotov et al.).
 *
 * Why this design:
 *   1. Data-dependent loads defeat the hardware prefetcher with NO explicit
 *      cache flush -- essential where none exists in user space (ARM/macOS).
 *   2. Batch amortisation: 10^6+ dependent hops timed in one window / hop count
 *      gives sub-nanosecond effective resolution despite coarse timers.
 *   3. Tick->ns conversion is CALIBRATED at runtime against the OS monotonic
 *      clock, so it is correct on every platform (invariant TSC, ARM cntvct,
 *      Windows QPC) without hard-coding any frequency.
 */

#if defined(__linux__) && !defined(_GNU_SOURCE)
#define _GNU_SOURCE /* for sched_setaffinity; must precede all includes */
#endif

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

/* ---------- monotonic wall clock (for timer calibration) ---------- */
#if defined(_WIN32)
#include <windows.h>
static double wall_ns(void) {
    LARGE_INTEGER c, f;
    QueryPerformanceCounter(&c);
    QueryPerformanceFrequency(&f);
    return (double)c.QuadPart * 1e9 / (double)f.QuadPart;
}
#else
#include <time.h>
static double wall_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec * 1e9 + (double)ts.tv_nsec;
}
#endif

/* ---------- high-resolution tick counter (per architecture) ---------- */
#if defined(_MSC_VER)
#include <intrin.h>
#endif

#if defined(__x86_64__) || defined(__i386__) || defined(_M_X64) || defined(_M_IX86)
#if !defined(_MSC_VER)
#include <x86intrin.h>
#endif
static inline uint64_t get_ticks(void) {
    unsigned int aux;
    return __rdtscp(&aux);
}
#elif defined(__aarch64__)
#ifdef __APPLE__
#include <mach/mach_time.h>
#include <pthread/qos.h>
static inline uint64_t get_ticks(void) { return mach_absolute_time(); }
#else
static inline uint64_t get_ticks(void) {
    uint64_t v;
    // ISB prevents the counter read being speculated across the timed region;
    // the memory clobber stops the compiler reordering loads across it.
    asm volatile("isb; mrs %0, cntvct_el0" : "=r"(v) :: "memory");
    return v;
}
#endif
#else
#error "Unsupported architecture"
#endif

/* ---------- thread affinity / QoS: keep the probe on one core so plateaus
 * are not blurred by migration between core types ---------- */
#if defined(__linux__)
#include <sched.h>
#endif

static void pin_and_boost(void) {
#if defined(__APPLE__) && defined(__aarch64__)
    /* Bias onto a performance core (M1 P-core: 128 KB L1d, 12 MB L2). */
    pthread_set_qos_class_self_np(QOS_CLASS_USER_INTERACTIVE, 0);
#elif defined(__linux__)
    cpu_set_t set;
    CPU_ZERO(&set);
    CPU_SET(0, &set); /* CPU 0 is a performance core on hybrid Intel */
    sched_setaffinity(0, sizeof(set), &set);
#elif defined(_WIN32)
    SetThreadAffinityMask(GetCurrentThread(), (DWORD_PTR)1);
#endif
}

/* Deterministic, portable RNG (xorshift64): reproducible given a fixed seed. */
static inline uint64_t xorshift64(uint64_t *state) {
    uint64_t x = *state;
    x ^= x << 13;
    x ^= x >> 7;
    x ^= x << 17;
    *state = x;
    return x;
}

/* Portable compiler barrier: forbids the compiler from moving the timed loads
 * across the timer reads (a hardware fence is unnecessary because the pointer
 * chase is already fully serialised by data dependencies). */
#if defined(_MSC_VER)
#define COMPILER_BARRIER() _ReadWriteBarrier()
#else
#define COMPILER_BARRIER() __asm__ __volatile__("" ::: "memory")
#endif

/* NOTE the placement: `void *volatile` is a *volatile pointer*, so the store
 * `g_sink = p` below is a required side effect and the compiler must keep the
 * dependent-load chase that produces p. Writing `volatile void *` instead makes
 * only the pointee volatile, leaving the store dead -- which lets -O3 (notably
 * GCC) delete the entire measured loop and report physically impossible ~0 ns. */
static void *volatile g_sink;

/* Page-aligned allocation (like the reference paper's posix_memalign). Alignment
 * only guarantees a cache line never straddles two pages; it does NOT reduce TLB
 * pressure -- the number of distinct pages touched grows with the working-set
 * size regardless of alignment, so the deep-memory plateau still includes
 * page-walk latency (see the Threats to Validity discussion). 16 KiB covers
 * Apple Silicon's page size and is a multiple of x86's 4 KiB. */
#define AE_ALIGN 16384
static void *aligned_alloc_portable(size_t size) {
#if defined(_WIN32)
    return _aligned_malloc(size, AE_ALIGN);
#else
    void *p = NULL;
    if (posix_memalign(&p, AE_ALIGN, size) != 0) return NULL;
    return p;
#endif
}
static void aligned_free_portable(void *p) {
#if defined(_WIN32)
    _aligned_free(p);
#else
    free(p);
#endif
}

/*
 * calibrate() -> nanoseconds per hardware tick.
 * Counts ticks over ~50 ms of monotonic wall-clock time. Correct on every
 * platform because it measures the real tick rate rather than assuming one.
 */
static PyObject *calibrate(PyObject *self, PyObject *args) {
    (void)self;
    (void)args;
    pin_and_boost();

    const double target_ns = 50e6; /* 50 ms */
    volatile uint64_t spin = 0;
    double w0 = wall_ns();
    uint64_t t0 = get_ticks();
    double w1;
    uint64_t t1;
    do {
        for (int i = 0; i < 2000; i++) spin += (uint64_t)i;
        w1 = wall_ns();
        t1 = get_ticks();
    } while (w1 - w0 < target_ns);

    uint64_t dticks = t1 - t0;
    if (dticks == 0) return PyFloat_FromDouble(1.0);
    return PyFloat_FromDouble((w1 - w0) / (double)dticks);
}

/*
 * measure_wss(size_bytes, stride, hops, repeats, seed) -> min ticks-per-access.
 * The caller converts ticks to ns using calibrate(). Returns the MINIMUM over
 * repeats: interference can only add time, so the fastest run is the best
 * estimate of true latency (standard lmbench practice).
 */
static PyObject *measure_wss(PyObject *self, PyObject *args) {
    (void)self;
    Py_ssize_t size_bytes, stride, hops, repeats;
    unsigned long long seed;

    if (!PyArg_ParseTuple(args, "nnnnK", &size_bytes, &stride, &hops,
                          &repeats, &seed)) {
        return NULL;
    }
    if (stride <= 0 || size_bytes < stride || hops <= 0 || repeats <= 0) {
        PyErr_SetString(PyExc_ValueError, "invalid probe parameters");
        return NULL;
    }
    /* Each slot must hold the pointer written into it during chase linking;
     * a sub-pointer stride would overflow the last slot's 8-byte store. */
    if (stride < (Py_ssize_t)sizeof(void *)) {
        PyErr_SetString(PyExc_ValueError,
                        "stride must be >= sizeof(void*) (pointer chase)");
        return NULL;
    }

    pin_and_boost();

    size_t nslots = (size_t)(size_bytes / stride);
    if (nslots < 2) nslots = 2;

    char *base = (char *)aligned_alloc_portable(nslots * (size_t)stride);
    size_t *order = (size_t *)malloc(nslots * sizeof(size_t));
    if (!base || !order) {
        aligned_free_portable(base);
        free(order);
        return PyErr_NoMemory();
    }

    uint64_t rng = seed ? seed : 0x9E3779B97F4A7C15ULL;

    /* Fisher-Yates shuffle, then link into a single Hamiltonian cycle so the
     * chase visits every slot once before repeating. Writing every slot also
     * pre-faults every page. */
    for (size_t i = 0; i < nslots; i++) order[i] = i;
    for (size_t i = nslots - 1; i > 0; i--) {
        size_t j = (size_t)(xorshift64(&rng) % (i + 1));
        size_t t = order[i];
        order[i] = order[j];
        order[j] = t;
    }
    for (size_t k = 0; k < nslots; k++) {
        char *slot = base + order[k] * (size_t)stride;
        char *next = base + order[(k + 1) % nslots] * (size_t)stride;
        *(void **)slot = (void *)next;
    }
    char *start = base + order[0] * (size_t)stride;

    double best = -1.0;

    Py_BEGIN_ALLOW_THREADS
    for (Py_ssize_t r = 0; r < repeats; r++) {
        /* Warm-up: one full traversal brings the working set to steady state. */
        void **p = (void **)start;
        for (size_t w = 0; w < nslots; w++) p = (void **)(*p);
        g_sink = (void *)p;

        p = (void **)start;
        COMPILER_BARRIER();
        uint64_t c0 = get_ticks();
        for (Py_ssize_t h = 0; h < hops; h++) {
            p = (void **)(*p);
        }
        uint64_t c1 = get_ticks();
        COMPILER_BARRIER();
        g_sink = (void *)p;

        double per_access = (double)(c1 - c0) / (double)hops;
        if (best < 0.0 || per_access < best) best = per_access;
    }
    Py_END_ALLOW_THREADS

    aligned_free_portable(base);
    free(order);
    return PyFloat_FromDouble(best);
}

static PyMethodDef WssMethods[] = {
    {"measure_wss", measure_wss, METH_VARARGS,
     "Measure min ticks-per-access for a pointer chase over a working-set size."},
    {"calibrate", calibrate, METH_NOARGS,
     "Measure nanoseconds per hardware tick against the OS monotonic clock."},
    {NULL, NULL, 0, NULL}};

static struct PyModuleDef wssmodule = {
    PyModuleDef_HEAD_INIT, "wss_probe_c", NULL, -1, WssMethods};

PyMODINIT_FUNC PyInit_wss_probe_c(void) { return PyModule_Create(&wssmodule); }
