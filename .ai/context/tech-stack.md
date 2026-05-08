# Tech Stack

## Approved Stack

- Python 3.11+
- Scapy or equivalent packet capture library
- Docker and Docker Compose
- InfluxDB for time-series storage
- Grafana for visualization
- Custom Grafana App Plugin (React / TypeScript) for configuration UI
- FastAPI for headless configuration API backend
- Linux deployment target

## Runtime Assumptions

- Promiscuous-mode capable network interface
- Docker privileges that allow raw socket or network access where needed
- Resource-constrained hardware is a primary target

## Development Bias

- Choose the simplest implementation that meets the performance target.
- Prefer standard library and existing project dependencies before adding new ones.
