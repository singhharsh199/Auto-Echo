"""Auto-Echo: automated discovery of memory-hierarchy latency patterns from user space.

The package is organised as the four-stage pipeline described in §3 of the
dissertation:

* :mod:`autoecho.wss` -- the native working-set-size pointer-chase probe.
* :mod:`autoecho.analysis` -- level discovery: exact 1-D k-means counts the
  levels, change-point detection localises each capacity.
* :mod:`autoecho.evaluation` -- comparative scoring of the level counters
  across independent sweeps.
* :mod:`autoecho.validation` -- comparison against OS-reported ground truth.

:mod:`autoecho.report` renders the Markdown report and figures. The
:mod:`autoecho.probe`, :mod:`autoecho.preprocessing` and
:mod:`autoecho.clustering` modules implement the superseded sample-based
baseline, retained as the documented negative result of §4.

Entry point: ``python -m autoecho --method wss``.
"""
