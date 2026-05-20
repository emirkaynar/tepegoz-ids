# Detection Rules Reference

Complete reference for Tepegoz IDS detection rules — how they work, how to configure them, and how to write your own.

---

## Rule Summary

| # | Rule | Severity | Status | Type | Key Metric |
|---|------|----------|--------|------|------------|
| 1 | Port Scan | High | ✅ Enabled | Cross-flow | `cross_unique_dst_ports ≥ 20` |
| 2 | DoS SYN Flood | Critical | ✅ Enabled | Cross-flow | `cross_syn_ratio ≥ 0.8` + `cross_pps ≥ 100` |
| 3 | Volumetric Flood | Medium | ✅ Enabled | Cross-flow | `cross_pps ≥ 1000` OR `cross_bps ≥ 5MB/s` |
| 4 | UDP Flood | High | ✅ Enabled | Cross-flow | UDP + `cross_pps ≥ 300` + `≥ 20 flows` |
| 5 | DNS Amplification | Critical | ✅ Enabled | Hybrid | UDP/53 + `cross_pps ≥ 100` + small packets |
| 6 | Suspicious Long Flow | Medium | ⏸ Disabled | Per-flow | `duration ≥ 300s` + `packets ≥ 100` |
| 7 | C2 Beacon | Critical | ✅ Enabled | Per-flow | Outbound + long duration + low PPS |
| 8 | Data Exfiltration | High | ✅ Enabled | Per-flow | Outbound + `bytes ≥ 10MB` + `duration ≥ 60s` |
| 9 | ICMP Flood | High | ✅ Enabled | Cross-flow | ICMP + `cross_pps ≥ 200` + `≥ 10 flows` |
| 10 | SSH Brute Force | High | ⏸ Disabled | Cross-flow | TCP/22 + `cross_flow_count ≥ 30` |
| 11 | RDP Brute Force | High | ⏸ Disabled | Cross-flow | TCP/3389 + `cross_flow_count ≥ 30` |

---

## How Rules Work

### Rule Structure

Each rule in `rules.yaml` follows this schema:

```yaml
- name: "Rule Name"           # Unique name (used in alerts)
  enabled: true               # true/false — disabled rules are skipped
  severity: "High"            # Critical, High, Medium, Low
  logic: "all"                # "all" = AND (every condition), "any" = OR (any condition)
  cooldown_seconds: 30        # Minimum seconds between repeated alerts for same source
  conditions:                 # List of threshold checks
    - field: "cross_pps"      # Metric to evaluate
      op: "gte"               # Comparison operator
      value: 100              # Threshold value
  description: >-             # Human-readable alert message (supports {field} templates)
    Alert text with {cross_pps:.0f} packets/sec detected.
```

### Comparison Operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `eq` | Equal to | `protocol eq "TCP"` |
| `neq` | Not equal to | `protocol neq "ICMP"` |
| `gt` | Greater than | `cross_pps gt 500` |
| `gte` | Greater than or equal | `cross_pps gte 100` |
| `lt` | Less than | `avg_packet_size lt 100` |
| `lte` | Less than or equal | `packets_per_second lte 1` |

### Logic Modes

- **`all`** (AND): Every condition must be true for the rule to fire. Used for targeted detection (e.g., "TCP AND port 22 AND high flow count").
- **`any`** (OR): Any condition being true triggers the rule. Used for volumetric detection (e.g., "high PPS OR high BPS").

### Cooldown

After a rule fires for a specific source IP, it won't fire again for that same source until `cooldown_seconds` has elapsed. This prevents alert flooding during sustained attacks.

---

## Available Fields

### Per-Flow Fields

These are computed from a single flow (one 5-tuple connection):

| Field | Type | Description |
|-------|------|-------------|
| `protocol` | String | `TCP`, `UDP`, or `ICMP` |
| `src_port` | Integer | Source port |
| `dst_port` | Integer | Destination port |
| `direction` | String | `inbound` or `outbound` |
| `packet_count` | Integer | Total packets in the flow |
| `byte_count` | Integer | Total bytes in the flow |
| `duration` | Float | Flow duration in seconds |
| `packets_per_second` | Float | `packet_count / duration` |
| `avg_packet_size` | Float | `byte_count / packet_count` |
| `syn_count` | Integer | Number of SYN packets |

### Cross-Flow Fields (SourceTracker)

