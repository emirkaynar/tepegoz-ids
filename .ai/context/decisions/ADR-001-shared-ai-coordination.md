# ADR-001: Shared Repo-Local AI Coordination

## Status

Accepted

## Context

The project needs a single coordination layer so every team member and every AI session uses the same project memory, decision history, and task state.

## Decision

Use the repo-local `.ai/` tree as the shared AI coordination system for context, tasks, memory, agents, and templates.

## Consequences

- Team knowledge stays in the repository instead of personal machine-local memory.
- Sessions can recover prior decisions and active work quickly.
- The team can keep sprint updates low-churn and only record meaningful changes.
- Future AI files should extend this structure rather than creating parallel memory systems.
