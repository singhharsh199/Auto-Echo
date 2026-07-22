"""Validate discovered cache capacities against documented hardware ground truth.

Ground truth is read from the OS rather than hard-coded, so the framework
validates itself on whatever machine it runs on:
  * macOS  -> sysctl hw.perflevelN.* / hw.* cache sizes
  * Linux  -> /sys/devices/system/cpu/cpu0/cache/index*/size
"""
import platform
import subprocess


def get_machine_label() -> str:
    """Human-readable identifier for the machine under test, e.g.
    'Apple M1 (arm64, Darwin)' or 'Intel(R) Core(TM) i7-... (x86_64, Linux)'.
    Used to label each generated report so per-machine (M1 / Intel / AMD)
    results can be told apart and slotted into the dissertation tables."""
    system = platform.system()
    arch = platform.machine()
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
            brand = (subprocess.check_output(
                ["wmic", "cpu", "get", "name"], stderr=subprocess.DEVNULL, text=True,
            ).splitlines()[1:] or [""])[0].strip()
    except Exception:
        pass
    brand = brand or platform.processor() or "unknown CPU"
    return f"{brand} ({arch}, {system})"


def _sysctl(name: str):
    try:
        out = subprocess.check_output(["sysctl", "-n", name], stderr=subprocess.DEVNULL)
        return int(out.strip())
    except Exception:
        return None


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
        # Best-effort via CIM. Win32_CacheMemory.Level: 3->L1, 4->L2, 5->L3;
        # MaxCacheSize is in KiB. Verify against vendor docs, as some firmware
        # reports these fields inconsistently.
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


def validate(detected_capacities: list, tolerance_octaves: float = 1.0,
             ground_truth: dict = None) -> dict:
    """Compare detected cache capacities to ground truth.

    A detected capacity matches a ground-truth cache if they are within
    ``tolerance_octaves`` (default 1.0 => within a factor of 2) on a log2 scale.
    Matching in log-space is the natural metric because cache sizes are powers
    of two and the sweep samples them geometrically.

    :param ground_truth: documented cache sizes; if ``None`` they are read from
        the OS. Injectable so callers can pass a cached reading (avoiding
        repeated OS queries) and so tests can supply deterministic values.
    :returns: dict with per-cache match results and an overall accuracy.
    """
    import math

    gt = ground_truth if ground_truth is not None else get_ground_truth()
    detected = sorted(float(c) for c in detected_capacities if c == c and c > 0)

    results = []
    used = [False] * len(detected)
    matched = 0
    for name, gt_size in sorted(gt.items(), key=lambda kv: kv[1]):
        best_j, best_err = None, None
        for j, d in enumerate(detected):
            if used[j]:
                continue
            err = abs(math.log2(d / gt_size))
            if best_err is None or err < best_err:
                best_err, best_j = err, j
        ok = best_j is not None and best_err <= tolerance_octaves
        if ok:
            used[best_j] = True
            matched += 1
        det_bytes = detected[best_j] if best_j is not None else None
        pct_err = (
            100.0 * (det_bytes - gt_size) / gt_size if det_bytes is not None else None
        )
        results.append(
            {
                "cache": name,
                "ground_truth_bytes": gt_size,
                "detected_bytes": det_bytes,
                "error_octaves": best_err,
                "pct_error": pct_err,
                "match": ok,
            }
        )

    accuracy = matched / len(gt) if gt else 0.0
    return {
        "ground_truth": gt,
        "detected_capacities": detected,
        "matches": results,
        "n_ground_truth": len(gt),
        "n_matched": matched,
        "accuracy": accuracy,
    }
