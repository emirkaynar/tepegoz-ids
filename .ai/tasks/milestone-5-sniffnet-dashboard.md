# Milestone 5: Sniffnet-Style Grafana Dashboard

## Status

Paused

## Objective

Build a Sniffnet-inspired Grafana dashboard that shows traffic rate, top hosts, top services, protocol distribution, and recent alerts without hitting InfluxDB cardinality limits or increasing packet-path CPU meaningfully.

## Decision

Use raw flow and alert records for IDS correctness, then add low-cardinality summary rollups for Grafana visualization. Keep the Custom Grafana App Plugin and headless FastAPI configuration API deferred to later milestones.

## Scope

- Keep `net_flow` and `alerts` as the operational records.
- Add summary measurements for dashboard views.
- Update the Grafana dashboard to use summary rollups instead of raw flow series.
- Keep provisioning declarative and lightweight.

## Planned Measurements

- `traffic_rollup`
- `top_hosts_rollup`
- `top_services_rollup`
- `alerts` for recent alert log rendering

## Files in Scope

- `engine/core/summary.py`
- `engine/core/database.py`
- `engine/main.py`
- `grafana/dashboards/network-security-v1.json`
- `grafana/provisioning/datasources/influxdb.yaml`
- `grafana/provisioning/dashboards/dashboard-provisioning.yaml`
- `grafana/README.md`

## Verification

- 11+ targeted tests pass in the engine venv.
- Dashboard queries avoid max-series errors.
- Alerts render as flat table rows.
- Summary rollups remain bounded and flush on interval.
- Engine packet-path overhead stays low.

## Notes

- Sniffnet-like layout is still the target, but the sensor runtime has shifted to a native package milestone.
- Process/program attribution is not part of this milestone.
- Continue to treat this as a companion observability effort, not the primary deployment decision.
