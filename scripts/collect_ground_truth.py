#!/usr/bin/env python3
"""Collect and cross-check the OS-reported cache ground truth on this machine.

The dissertation validates every detected capacity against ground truth read from
the operating system. That makes the ground truth itself a reference standard, so
it needs verifying rather than assuming. This script prints, for the machine it is
run on:

1. What ``autoecho.validation.get_ground_truth()`` actually returns -- the values
   §5 scores against.
2. The **raw OS sources** behind those values, including the *generic* keys the
   framework deliberately does **not** use. On a heterogeneous (performance +
   efficiency core) die the generic keys report the efficiency cluster, so using
   them would score a performance-core probe against the wrong reference.
3. An **independent cross-check** from ``hwloc``/``lstopo`` if it is installed
   (``brew install hwloc`` / ``apt install hwloc`` / hwloc Windows binaries), plus
   ``coreinfo`` on Windows if present.

Run it on every machine that appears in §5.1 and paste the output into the
dissertation's ground-truth provenance table.

Usage::

    python scripts/collect_ground_truth.py
"""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys


def _run(cmd: list[str]) -> str | None:
    """Run a command, returning stdout, or None if it is unavailable/fails."""
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout if out.returncode == 0 else None


def _human(n: float) -> str:
    for unit in ("B", "KiB", "MiB", "GiB"):
        if abs(n) < 1024.0:
            return f"{n:.0f} {unit}"
        n /= 1024.0
    return f"{n:.1f} TiB"


def _rule(title: str) -> None:
    print(f"\n{'=' * 72}\n{title}\n{'=' * 72}")


def framework_view() -> None:
    """What the pipeline itself reads -- the values §5 scores against."""
    _rule("1. What the framework reads (autoecho.validation.get_ground_truth)")
    try:
        from autoecho.validation import get_ground_truth, get_machine_label
    except ImportError as e:
        print(f"  autoecho not importable ({e}).")
        print("  Run `pip install -e .` from the repository root first.")
        return
    print(f"  machine label : {get_machine_label()}")
    gt = get_ground_truth()
    if not gt:
        print("  (no ground truth reported on this platform)")
        return
    for name, size in sorted(gt.items(), key=lambda kv: kv[1]):
        print(f"  {name:<4} : {size:>10} B  = {_human(size)}")


def macos_sources() -> None:
    """macOS: per-performance-level keys vs the generic ones."""
    _rule("2. Raw OS sources (macOS sysctl)")
    keys_percore = [
        "hw.perflevel0.l1dcachesize",
        "hw.perflevel0.l1icachesize",
        "hw.perflevel0.l2cachesize",
        "hw.perflevel1.l1dcachesize",
        "hw.perflevel1.l2cachesize",
    ]
    keys_generic = ["hw.l1dcachesize", "hw.l1icachesize", "hw.l2cachesize"]
    misc = ["hw.cachelinesize", "hw.cacheconfig", "hw.cachesize", "hw.pagesize"]

    print("  -- per-performance-level (perflevel0 = P-cores; what the framework uses)")
    for k in keys_percore:
        out = _run(["sysctl", "-n", k])
        if out:
            v = out.strip()
            extra = f"  = {_human(int(v))}" if v.isdigit() else ""
            print(f"    {k:<32} {v}{extra}")

    print("\n  -- GENERIC keys (deliberately NOT used: they report the E-cluster)")
    for k in keys_generic:
        out = _run(["sysctl", "-n", k])
        if out:
            v = out.strip()
            extra = f"  = {_human(int(v))}" if v.isdigit() else ""
            print(f"    {k:<32} {v}{extra}")

    print("\n  -- other")
    for k in misc:
        out = _run(["sysctl", "-n", k])
        if out:
            print(f"    {k:<32} {out.strip()}")

    print("\n  -- any mention of an L3 / system-level cache?")
    out = _run(["sysctl", "-a"])
    hits = [
        ln
        for ln in (out or "").splitlines()
        if any(t in ln.lower() for t in ("slc", "systemlevel", "system_level", "l3cache"))
    ]
    print("    " + ("\n    ".join(hits) if hits else "NONE — no L3/SLC entry exists"))


