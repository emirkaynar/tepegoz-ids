# Backend Agent

## When to Use

Use this agent for packet capture, flow processing, rule evaluation, alert generation, persistence, and any performance-sensitive Python work.

## Inputs

- Relevant files in `.ai/context/`
- `.ai/tasks/current-sprint.md`
- Relevant ADRs
- The corresponding implementation files

## Rules

- Prefer efficient execution over abstraction.
- Keep data flow explicit and lean.
- Preserve metadata-only analysis.
- Escalate to a decision file when a backend choice should not be revisited.

## Output

Implementation changes, focused refactors, or short technical notes tied to the active task.
