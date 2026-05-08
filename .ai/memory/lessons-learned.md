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
