# Project Overview

## Project

Lightweight Hybrid Intrusion Detection System for small-scale networks.

## Current Scope

- Release 1.0 focuses on Tier 1 rule-based detection.
- The system captures traffic, extracts flow features, evaluates rule thresholds, and writes alerts and metrics to InfluxDB.
- Grafana provides the dashboard layer.

## Future Scope

- Tier 2 machine-learning detection is conditional and should stay separated from the active release unless implementation begins.
- Keep future work visible in shared context, but do not mix it into current sprint work unless it is active.

## Constraints

- Optimize for low CPU and memory usage.
- Analyze metadata and flow behavior, not payload content.
- Assume Docker-based deployment on Linux with network capture privileges.

## Canonical Sources

- `documents/md/SRS-v1.md`
- `documents/md/SDD.md`
- `documents/md/Project Proposal.md`
