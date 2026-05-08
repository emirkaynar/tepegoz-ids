# ADR-003: Packet Capture Strategy

## Status

Accepted

## Context

The system must capture network traffic efficiently without payload inspection and with respect for user privacy. The hardware target is resource-constrained (e.g., Raspberry Pi).

## Decision

Use Scapy or equivalent packet capture library to read packets in promiscuous mode with Berkeley Packet Filter (BPF) to reduce system load.
Discard payloads immediately after header parsing.
Maintain only essential metadata: timestamps, addresses, ports, protocol type, TCP flags, and packet size.

## Consequences

- Low memory footprint and minimal CPU overhead for capture.
- Privacy preserved by design through metadata-only analysis.
- Payload cannot be inspected for content-based detection (out of scope for Tier 1).
- Compatibility with ETA (Encrypted Traffic Analysis) approach.
