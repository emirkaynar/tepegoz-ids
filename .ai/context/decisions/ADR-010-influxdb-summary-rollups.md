# ADR-010: InfluxDB Summary Rollups for Grafana Dashboards

## Status

Accepted

## Context

The IDS engine already produces raw flow and alert records for Tier 1 detection, but Sniffnet-style dashboards need low-cardinality aggregates for traffic, top hosts, top services, and alert visibility. Querying raw flow series directly from Grafana caused max-series failures and table rendering issues.

## Decision

Keep raw `net_flow` and `alerts` records for detection correctness, but add bounded summary rollups for dashboard consumption.

- Raw measurements remain the source of truth for IDS processing.
- Summary measurements are generated only from finalized flows.
- Dashboard-facing measurements must stay low-cardinality and bounded.
- High-cardinality identifiers such as `flow_key` must not be used as indexed tags for dashboard rollups.
- Grafana dashboards must read summary rollups for overview, host ranking, and service ranking panels.

## Consequences

- Grafana queries become stable and cheap to render.
- The engine keeps its packet-path work lean by summarizing only finalized flows.
- Dashboard panels can resemble Sniffnet without forcing raw flow series into the UI.
- Top-host and top-service panels must be bounded to avoid unbounded cardinality growth.
- A small summary aggregation layer becomes part of the Tier 1 architecture.

## Implementation Guidance

1. Keep `net_flow` and `alerts` as raw operational measurements.
2. Add rollup measurements such as `traffic_rollup`, `top_hosts_rollup`, and `top_services_rollup`.
3. Generate summary records only after a flow is finalized or on a bounded flush interval.
4. Use low-cardinality tags only for dashboard rollups.
5. Update Grafana panels to query rollups, not raw flow series.
