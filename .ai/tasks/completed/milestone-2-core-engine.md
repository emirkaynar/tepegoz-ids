# Milestone 2: Core Capture & Flow Engine

## Status
Completed

## What Changed
- **Workflow Migration:** Updated `.instructions.md` to prioritize the `.ai/` directory and explicitly forbid the use of `conductor/`.
- **Data Contracts:** Implemented `PacketRecord` and `FlowRecord` in `engine/core/contracts.py` with `__slots__` for memory efficiency.
- **Packet Sniffer:** Implemented `PacketSniffer` in `engine/core/capture.py` using Scapy's `sniff(store=False)` with BPF filters and metadata-only parsing.
- **Flow Processor:** Implemented `FlowProcessor` in `engine/core/flow.py` for 5-tuple flow aggregation, statistics computation, and lifecycle management (FIN/RST detection and idle timeouts).
- **Integration:** Updated `engine/main.py` to orchestrate the sniffer and processor with a background cleanup thread.

## Validation
- Rebuilt the `ids-engine` container.
- Verified logs show active flow capture and finalization on the `eth0` interface within the Docker network environment.

## Memory / Decisions Updated
- Confirmed that Scapy successfully captures packets in the Docker `network_mode: host` environment with `NET_ADMIN` capabilities.
