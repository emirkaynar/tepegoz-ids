# ADR-007: Docker Deployment Model

## Status

Superseded by ADR-011

## Context

The system must run on consumer hardware, often with limited network access and privilege constraints. Docker Compose is the approved deployment platform for simplicity and repeatability.

## Decision

Build the system as Docker containers deployed via Docker Compose.
Each major component (capture engine, InfluxDB, Grafana) runs in a separate container.
Use network-scoped volumes for configuration and data persistence.
Capture container requires NET_ADMIN or equivalent capability to access raw sockets.
Use restart policies to ensure resilience on unexpected failures.

## Consequences

- Simple one-command deployment and teardown.
- Container isolation reduces unexpected interactions.
- Network capture privilege must be explicitly granted to the capture container.
- Volume management and cleanup becomes an operational task.

## Supersession Note

This ADR is retained for historical context from Milestone 1-5. The active deployment direction is now defined by ADR-011:

- Sensor runtime is native Linux package + `systemd`.
- Docker Compose remains for development, replay tests, and optional companion stacks.
