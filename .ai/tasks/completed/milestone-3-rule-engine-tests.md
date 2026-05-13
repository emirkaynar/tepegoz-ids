# Milestone 3: Rule-Based Detection Engine & Test Framework

## Status
Completed

## What Changed
- **Rule Engine:** Implemented `RuleEngine` in `engine/core/rules.py` with support for Scanning, Protocol Anomaly, and Volumetric detection.
- **Rules Config:** Created `engine/config/rules.yaml` to define tunable thresholds.
- **Data Contracts:** Extended `FlowRecord` to track SYN counts and unique destination ports. Added `AlertRecord`.
- **Integration:** Hooked the Rule Engine into the `FlowProcessor` callback in `engine/main.py`.
- **Test Framework:** 
    - Created `engine/tests/test_rules.py` (Pytest).
    - Created `engine/tests/pcap_replay.py` for dataset verification.
- **Dev Environment:** Established `docker-compose.dev.yml` with volume mounting for live development.

## Validation
- **Pytest:** 3/3 tests passed (Port Scan, SYN Flood, Benign flow).
- **Live Logs:** Verified real-time alerting for volumetric noise in the Docker environment.

## Memory / Decisions Updated
- **Hybrid Testing Strategy:** Confirmed Docker Desktop is suitable for logic and PCAP-based verification, while physical/VM hardware will be required for final live network calibration.
