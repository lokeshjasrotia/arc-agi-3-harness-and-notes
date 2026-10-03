"""arcbench: reproducible benchmarking utilities for ARC-AGI-3 agents.

The package is deliberately split into

* pure modules (``schema``, ``gitinfo``, ``report``) that need nothing beyond the
  standard library and are unit-tested in CI, and
* ``runner`` / ``loader``, which need the ``arc-agi`` engine and the vendored
  ARC-AGI-3-Agents framework and are therefore exercised on a developer machine.
"""

__version__ = "0.1.0"