def windows_sources() -> None:
    """Windows: per-core (GetLogicalProcessorInformationEx) vs per-socket (WMI)."""
    _rule("2. Raw OS sources (Windows)")

    print("  -- per-core, via GetLogicalProcessorInformationEx (what the framework uses)")
    try:
        from autoecho.validation import _windows_ground_truth_percore

        gt = _windows_ground_truth_percore()
        if gt:
            for name, size in sorted(gt.items(), key=lambda kv: kv[1]):
                print(f"    {name:<4} : {size:>10} B  = {_human(size)}")
        else:
            print("    (returned nothing)")
    except Exception as e:  # noqa: BLE001 - diagnostic script, report anything
        print(f"    unavailable: {e}")

    print(
        "\n  -- per-SOCKET aggregate, via legacy Win32_CacheMemory (NOT used; for contrast)"
    )
    ps = shutil.which("powershell") or shutil.which("pwsh")
    if ps:
        out = _run(
            [
                ps,
                "-NoProfile",
                "-Command",
                "Get-CimInstance Win32_CacheMemory | "
                "Select-Object Purpose,InstalledSize,Level | Format-Table -AutoSize",
            ]
        )
        print("    " + "\n    ".join((out or "(no output)").strip().splitlines()))
    else:
        print("    powershell not found")

    print("\n  -- logical processor / core counts")
    if ps:
        out = _run(
            [
                ps,
                "-NoProfile",
                "-Command",
                "Get-CimInstance Win32_Processor | Select-Object Name,"
                "NumberOfCores,NumberOfLogicalProcessors | Format-List",
            ]
        )
        print("    " + "\n    ".join((out or "(no output)").strip().splitlines()))

    print("\n  -- coreinfo (Sysinternals), if installed: per-core cache topology")
    ci = shutil.which("coreinfo") or shutil.which("coreinfo64")
    if ci:
        out = _run([ci, "-c", "-nobanner", "-accepteula"])
        print("    " + "\n    ".join((out or "(no output)").strip().splitlines()[:40]))
    else:
        print(
            "    coreinfo not found — https://learn.microsoft.com/sysinternals/downloads/coreinfo"
        )


def linux_sources() -> None:
    """Linux: sysfs cache indices for CPU 0."""
    _rule("2. Raw OS sources (Linux sysfs)")
    from pathlib import Path

    base = Path("/sys/devices/system/cpu/cpu0/cache")
    if not base.exists():
        print(f"  {base} does not exist")
        return
    for idx in sorted(base.glob("index*")):
        fields = {}
        for f in ("level", "type", "size", "ways_of_associativity", "shared_cpu_list"):
            p = idx / f
            if p.exists():
                fields[f] = p.read_text().strip()
        print(f"  {idx.name}: {fields}")
    out = _run(["lscpu"])
    if out:
        print("\n  -- lscpu cache lines")
        for ln in out.splitlines():
            if "cache" in ln.lower():
                print(f"    {ln.strip()}")


def independent_check() -> None:
    """hwloc: an implementation independent of this project's own reader."""
    _rule("3. Independent cross-check (hwloc / lstopo)")
    exe = shutil.which("lstopo-no-graphics") or shutil.which("lstopo")
    if not exe:
        print("  lstopo not installed. Install with:")
        print("    macOS   : brew install hwloc")
        print("    Ubuntu  : sudo apt-get install -y hwloc")
        print("    Windows : https://www.open-mpi.org/projects/hwloc/ (binary zip)")
        return
    out = _run([exe, "--of", "console"]) or _run([exe])
    print("  " + "\n  ".join((out or "(no output)").strip().splitlines()))
    print(
        "\n  NOTE: hwloc reads the same OS interfaces this project does, so it is an\n"
        "  independent *implementation*, not an independent *source*. A cache absent\n"
        "  from the OS (e.g. the M1 System-Level Cache) is absent here too — which is\n"
        "  itself the point §2.2 makes about the chain of trust."
    )


def main() -> None:
    print("Auto-Echo — ground-truth provenance report")
    print(f"platform : {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"python   : {sys.version.split()[0]}")

    framework_view()

    system = platform.system()
    if system == "Darwin":
        macos_sources()
    elif system == "Windows":
        windows_sources()
    elif system == "Linux":
        linux_sources()
    else:
        print(f"\n(no raw-source collector for {system})")

    independent_check()
    print("\nDone. Paste this output into the dissertation's ground-truth table.\n")


if __name__ == "__main__":
    main()
