# ADR-006: Tier 1 Performance Target

## Status

Accepted

## Context

The project explicitly constrains the system to run on consumer hardware with limited CPU (e.g., dual-core) and memory (e.g., 2GB).

## Decision

Set the Tier 1 performance target at no more than 60% average CPU utilization on a dual-core system during normal operation.
Design for sub-second alert latency from packet arrival to database write for high-severity events.
Measure throughput ceiling at 100 Mbps continuous traffic as a baseline for validation.

## Consequences

- All implementation choices must be evaluated against this budget.
- Complex algorithms or unnecessary data structures are prohibited.
- Performance regression must trigger immediate review.
- Tier 2 ML work is conditional and deferred until this target is met.
