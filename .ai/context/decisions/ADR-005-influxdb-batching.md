# ADR-005: InfluxDB Batching and Persistence

## Status

Accepted

## Context

Network monitoring generates high-velocity data streams. Writing every metric and alert individually to InfluxDB would cause I/O bottlenecks and poor performance on resource-constrained hardware.

## Decision

Batch writes to InfluxDB at regular intervals (e.g., every 1-5 seconds) or when the batch reaches a size threshold.
Separate alert writes from metric writes so alerts are persisted immediately but metrics can tolerate slight delays.
Use connection pooling and batch API calls to minimize overhead.

## Consequences

- Reduced I/O pressure and CPU overhead.
- Slight delay in metric visibility on the dashboard (acceptable trade-off).
- Alerts are written with lower latency for operational responsiveness.
- Requires careful handling of batch queue overflow to prevent memory growth.
