# Architecture

## Pipeline

1. Packet capture
2. Preprocessing and header parsing
3. Flow feature extraction
4. Rule-based inspection
5. Metric and alert persistence
6. Grafana visualization

## Main Components

- `PacketSniffer`: captures packets from the network interface.
- `FlowProcessor`: aggregates packets into flows and computes flow statistics.
- `RuleEngine`: evaluates flows against thresholds and rule definitions.
- `DatabaseManager`: writes metrics and alerts to InfluxDB.
- `MLEngine`: future-only component for conditional Tier 2 work.

## Data Flow

- Raw packets are transient.
- Flow summaries and alerts are persistent.
- Payload data is not part of the normal architecture path.

## Architectural Bias

- Prefer simple, deterministic, and measurable paths.
- Keep interfaces explicit between capture, processing, decision, and storage.
