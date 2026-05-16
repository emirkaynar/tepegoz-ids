# Tech Stack

## Approved Stack

- Python 3.11+
- Scapy or equivalent packet capture library
- Debian/Ubuntu package tooling for native install
- `systemd` for native service lifecycle
- Docker and Docker Compose for development and testing harnesses
- InfluxDB for time-series storage
- Grafana for visualization
- Custom Grafana App Plugin (React / TypeScript) for configuration UI
- FastAPI for headless configuration API backend
- Linux deployment target

## Runtime Assumptions

- Promiscuous-mode capable network interface
- Native sensor service has privileges that allow raw socket or network access where needed
- Resource-constrained hardware is a primary target

## Development Bias

- Choose the simplest implementation that meets the performance target.
- Prefer standard library and existing project dependencies before adding new ones.
- For Milestone 5, prefer declarative Grafana provisioning and read-only dashboards before any plugin or API-driven configuration work.
- For Milestone 6, treat the native sensor package as primary and Docker as support tooling.
