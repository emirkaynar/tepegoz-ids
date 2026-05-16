# Grafana Integration

This folder contains the read-only Grafana integration for Milestone 5.

## Layout

- `grafana/provisioning/datasources/` contains the InfluxDB datasource definition.
- `grafana/provisioning/dashboards/` contains the dashboard provider that tells Grafana where to load JSON dashboards from.
- `grafana/dashboards/` contains exported dashboard JSON files.

## Why this approach

- It keeps the runtime footprint low.
- It avoids adding any new service or API layer for visualization.
- It preserves the Grafana App Plugin milestone for later work.

## Current dashboard target

- `network-security-v1.json` is the first dashboard.
- It is intended to show:
    - traffic rate from `traffic_rollup`
    - top hosts from `top_hosts_rollup`
    - top services from `top_services_rollup`
    - recent alerts from `alerts`
    - protocol distribution from `traffic_rollup`

## Data contract

- `net_flow` stays as the raw flow record for IDS correctness.
- `alerts` stays as the raw alert record.
- `traffic_rollup`, `top_hosts_rollup`, and `top_services_rollup` are dashboard-facing summaries.
- The dashboard should never rely on `flow_key` as a grouping tag.

## Update workflow

1. Edit the dashboard JSON in `grafana/dashboards/`.
2. Restart Grafana or reload the container.
3. Confirm the panels still query only the existing InfluxDB measurements.

## Notes

- Keep panel refresh rates at 5 seconds or higher to stay aligned with the batching and summary flush model.
- Do not add configuration UI code here; that belongs to the later Grafana App Plugin milestone.
