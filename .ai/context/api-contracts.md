# API Contracts

## Canonical Internal Contracts

- `PacketRecord`: minimal packet metadata after capture and header parsing.
- `FlowRecord`: normalized flow summary produced by the flow processor.
- `RuleConfig`: rule thresholds and matching criteria loaded from shared configuration.
- `AlertRecord`: structured detection output produced by the rule engine.
- `MetricsWrite`: time-series payload sent to InfluxDB.

## Suggested Field Groups

- `PacketRecord`: timestamps, source and destination addresses, ports, protocol, flags, and size.
- `FlowRecord`: flow key, packet counts, byte counts, duration, rate metrics, and protocol ratios.
- `RuleConfig`: rule name, enabled state, thresholds, window size, severity, and match scope.
- `AlertRecord`: alert id, rule name, flow key, severity, trigger time, and short reason.
- `MetricsWrite`: measurement name, tags, fields, and timestamp.

## Contract Rules

- Keep field names stable across components.
- Separate capture data, flow data, alert data, and persistence payloads.
- Treat rules as configuration, not hard-coded behavior.
- Use the same identifiers across tasks, decisions, and implementation.
- Preserve metadata-only analysis in every contract.

## Storage Boundary

- InfluxDB writes should be treated as a distinct integration contract.
- Grafana reads from stored metrics only; it should not define the core detection logic.
- Rule evaluation should happen before persistence so alerts can be written as structured outputs, not derived later in the dashboard layer.
