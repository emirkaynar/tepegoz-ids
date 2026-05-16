# ADR-011: Native Sensor Package and Optional Observability Stack

## Status

Accepted

## Context

The current Docker-first sensor runtime introduced capture noise from container and bridge traffic, especially in environments that are meant to represent real hosts, routers, and externally facing sensors. The project still needs Grafana and InfluxDB for visualization and persistence, but the packet-capture runtime itself is cleaner, easier to operate, and more realistic when installed natively on Linux.

## Decision

Move the IDS sensor runtime to a native Linux package and service model while keeping Grafana and InfluxDB as optional companion services or separate install targets.

- The sensor runtime is packaged as the primary deliverable and runs as a native `systemd` service.
- Docker Compose remains supported for development, replay testing, and optional lab stacks, but not as the authoritative sensor deployment path.
- Grafana and InfluxDB remain part of the product story, but they are deployed as companion observability services instead of being embedded into the sensor process.
- Optional meta-packaging may install the observability stack alongside the sensor, but the processes remain separate.

## Consequences

- Packet capture uses the host network directly, which reduces container bridge noise and improves realism.
- The sensor package can be installed with standard Linux packaging and service management tools.
- Observability remains available, but Grafana/InfluxDB failures no longer define the sensor deployment model.
- Docker-based demos become a support path rather than the core runtime path.
- The repository now needs a packaging and service boundary in addition to the existing Docker development boundary.

## Alternatives Considered

1. Keep the entire system Docker-first.
    - Rejected because it keeps the sensor exposed to bridge noise and makes real-host capture less representative.
2. Bundle Grafana and InfluxDB directly into the sensor binary/package.
    - Rejected because it increases operational coupling and makes the sensor heavier than necessary.
3. Split the project into separate repos.
    - Rejected because the current repo-local `.ai/` coordination layer already provides the shared source of truth and the code can still be organized cleanly in one repository.

## References

- Relevant context files: `context/project-overview.md`, `context/architecture.md`, `context/tech-stack.md`, `context/coding-standards.md`, `context/api-contracts.md`
- Relevant ADRs: `context/decisions/ADR-003-packet-capture-strategy.md`, `context/decisions/ADR-005-influxdb-batching.md`, `context/decisions/ADR-006-tier1-performance-target.md`, `context/decisions/ADR-007-docker-deployment.md`, `context/decisions/ADR-008-design-doc-stability.md`, `context/decisions/ADR-010-influxdb-summary-rollups.md`
