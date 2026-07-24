"""Validate discovered cache capacities against documented hardware ground truth.

Ground truth is read from the OS rather than hard-coded, so the framework
validates itself on whatever machine it runs on:
  * macOS  -> sysctl hw.perflevelN.* / hw.* cache sizes
  * Linux  -> /sys/devices/system/cpu/cpu0/cache/index*/size
"""
import platform
import subprocess


def _normalize_arch(arch: str) -> str:
    """Map the OS-reported machine token to a vendor-neutral ISA name.

    64-bit Windows (and Python's ``platform.machine()``) reports x86-64 as
    ``AMD64`` -- the name of the instruction set AMD designed -- even on Intel
    parts, which misreads as a CPU *vendor*. Normalise it (and the various
    aliases) to ``x86-64`` so an Intel run is not labelled 'AMD64'."""
    a = (arch or "").lower()
    if a in ("amd64", "x86_64", "x64", "em64t"):
        return "x86-64"
    if a in ("aarch64", "arm64"):
        return "arm64"
    return arch or "unknown"


def _clean_brand(brand: str) -> str:
    """Strip trademark noise and collapse whitespace so a brand string reads as
    e.g. 'Intel Core i5-13450HX' rather than 'Intel(R) Core(TM)  i5-13450HX'."""
    import re

    brand = re.sub(r"\((?:R|TM|tm|r)\)", "", brand or "")
    return re.sub(r"\s+", " ", brand).strip()


def get_machine_label() -> str:
    """Human-readable identifier for the machine under test, e.g.
    'Apple M1 (arm64, Darwin)' or 'Intel Core i5-13450HX (x86-64, Windows)'.
    Used to label each generated report so per-machine (M1 / Intel / M5)
    results can be told apart and slotted into the dissertation tables.

    The architecture token is normalised (``AMD64`` -> ``x86-64``) so an Intel
    run on Windows is not mislabelled with AMD's ISA name; the brand string is
    read via PowerShell CIM on Windows (``wmic`` is deprecated/removed on recent
    Windows 11 and silently fell back to the raw ``Intel64 Family 6 Model ...``
    processor string)."""
    system = platform.system()
    arch = _normalize_arch(platform.machine())
    brand = ""
    try:
        if system == "Darwin":
            brand = subprocess.check_output(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                stderr=subprocess.DEVNULL, text=True,
            ).strip()
        elif system == "Linux":
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if "model name" in line:
                        brand = line.split(":", 1)[1].strip()
                        break
        elif system == "Windows":
            # PowerShell CIM query for the marketing name (e.g. 'Intel(R)
            # Core(TM) i5-13450HX'); robust where the legacy `wmic` is absent.
            out = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command",
                 "(Get-CimInstance Win32_Processor).Name"],
                stderr=subprocess.DEVNULL, text=True,
            )
            lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
            brand = lines[0] if lines else ""
    except Exception:
        pass
    brand = _clean_brand(brand) or _clean_brand(platform.processor()) or "unknown CPU"
    return f"{brand} ({arch}, {system})"


def _sysctl(name: str):
    try:
        out = subprocess.check_output(["sysctl", "-n", name], stderr=subprocess.DEVNULL)
        return int(out.strip())
    except Exception:
        return None


