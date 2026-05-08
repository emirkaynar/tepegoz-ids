# .ai/ — Shared AI Coordination Layer

This directory contains the repo-local coordination files for all AI work in the project.

## Quick Navigation

### Context (Shared Knowledge)

- [project-overview.md](context/project-overview.md) — Project scope and release boundaries.
- [architecture.md](context/architecture.md) — System pipeline and main components.
- [tech-stack.md](context/tech-stack.md) — Approved tools and runtime assumptions.
- [coding-standards.md](context/coding-standards.md) — Performance-first code rules.
- [api-contracts.md](context/api-contracts.md) — Internal data structures and field definitions.
- [glossary.md](context/glossary.md) — Standardized terminology.
- [decisions/](context/decisions/) — Architecture and policy decisions (ADRs).

### Tasks (Work Coordination)

- [backlog.md](tasks/backlog.md) — Approved but not yet active work.
- [current-sprint.md](tasks/current-sprint.md) — Actively in-progress work (updated only on meaningful scope changes).
- [completed/](tasks/completed/) — Archive of finished tasks.

### Memory (Shared Experience)

- [known-issues.md](memory/known-issues.md) — Reproducible bugs and environment quirks.
- [pitfalls.md](memory/pitfalls.md) — Mistakes to avoid.
- [lessons-learned.md](memory/lessons-learned.md) — Verified successful approaches.

### Agents (Role-Based Guidance)

- [agents/backend-agent.md](agents/backend-agent.md) — Packet capture, flow processing, rule evaluation, persistence.
- [agents/devops-agent.md](agents/devops-agent.md) — Docker, InfluxDB, Grafana, deployment.
- [agents/reviewer-agent.md](agents/reviewer-agent.md) — Code review and alignment checks.
- [agents/frontend-agent.md](agents/frontend-agent.md) — Custom UI work (optional).

### Templates (Reusable Forms)

- [templates/task-template.md](templates/task-template.md) — Task skeleton.
- [templates/pr-template.md](templates/pr-template.md) — PR review checklist.
- [templates/adr-template.md](templates/adr-template.md) — ADR skeleton.

## Working with This Structure

1. **Start every session by reading:** [AGENTS.md](../AGENTS.md), [project-overview.md](context/project-overview.md), and [current-sprint.md](tasks/current-sprint.md).
2. **Check decisions before changing scope:** Relevant ADRs are in [decisions/](context/decisions/).
3. **Record new insights:** Update [memory/](memory/) or create new ADRs if the change is durable.
4. **Update the sprint only on meaningful changes:** Do not log every small implementation step.
5. **Stay aligned:** Every team member uses this shared layer, not personal machine-local memory.
