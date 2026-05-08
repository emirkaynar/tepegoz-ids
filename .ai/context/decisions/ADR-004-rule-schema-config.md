# ADR-004: Rule Schema and Configuration

## Status

Accepted

## Context

The rule engine needs to evaluate flows against thresholds and signatures. Rules should be external configuration, not hard-coded, so operators can tune detection without code changes.

## Decision

Define rules as a YAML or JSON configuration file with the following structure:

- Rule name and description.
- Enabled flag and severity level.
- Matching criteria: flow key patterns, time windows, or threshold comparisons.
- Actions: generate alert with context.

Rules are loaded at startup and reloaded on signal or on-demand.

## Consequences

- Non-technical operators can adjust detection thresholds.
- Rules are versionable and auditable.
- Easy to add new rules without touching core code.
- Rule evaluation must remain O(1) or O(n) where n is manageable rule count.
