# ADR-002: Tier 1 and Tier 2 Scope Boundary

## Status

Accepted

## Context

The project description includes a future Tier 2 machine-learning path, but the current release is focused on Tier 1 rule-based detection and lightweight execution.

## Decision

Keep Tier 1 as the active production scope and treat Tier 2 as conditional future work until the project explicitly moves into ML implementation.

## Consequences

- Active sprint planning stays centered on capture, flow extraction, rule evaluation, and storage.
- Tier 2 work can be tracked in backlog or ADRs without polluting current delivery scope.
- AI agents should not automatically promote Tier 2 into current sprint work unless a clear implementation decision is made.
- The shared context stays aligned with the current release constraints and performance goals.
