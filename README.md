```
  █████                                                            
 ░░███                                                             
 ███████    ██████  ████████   ██████   ███████  ██████   █████████
░░░███░    ███░░███░░███░░███ ███░░███ ███░░███ ███░░███ ░█░░░░███ 
  ░███    ░███████  ░███ ░███░███████ ░███ ░███░███ ░███ ░   ███░  
  ░███ ███░███░░░   ░███ ░███░███░░░  ░███ ░███░███ ░███   ███░   █
  ░░█████ ░░██████  ░███████ ░░██████ ░░███████░░██████   █████████
   ░░░░░   ░░░░░░   ░███░░░   ░░░░░░   ░░░░░███ ░░░░░░   ░░░░░░░░░ 
                    ░███               ███ ░███                    
                    █████             ░░██████                     
                   ░░░░░               ░░░░░░                       
```

[![Tests](https://github.com/emirkaynar/tepegoz-ids/actions/workflows/ci.yml/badge.svg)](https://github.com/emirkaynar/tepegoz-ids/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/emirkaynar/tepegoz-ids?label=latest%20release)](https://github.com/emirkaynar/tepegoz-ids/releases/latest)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

> *In the ancient Turkic epic "Book of Dede Korkut," Tepegöz is a one-eyed giant - a creature whose single, unblinking eye sees everything that moves across the land. While the legends speak of a fearsome being, we chose this name for a different reason: that tireless, all-seeing gaze. Like its namesake, Tepegoz IDS watches over your network with a single focused eye, quietly observing every flow and every connection - never blinking, never looking away. It doesn't read your private messages or inspect your data. It simply watches the patterns, the rhythms of traffic, and raises its voice only when something doesn't look right.*

---

## What is Tepegoz IDS?

**Tepegoz IDS** is a lightweight, real-time network intrusion detection system designed specifically for **small office, home office (SOHO), and SME networks**. It monitors network traffic using metadata-only analysis - detecting threats like port scans, DoS floods, and data exfiltration without ever inspecting packet payloads or private content.

### Why Tepegoz?

| | Enterprise IDS (Snort, Zeek) | Tepegoz IDS |
|---|---|---|
| **Setup** | Hours of configuration, rule writing, SIEM integration | `apt install` → 3 commands → done |
| **Resources** | Dedicated hardware, high CPU/RAM | Runs on a Raspberry Pi |
| **Expertise** | Requires security engineers | Built for non-technical users |
| **Privacy** | Often requires DPI | Metadata-only - never reads content |
| **Cost** | Free software, expensive infrastructure | Free, runs on any Linux box |

---

## Comparative Analysis

How Tepegoz compares to existing lightweight IDS solutions for SME environments:

| Feature | Zeek | OSSEC | Prelude | Snort/Suricata | **Tepegoz** |
|---------|------|-------|---------|----------------|-------------|
| **Detection** | Deep network analysis | Log analysis, file integrity | Modular multi-sensor | Signature + anomaly | Signature + basic anomaly (cross-flow correlation) |
| **Scalability** | High, but resource-intensive | Limited to host-level | High, but complex | High, high resource demands | High, modular growth with minimal overhead |
| **Resource Demands** | Moderate to high | Low | Moderate to high | High | **Low** |
| **Ease of Use** | Complex setup | Moderate | Complex setup | Complex setup | **Simple setup and management** |
| **Cost** | Free (significant resources) | Free | Free (complex to manage) | Free (requires expertise) | **Free (no special hardware)** |
| **Relevance to SMEs** | Too complex for typical SMEs | Useful for host-level only | Challenging for SMEs | High capability but high cost | **Explicitly designed for SMEs** |

> *Based on: El-Taj, H., et al. (2025). A Lightweight Network Intrusion Detection System for SMEs.*

---

## Architecture

Tepegoz follows a linear **Pipe and Filter** architecture designed for low overhead:

```
┌──────────────┐    ┌──────────────────┐    ┌──────────────┐    ┌───────────┐    ┌─────────┐
│ PacketSniffer│───▶│  FlowProcessor   │───▶│  RuleEngine  │───▶│ InfluxDB  │───▶│ Grafana │
│  (Scapy)     │    │ (5-tuple flows)  │    │ (YAML rules) │    │ (metrics) │    │ (dash)  │
└──────────────┘    └──────────────────┘    └──────────────┘    └───────────┘    └─────────┘
```

- **Packet Capture** - Raw frames captured via Scapy in promiscuous mode with BPF kernel filters
- **Flow Extraction** - Packets aggregated into 5-tuple flows with statistical metrics (duration, packet rate, byte count, TCP flag ratios)
- **Rule Engine** - Configurable YAML-based rules with cross-flow correlation via `SourceTracker` (per-source-IP behavioral analysis)
- **Persistence** - Batched writes to InfluxDB time-series database
- **Visualization** - Pre-configured Grafana dashboard with KPIs, traffic charts, alert tables, and protocol distribution

📖 **[Detailed Architecture →](docs/ARCHITECTURE.md)**

---

## Detection Rules

Tepegoz ships with **10 detection rules** covering the most common SOHO/SME threats:

| Rule | Severity | Status | Description |
|------|----------|--------|-------------|
| Port Scan | High | ✅ Enabled | Detects single-source scanning of 20+ unique destination ports |
| DoS SYN Flood | Critical | ✅ Enabled | High SYN ratio (>80%) at 100+ pps across multiple flows |
| Volumetric Flood | Medium | ✅ Enabled | Traffic exceeding 1000 pps or 5 MB/s from a single source |
| UDP Flood | High | ✅ Enabled | 300+ UDP pps across 20+ flows from one source |
| DNS Amplification | Critical | ✅ Enabled | High-rate small DNS packets indicating reflection attack |
| C2 Beacon | Critical | ✅ Enabled | Low-rate, long-lived outbound "heartbeat" patterns |
| Data Exfiltration | High | ✅ Enabled | Large sustained outbound transfers (10+ MB over 60s) |
| ICMP Flood | High | ✅ Enabled | 200+ ICMP pps across 10+ flows |
| SSH Brute Force | High | ⏸ Disabled | Rapid connection attempts to port 22 (pending per-port tracking) |
| RDP Brute Force | High | ⏸ Disabled | Rapid connection attempts to port 3389 (pending per-port tracking) |

All rules are defined in [`config/rules.yaml`](engine/config/rules.yaml) and can be customized without code changes.

📖 **[Detection Rules Reference →](docs/DETECTION_RULES.md)**

---

## Quick Start

### Installation

Download the latest `.deb` package from [GitHub Releases](https://github.com/emirkaynar/tepegoz-ids/releases/latest):

#### For amd64 architecture (Windows, Linux etc.)

```bash
# Download the latest release
wget https://github.com/emirkaynar/tepegoz-ids/releases/latest/download/tepegoz-ids_amd64.deb

# Install (handles dependencies automatically)
sudo apt install ./tepegoz-ids_amd64.deb
```

#### For arm64 architecture (Raspberry Pi etc.)

```bash
# Download the latest release
wget https://github.com/emirkaynar/tepegoz-ids/releases/latest/download/tepegoz-ids_arm64.deb

# Install (handles dependencies automatically)
sudo apt install ./tepegoz-ids_arm64.deb
```

### Setup (3 steps)

```bash
# 1. Set the network interface to monitor
sudo tepegoz sensor iface set eth0
#    Not sure which one? Run: ip link
#    (Usually "eth0" for wired or "wlan0" for Wi-Fi)

# 2. Install and configure the dashboard
sudo tepegoz dash setup
#    This installs InfluxDB + Grafana, configures data sources,
#    and opens the dashboard at http://localhost:3000

# 3. Check that everything is running
tepegoz sensor status
```

### CLI Reference

| Command | Description |
|---------|-------------|
| `tepegoz sensor iface set <name>` | Set the network interface to monitor |
| `tepegoz sensor status` | Show sensor service status |
| `tepegoz dash setup` | Install & configure InfluxDB + Grafana |
| `tepegoz dash on` | Start the dashboard services |
| `tepegoz dash off` | Stop the dashboard services |
| `tepegoz dash status` | Show dashboard service status |
| `tepegoz --help` | Display the welcome guide |

### Configuration Files

| File | Purpose |
|------|---------|
| `/etc/tepegoz-ids/sensor.conf` | Sensor settings (interface, InfluxDB connection) |
| `/etc/tepegoz-ids/rules.yaml` | Detection rules and thresholds |

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Capture** | Python 3.11 + Scapy | Real-time packet sniffing with BPF filters |
| **Detection** | Custom rule engine | YAML-driven threshold evaluation with cross-flow correlation |
| **Storage** | InfluxDB 2.x | Time-series database for metrics and alerts |
| **Visualization** | Grafana OSS | Pre-configured dashboard with KPIs and alert tables |
| **Packaging** | Debian `.deb` | Native package with systemd service integration |
| **CI/CD** | GitHub Actions | Automated testing + multi-arch build (amd64/arm64) |

---

## Development

### Running Tests

```bash
cd engine
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest tests/ -v --tb=short
```

### Test Scenarios

From the [System Design Description](documents/md/SDD-v1.md):

| Scenario | Tool | Command | Expected |
|----------|------|---------|----------|
| Port Scan | nmap | `nmap -sS -p 1-1000 <target>` | Port Scan alert triggered |
| SYN Flood | hping3 | `sudo hping3 -S --flood -p 80 <target>` | DoS SYN Flood alert (Critical) |
| Benign Stress | iperf3 | `iperf3 -c <target> -t 60 -b 100M` | No false positives |

### Building from Source

```bash
# Build the .deb package locally
./build-deb.sh
```

---

## Project Documentation

| Document | Description |
|----------|-------------|
| [Project Proposal](documents/md/Project%20Proposal.md) | Original project proposal and objectives |
| [Software Requirements Specification](documents/md/SRS-v1.md) | Functional and non-functional requirements |
| [System Design Description](documents/md/SDD-v1.md) | Architecture, component design, and algorithms |
| [Architecture Guide](docs/ARCHITECTURE.md) | Detailed technical architecture |
| [Detection Rules Reference](docs/DETECTION_RULES.md) | Rule configuration and tuning guide |

---

## References

- El-Taj, H., et al. (2025). *A Lightweight Network Intrusion Detection System for SMEs.*
- Almalawi, A. (2025). *A Lightweight Intrusion Detection System for Internet of Things: Clustering and Monte Carlo Cross-Entropy Approach.* Sensors 2025, 25, 2235.
- IEEE Std 830-1998, *IEEE Recommended Practice for Software Requirements Specifications.*
- CIC-IDS-2017/18 Dataset Documentation.
- [Scapy Documentation](https://scapy.net/)
- [InfluxDB Documentation](https://docs.influxdata.com/)
- [Grafana Documentation](https://grafana.com/docs/)

---

## License

This project is licensed under the **Apache License 2.0** - see the [LICENSE](LICENSE) file for details.

You are free to use, modify, and distribute this software. Future versions may be released under different licensing terms.

---

## Authors

**Mustafa Emir KAYNAR** & **Şamil KEKLİKOĞLU**

Advisor: **Prof. Dr. Reza Zare HASSANPOUR**

Department of Computer Engineering, Konya Food and Agriculture University

---

<p align="center">
  <i>The eye that never blinks. The guardian that never sleeps.</i>
</p>
