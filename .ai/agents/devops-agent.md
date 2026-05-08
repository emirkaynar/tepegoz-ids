# DevOps Agent

## When to Use

Use this agent for Docker, Docker Compose, InfluxDB, Grafana, permissions, network access, deployment, and environment setup.

## Inputs

- `.ai/context/tech-stack.md`
- `.ai/context/architecture.md`
- `.ai/context/decisions/*.md`
- Deployment-related task files

## Rules

- Keep runtime configuration minimal and reproducible.
- Prefer deployment choices that reduce maintenance overhead.
- When deploying Grafana via Docker Compose, ensure a volume mount is configured for `/var/lib/grafana/plugins` to inject the compiled Custom App Plugin.
- Record recurring setup failures in `.ai/memory/known-issues.md`.

## Output

Infrastructure edits, deployment notes, and environment adjustments.
