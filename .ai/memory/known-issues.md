# Known Issues

## Purpose

Record reproducible issues, environment quirks, and failures that future sessions should not rediscover.

## Entries

- Scapy packet capture on Linux requires NET_ADMIN or raw socket capability inside Docker container.
- Promiscuous mode may not work on all network interfaces or virtualized environments; check with `ip link show` and `ip link set <interface> promisc on`.
- InfluxDB single-node deployments can experience write stalls under sustained high-volume traffic; consider batching window tuning if latency spikes.
- Flow timeout and cleanup logic must be deterministic; unbounded flow state can cause memory exhaustion on long-running captures.
- Docker Desktop networking can hide or remap bridge interfaces, making automatic container subnet detection inconsistent across hosts.
