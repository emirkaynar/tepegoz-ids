# Backlog

## Purpose

Approved work that is not active yet belongs here.

## Rules

- Keep items short and actionable.
- Link each item to the relevant context, decision, or design file.
- Move an item into `current-sprint.md` only when the work becomes actively owned and meaningful.

## Current Items

- Define the rule schema and alert shape for the rule engine. (See ADR-004)
- Document Tier 2 entry criteria so ML work stays conditional and separated. (See ADR-002)
- Scaffold the Custom Grafana App Plugin (React) for rules configuration. (See ADR-009)
- Implement headless FastAPI configuration API as a separate Docker service. (See ADR-009)
- Optional: Add persistence reliability hardening for InfluxDB writes (bounded queue, retry/backoff, write-failure metrics, and crash-recovery validation) while preserving Tier 1 performance targets. (Related: ADR-005, ADR-006)