These are aggregated across **all flows from the same source IP** within a sliding time window. They are essential for detecting distributed attacks.

| Field | Type | Description |
|-------|------|-------------|
| `cross_flow_count` | Integer | Total active flows from this source |
| `cross_pps` | Float | Aggregate packets/sec across all flows |
| `cross_bps` | Float | Aggregate bytes/sec across all flows |
| `cross_unique_dst_ports` | Integer | Unique destination ports targeted |
| `cross_syn_ratio` | Float | SYN packets / total packets (0.0 – 1.0) |

---

## Writing Custom Rules

### Example: Detecting Telnet Brute Force

```yaml
- name: "Telnet Brute Force"
  enabled: true
  severity: "High"
  logic: "all"
  cooldown_seconds: 60
  conditions:
    - field: "protocol"
      op: "eq"
      value: "TCP"
    - field: "dst_port"
      op: "eq"
      value: 23
    - field: "cross_flow_count"
      op: "gte"
      value: 30
    - field: "cross_pps"
      op: "gte"
      value: 20
  description: >-
    {cross_flow_count} connection attempts to Telnet (port 23) detected
    from this source at {cross_pps:.0f} packets/sec.
```

### Example: Detecting NTP Amplification

```yaml
- name: "NTP Amplification"
  enabled: true
  severity: "Critical"
  logic: "all"
  cooldown_seconds: 30
  conditions:
    - field: "protocol"
      op: "eq"
      value: "UDP"
    - field: "dst_port"
      op: "eq"
      value: 123
    - field: "cross_pps"
      op: "gte"
      value: 100
    - field: "cross_flow_count"
      op: "gte"
      value: 10
  description: >-
    High-rate NTP traffic detected ({cross_pps:.0f} pps across
    {cross_flow_count} flows). Possible NTP amplification attack.
```

### Description Templates

The `description` field supports Python format strings. Any field name can be used as a template variable:

```yaml
description: >-
  {cross_flow_count} flows at {cross_pps:.0f} pps with {cross_syn_ratio:.0%} SYN ratio.
```

Format specifiers:
- `{field}` — raw value
- `{field:.0f}` — float with 0 decimal places
- `{field:.2f}` — float with 2 decimal places
- `{field:.0%}` — percentage (0.8 → "80%")

---

## Tuning Guide

### Reducing False Positives

If a rule triggers too often on legitimate traffic:

1. **Increase thresholds** — Raise `value` for cross-flow metrics (e.g., `cross_pps: 100 → 200`)
2. **Increase cooldown** — Set a longer `cooldown_seconds` to reduce alert frequency
3. **Disable the rule** — Set `enabled: false` while investigating

### Reducing False Negatives

If attacks are missed:

1. **Lower thresholds** — Decrease `value` fields (be careful of false positives)
2. **Change logic from `all` to `any`** — Makes the rule more sensitive
3. **Reduce cooldown** — Allows faster re-triggering

### Network-Specific Tuning

| Network Size | Recommended PPS Threshold | Recommended Flow Count |
|-------------|--------------------------|----------------------|
| Home (1-5 devices) | 50-100 pps | 5-10 flows |
| Small Office (5-20 devices) | 100-500 pps (default) | 10-20 flows |
| Medium Office (20-100 devices) | 500-1000 pps | 20-50 flows |

---

## Known Limitations

### Cross-flow metrics are per-source-IP, not per-destination-port

The `SourceTracker` aggregates metrics across **all flows from a source IP**, regardless of destination port. This means:

- During a **port scan** (many destination ports), `cross_flow_count` reflects the total scan, not per-port connections
- A port scan can trigger **both** the Port Scan rule (correctly) **and** brute force rules (false positive) if the scan touches ports 22 or 3389

This is why the SSH and RDP Brute Force rules are currently disabled. A future improvement would add per-destination-port cross-flow tracking to the `SourceTracker`.

### Cooldown applies per source IP

If the same source IP triggers different rules, each rule has its own independent cooldown. However, if two different source IPs trigger the same rule, they are tracked independently (one does not suppress the other).

---

## Configuration File Location

| Environment | Path |
|-------------|------|
| Installed (`.deb`) | `/etc/tepegoz-ids/rules.yaml` |
| Development | `engine/config/rules.yaml` |

After editing the rules file, restart the sensor service for changes to take effect:

```bash
sudo systemctl restart tepegoz-ids
```