def _windows_ground_truth_percore() -> dict:
    """Per-core data-cache sizes for CPU 0 via ``GetLogicalProcessorInformationEx``.

    The legacy WMI class ``Win32_CacheMemory`` reports **per-socket aggregate**
    sizes on hybrid Intel parts (e.g. L1 = 288 KiB = 6 x 48 KiB summed across the
    P-cores), which makes validation read 0% even when the per-core knees are
    correct. ``GetLogicalProcessorInformationEx(RelationCache, ...)`` instead
    returns one record per *physical* cache with its true (un-summed)
    ``CacheSize`` and the affinity mask of the logical processors it serves, so
    we can select exactly the data/unified caches that serve CPU 0 -- the P-core
    the probe pins to.

    Uses ctypes only (no native rebuild). Returns ``{}`` on any failure so the
    caller can fall back to the WMI path."""
    import ctypes
    import struct
    from ctypes import wintypes

    RelationCache = 2  # LOGICAL_PROCESSOR_RELATIONSHIP.RelationCache
    # PROCESSOR_CACHE_TYPE: 0=Unified, 1=Instruction, 2=Data, 3=Trace. A load-
    # latency sweep only exercises the data-side caches (Data + Unified).
    DATA_LIKE = (0, 2)

    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        glpi_ex = kernel32.GetLogicalProcessorInformationEx
        glpi_ex.argtypes = [wintypes.DWORD, ctypes.c_void_p,
                            ctypes.POINTER(wintypes.DWORD)]
        glpi_ex.restype = wintypes.BOOL

        length = wintypes.DWORD(0)
        # First call sizes the buffer (returns FALSE / ERROR_INSUFFICIENT_BUFFER).
        glpi_ex(RelationCache, None, ctypes.byref(length))
        if length.value == 0:
            return {}
        buf = (ctypes.c_byte * length.value)()
        if not glpi_ex(RelationCache, buf, ctypes.byref(length)):
            return {}
        raw = bytes(buf)
    except Exception:
        return {}

    gt = {}
    pos, n = 0, length.value
    while pos + 8 <= n:
        # SYSTEM_LOGICAL_PROCESSOR_INFORMATION_EX header: Relationship, Size.
        relationship = struct.unpack_from("<I", raw, pos)[0]
        size = struct.unpack_from("<I", raw, pos + 4)[0]
        if size == 0:
            break
        if relationship == RelationCache:
            # CACHE_RELATIONSHIP begins at offset 8 (the union is 8-byte aligned):
            #   Level(BYTE@0) Assoc(BYTE@1) LineSize(WORD@2) CacheSize(DWORD@4)
            #   Type(DWORD@8) ... GroupMask.Mask(KAFFINITY@32) Group(WORD@40).
            # The first GROUP_AFFINITY sits at offset 32 in BOTH the pre-20H2
            # (Reserved[20]) and 20H2+ (Reserved[18]+GroupCount WORD) layouts.
            c = pos + 8
            level = raw[c + 0]
            cache_size = struct.unpack_from("<I", raw, c + 4)[0]
            ctype = struct.unpack_from("<I", raw, c + 8)[0]
            mask = struct.unpack_from("<Q", raw, c + 32)[0]
            group = struct.unpack_from("<H", raw, c + 40)[0]
            serves_cpu0 = (group == 0) and bool(mask & 1)
            if ctype in DATA_LIKE and serves_cpu0 and cache_size > 0:
                key = f"L{level}"
                # CPU 0 is served by exactly one data/unified cache per level; if
                # a level somehow recurs, keep the smaller (closer, more private)
                # one rather than a larger shared duplicate.
                if key not in gt or cache_size < gt[key]:
                    gt[key] = cache_size
        pos += size
    return gt


def _windows_ground_truth_cim() -> dict:
    """Labelled fallback: cache sizes via WMI ``Win32_CacheMemory`` (CIM).

    NOTE: on hybrid Intel parts this reports per-socket **aggregate** sizes (L1
    summed across cores), so it can over-count and mismatch a per-core sweep --
    it is used only when the accurate per-core
    ``GetLogicalProcessorInformationEx`` path is unavailable. Level: 3->L1,
    4->L2, 5->L3; MaxCacheSize is in KiB."""
    gt = {}
    try:
        import json

        out = subprocess.check_output(
            [
                "powershell", "-NoProfile", "-Command",
                "Get-CimInstance Win32_CacheMemory | "
                "Select-Object Level,MaxCacheSize | ConvertTo-Json",
            ],
            stderr=subprocess.DEVNULL, text=True,
        )
        data = json.loads(out)
        if isinstance(data, dict):
            data = [data]
        level_map = {3: "L1", 4: "L2", 5: "L3"}
        for entry in data:
            name = level_map.get(entry.get("Level"))
            size_kb = entry.get("MaxCacheSize")
            if name and size_kb:
                size = int(size_kb) * 1024
                # Keep the largest instance reported for each level.
                if name not in gt or size > gt[name]:
                    gt[name] = size
    except Exception:
        pass
    return gt


def get_ground_truth() -> dict:
    """Return documented data-cache capacities in bytes, keyed by level name.

    Only the data-side caches that appear in a load-latency sweep are returned
    (L1d, L2, L3 if present). Apple Silicon exposes per-core-type ("perflevel")
    caches and has no conventional L3, so the performance-core figures are used.
    """
    system = platform.system()
    gt = {}

    if system == "Darwin":
        # Prefer performance-core caches (perflevel0); the QoS hint in the probe
        # biases measurement onto these cores.
        l1 = _sysctl("hw.perflevel0.l1dcachesize") or _sysctl("hw.l1dcachesize")
        l2 = _sysctl("hw.perflevel0.l2cachesize") or _sysctl("hw.l2cachesize")
        l3 = _sysctl("hw.l3cachesize")  # usually absent on Apple Silicon
        if l1:
            gt["L1"] = l1
        if l2:
            gt["L2"] = l2
        if l3:
            gt["L3"] = l3

    elif system == "Linux":
        base = "/sys/devices/system/cpu/cpu0/cache"
        try:
            import os

            for idx in sorted(os.listdir(base)):
                d = os.path.join(base, idx)
                try:
                    with open(os.path.join(d, "level")) as f:
                        level = int(f.read().strip())
                    with open(os.path.join(d, "type")) as f:
                        ctype = f.read().strip()
                    with open(os.path.join(d, "size")) as f:
                        size_str = f.read().strip()
                except FileNotFoundError:
                    continue
                if ctype == "Instruction":
                    continue  # not exercised by a load-latency sweep
                mult = 1024 if size_str.endswith("K") else (
                    1024 * 1024 if size_str.endswith("M") else 1
                )
                size = int(size_str.rstrip("KM")) * mult
                gt[f"L{level}"] = size
        except Exception:
            pass

    elif system == "Windows":
        # Per-core sizes via GetLogicalProcessorInformationEx are correct; the WMI
        # Win32_CacheMemory path is a labelled fallback reporting per-socket
        # AGGREGATE sizes -- the cause of the historical 0% validation on hybrid
        # Intel parts. Prefer per-core; fall back only if it yields nothing.
        gt = _windows_ground_truth_percore() or _windows_ground_truth_cim()

    return gt


