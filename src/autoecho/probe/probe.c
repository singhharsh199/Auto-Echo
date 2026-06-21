#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>
#include <stdlib.h>

#if defined(__x86_64__) || defined(__i386__)
#include <x86intrin.h>

static inline uint64_t get_time(void) {
    unsigned int ui;
    return __rdtscp(&ui);
}

static inline void flush_cache(volatile void *p) {
    _mm_clflush((void*)p);
}

static inline void memory_fence(void) {
    _mm_mfence();
}

#elif defined(__aarch64__)
#ifdef __APPLE__
#include <mach/mach_time.h>
#endif

static inline uint64_t get_time(void) {
#ifdef __APPLE__
    return mach_absolute_time();
#else
    uint64_t val;
    asm volatile("mrs %0, cntvct_el0" : "=r" (val));
    return val;
#endif
}

static inline void flush_cache(volatile void *p) {
    // ARM userspace cache flush is typically not available or requires specific OS support
    // (e.g. __builtin___clear_cache for instruction cache, not data cache).
    // We do nothing here and rely on natural eviction for ARM fallback.
    (void)p;
}

static inline void memory_fence(void) {
    asm volatile("dmb ish" ::: "memory");
}
#else
#error "Unsupported architecture"
#endif


static PyObject* collect_latencies(PyObject* self, PyObject* args) {
    int num_samples;
    int mode; // 0 = L1/L2 (no flush), 1 = WPQ/DRAM (flush)
    
    if (!PyArg_ParseTuple(args, "ii", &num_samples, &mode)) {
        return NULL;
    }

    PyObject* latencies_list = PyList_New(num_samples);
    if (!latencies_list) {
        return NULL;
    }

    size_t array_size = 1024 * 1024 * 64; // 64 MB array
    volatile uint8_t *array = (volatile uint8_t *)malloc(array_size);
    if (!array) {
        PyErr_NoMemory();
        return NULL;
    }

    // Initialize array to prevent page faults during measurement
    for (size_t i = 0; i < array_size; i += 4096) {
        array[i] = 1;
    }

    for (int i = 0; i < num_samples; i++) {
        size_t idx = (rand() % (array_size / 64)) * 64; // 64-byte aligned access
        
        // Write to element to ensure it's modified (dirty cache line)
        array[idx] = (uint8_t)(i & 0xFF);
        memory_fence();

        if (mode == 1) {
            flush_cache(&array[idx]);
            memory_fence();
        }

        uint64_t start = get_time();
        
        // Read access
        volatile uint8_t val = array[idx];
        (void)val;
        
        // Prevent compiler from reordering
        memory_fence(); 
        
        uint64_t end = get_time();
        uint64_t latency = end - start;

        PyList_SetItem(latencies_list, i, PyLong_FromUnsignedLongLong(latency));
    }

    free((void*)array);
    return latencies_list;
}

static PyMethodDef ProbeMethods[] = {
    {"collect_latencies",  collect_latencies, METH_VARARGS,
     "Collect memory access latencies."},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

static struct PyModuleDef probemodule = {
    PyModuleDef_HEAD_INIT,
    "probe_c",   /* name of module */
    NULL, /* module documentation, may be NULL */
    -1,       /* size of per-interpreter state of the module,
                 or -1 if the module keeps state in global variables. */
    ProbeMethods
};

PyMODINIT_FUNC PyInit_probe_c(void) {
    return PyModule_Create(&probemodule);
}
