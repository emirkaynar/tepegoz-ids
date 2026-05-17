# Lessons Learned

## Purpose

Record verified approaches that worked so future sessions can reuse them.

## Entries

- Use the repo-local `.ai/` tree as the single shared AI coordination layer.
- Keep Tier 1 work separate from future Tier 2 work unless Tier 2 is actively being implemented.
- Keep `current-sprint.md` low-churn and update it only on meaningful work changes.
- Metadata-only analysis (ETA approach) is sufficient for detecting volumetric attacks and behavioral anomalies without payload inspection.
- Deterministic rule-based detection is fast enough for Tier 1 when rule evaluation is O(1) and flow state is bounded.
- Batching InfluxDB writes reduces I/O overhead without sacrificing alert responsiveness when alerts and metrics are on separate write schedules.
- Performance measurement should happen early and often; speculate on bottlenecks but verify with actual metrics.
- Native host deployment for the sensor reduces container bridge noise and simplifies direction semantics for real traffic.
- A split-product UX works well: install sensor first, then bootstrap dashboard stack on demand via a dedicated command.
- **Python Subprocess:** Never use `shell=True` when passing a list of arguments to `subprocess.run` on POSIX/WSL; it causes interactive shell hangs. Use a single string with `shell=True` or a list without `shell=True`.
- **Debian Packaging:** Avoid manual systemd management in `postinst/prerm` scripts; use the `#DEBHELPER#` token and let `dh_installsystemd` generate standard, safe snippets.
- **GPG Keyrings:** Modern `apt` (Ubuntu 24.04+) requires GPG keys to be dearmored (binary format) when stored in `/etc/apt/keyrings/` for `[signed-by=...]` usage.
- **InfluxDB CLI:** The InfluxDB CLI (`influx`) stores persistent config in `~/.influxdbv2/configs`. This state must be cleared manually during resets, or it will conflict with fresh `influx setup` calls.
- **Dpkg Interactive Prompts:** Use `-o Dpkg::Options::=--force-confold --force-confdef` with `apt-get install` to prevent hidden interactive prompts from hanging non-interactive scripts.