def validate(detected_capacities: list, tolerance_octaves: float = 1.0,
             ground_truth: dict = None) -> dict:
    """Compare detected cache capacities to ground truth.

    A detected capacity matches a ground-truth cache if they are within
    ``tolerance_octaves`` (default 1.0 => within a factor of 2) on a log2 scale.
    Matching in log-space is the natural metric because cache sizes are powers
    of two and the sweep samples them geometrically.

    Detected knees are assigned to documented caches by **optimal one-to-one
    (Hungarian) assignment** minimising total log2 error, not greedy
    nearest-first: greedy can undercount when two adjacent caches both fall
    within tolerance of the detected knees. Both **recall** (documented caches
    found) *and* **precision** (detected knees that are real caches) are reported
    -- a discovery tool must be judged on false positives too, since a spurious
    knee (e.g. a TLB-transition artefact) within an octave of a real cache would
    otherwise be silently credited as a hit.

    :param ground_truth: documented cache sizes; if ``None`` they are read from
        the OS. Injectable so callers can pass a cached reading (avoiding
        repeated OS queries) and so tests can supply deterministic values.
    :returns: dict with per-cache match results, ``recall``/``precision``/``f1``,
        and ``accuracy`` (retained as an alias of recall for backward compat).
    """
    import math

    import numpy as np
    from scipy.optimize import linear_sum_assignment

    gt = ground_truth if ground_truth is not None else get_ground_truth()
    detected = sorted(float(c) for c in detected_capacities if c == c and c > 0)
    gt_items = sorted(gt.items(), key=lambda kv: kv[1])
    n_gt, n_det = len(gt_items), len(detected)

    # Optimal assignment over the log2-error matrix; infeasible (out-of-tolerance)
    # pairs are given a prohibitive cost and rejected afterwards, so the match
    # count is the maximum achievable within tolerance.
    match_for_gt = [None] * n_gt
    used = [False] * n_det
    matched = 0
    INFEASIBLE = 1e9
    if n_gt and n_det:
        cost = np.full((n_gt, n_det), INFEASIBLE)
        for i, (_, gt_size) in enumerate(gt_items):
            for j, d in enumerate(detected):
                err = abs(math.log2(d / gt_size))
                if err <= tolerance_octaves:
                    cost[i, j] = err
        rows, cols = linear_sum_assignment(cost)
        for i, j in zip(rows, cols):
            if cost[i, j] < INFEASIBLE:
                match_for_gt[i] = int(j)
                used[j] = True
                matched += 1

    results = []
    for i, (name, gt_size) in enumerate(gt_items):
        j = match_for_gt[i]
        det_bytes = detected[j] if j is not None else None
        err_oct = abs(math.log2(det_bytes / gt_size)) if det_bytes is not None else None
        pct_err = (
            100.0 * (det_bytes - gt_size) / gt_size if det_bytes is not None else None
        )
        results.append(
            {
                "cache": name,
                "ground_truth_bytes": gt_size,
                "detected_bytes": det_bytes,
                "error_octaves": err_oct,
                "pct_error": pct_err,
                "match": j is not None,
            }
        )

    # Recall = documented caches found; precision = detected knees that ARE real
    # caches (the rest -- e.g. TLB-transition artefacts -- are false positives).
    n_false_positive = sum(1 for u in used if not u)
    recall = matched / n_gt if n_gt else 0.0
    precision = matched / n_det if n_det else 0.0
    f1 = (2 * precision * recall / (precision + recall)
          if (precision + recall) > 0 else 0.0)
    return {
        "ground_truth": gt,
        "detected_capacities": detected,
        "matches": results,
        "n_ground_truth": n_gt,
        "n_matched": matched,
        "n_detected": n_det,
        "n_false_positive": n_false_positive,
        "accuracy": recall,  # alias of recall, retained for backward compatibility
        "recall": recall,
        "precision": precision,
        "f1": f1,
    }
