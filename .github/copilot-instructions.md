Read the repo-local AI coordination layer under `.ai/`.

## CRITICAL Read Order:

1. `AGENTS.md` (Root operating contract)
2. `.ai/context/project-overview.md`
3. `.ai/context/architecture.md`
4. `.ai/tasks/current-sprint.md`

## Core Mandates:

- **Performance First:** All implementation must respect the Tier 1 performance targets (60% CPU, 100Mbps).
- **Metadata Only:** Never implement payload inspection. Focus on flow metadata (ETA).
- **Single Source of Truth:** Use `.ai/` for all context and decisions. Do not rely on machine-local memory.

All decisions must adhere to the performance targets and architecture defined in the `.ai/` directory.
