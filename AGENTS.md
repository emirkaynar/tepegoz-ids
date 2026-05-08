# AI Operating Contract

## Purpose

This repository uses a shared, repo-local AI coordination layer under `.ai/` so every session and every team member works from the same context.

## Read Order

Before making changes, inspect the relevant files in this order:

1. `.ai/context/project-overview.md`
2. `.ai/context/architecture.md`
3. `.ai/context/tech-stack.md`
4. `.ai/context/coding-standards.md`
5. `.ai/context/api-contracts.md`
6. `.ai/context/glossary.md`
7. `.ai/context/decisions/*.md`
8. `.ai/tasks/backlog.md`
9. `.ai/tasks/current-sprint.md`
10. `.ai/memory/*.md`
11. `documents/md/*.md`

## Working Rules

- Use the repo-local `.ai/` files as the shared memory for this project.
- Do not rely on personal or machine-local memory directories for team alignment.
- Keep implementation lightweight, efficient, and performance-first.
- Prefer low-overhead data paths, batching, and clear ownership boundaries.
- Avoid payload inspection or deep packet inspection unless the docs explicitly require it.
- Treat `current-sprint.md` as a low-churn file: update it only when work enters, exits, or materially changes scope, focus, or ownership.
- Let the AI decide whether a change is significant enough to update `current-sprint.md`; do not update it for every small subtask.
- Use ADRs for decisions that should not be re-litigated.
- Keep design docs intact unless the task explicitly requires changes there.

## Conflict Rule

If a task conflicts with the existing `.ai/` context or decisions, prefer the shared project files and ask for clarification only if the conflict cannot be resolved locally.
