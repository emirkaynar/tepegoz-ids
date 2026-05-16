# Milestone 6: Native Sensor Package and Deployment Split

## Status

In Progress

## Objective

Move the IDS sensor runtime from a Docker-first deployment to a native Linux package and `systemd` service while keeping Grafana and InfluxDB as optional companion services for visualization and persistence.

## Decision

Use the native sensor package as the authoritative runtime path. Keep Docker Compose only for development, replay testing, and optional lab stacks. Preserve the low-cardinality summary rollups and declarative Grafana provisioning work, but stop treating the Docker sensor container as the production deployment target.

## Scope

- Package the sensor as an installable Linux service.
- Define config loading and defaults for native deployment.
- Preserve metadata-only capture, flow extraction, rule evaluation, and InfluxDB writes.
- Keep Grafana and InfluxDB available as companion services or separate install targets.
- Maintain Docker Compose for tests and demos, not as the primary runtime.

## Planned Work

- Create a Debian package and `systemd` service layout for the sensor.
- Define runtime config and permissions for host-network capture.
- Add install/run documentation for the native package path.
- Keep the existing Docker stack as a test harness for replay and observability checks.
- Decide whether Grafana and InfluxDB are shipped as optional companion packages or external dependencies.

## Approved UX Contract

1. `sudo apt install tepegoz-ids`
    - Installs sensor package and enables native sensor service.
    - Prints post-install guidance for optional dashboard setup.
2. `sudo tepegoz dash setup`
    - Explicit companion setup command run over SSH/CLI by an operator with host access.
    - Installs and configures InfluxDB + Grafana for the companion path.
    - Does not require a first-run web wizard or temporary public setup port.
3. Explicit commands for operations and automation:
    - `sudo tepegoz dash on`
    - `sudo tepegoz dash off`
    - `sudo tepegoz dash status`
    - `sudo tepegoz sensor iface set <name>`

## Execution Breakdown

### Stage A: Packaging and Service Baseline

- Define package layout, service user, and systemd unit boundaries.
- Ensure sensor runs without Grafana/Influx dependencies.

### Stage B: Dash Command State Machine

- Implement idempotent dashboard setup state model.
- Persist setup state and credentials references.
- Ensure no-op behavior on repeated setup attempts.

### Stage C: Companion Service Provisioning

- Install companion services through native package manager path first.
- Apply existing declarative datasource/dashboard provisioning files.
- Add optional documented fallback path if companion install target is unavailable.

### Stage D: Operational Safety

- Guarantee sensor service continuity if dashboard provisioning fails.
- Provide actionable command output and exit statuses for operators.
- Validate upgrade and rollback behavior for package and companion stack.

## Files in Scope

- `engine/main.py`
- `engine/core/capture.py`
- `engine/core/flow.py`
- `engine/core/rules.py`
- `engine/core/database.py`
- `engine/config/rules.yaml`
- `docker-compose.yml`
- `docker-compose.dev.yml`
- `grafana/README.md`
- `grafana/dashboards/network-security-v1.json`
- future packaging files for native install and service management

## Verification

- Sensor runs correctly as a native Linux service on a host interface.
- Capture works without Docker bridge noise dominating the signal.
- Existing engine tests still pass in the project venv.
- Docker-based replay and Grafana/Influx checks still work as a support path.
- Native install documentation is clear enough to follow without consulting Docker deployment steps first.
- `tepegoz dash setup` performs companion setup explicitly from SSH/CLI and remains idempotent.
- Repeated `tepegoz dash setup` calls are idempotent and safe.
- `tepegoz dash on/off/status` provides deterministic control and clear operator feedback.
- `tepegoz sensor iface set <name>` updates capture interface configuration deterministically.

## Notes

- This milestone narrows the Docker deployment decision for the sensor runtime; Docker remains useful for development and testing.
- Grafana and InfluxDB remain part of the product, but they are no longer coupled to the sensor runtime itself.
