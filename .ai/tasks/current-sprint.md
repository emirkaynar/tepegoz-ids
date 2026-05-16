# Current Sprint

## Purpose

This file tracks only the active work items that are meaningfully in progress.

## Update Rule

Update this file only when work enters, exits, or materially changes scope, focus, or ownership.
Do not update it for every small subtask, code tweak, or minor implementation step.
Let the AI judge whether a change is large enough to record here using a clear feature boundary or a real shift in active work.

## Active Work

- **Milestone 6: Native Sensor Package and Deployment Split:** Move the IDS sensor runtime to a native Linux package and `systemd` service, keep Grafana and InfluxDB as optional companion services, and retain Docker Compose only as a development and replay harness. Preserve the Sniffnet-style dashboard work, but treat Docker as support infrastructure rather than the authoritative runtime path.

## Milestone 6 Focus

- Keep metadata-only capture and bounded flow processing on the host.
- Package the sensor as an installable service instead of a Docker-only runtime.
- Keep Grafana and InfluxDB as separate observability services or install targets.
- Preserve the summary rollups and declarative dashboard work as a companion path, not the primary deployment decision.
- Implement approved UX contract: `apt install tepegoz-ids`, then optional explicit `sudo tepegoz dash setup` and deterministic `sudo tepegoz dash on|off|status` operations.
