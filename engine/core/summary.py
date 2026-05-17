import time
from collections import Counter
from dataclasses import dataclass
from threading import Lock
from typing import List, Optional

from .contracts import FlowRecord, HostSummaryRecord, ServiceSummaryRecord, TrafficSummaryRecord

# Well-known port → human-readable service name mapping.
# Kept small (~30 entries) to stay lightweight per ADR-006.
PORT_TO_SERVICE = {
    20: "FTP-Data", 21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
    53: "DNS", 67: "DHCP", 68: "DHCP", 80: "HTTP", 110: "POP3",
    123: "NTP", 143: "IMAP", 161: "SNMP", 162: "SNMP-Trap",
    443: "HTTPS", 445: "SMB", 465: "SMTPS", 514: "Syslog",
    587: "SMTP-Sub", 993: "IMAPS", 995: "POP3S",
    1433: "MSSQL", 1883: "MQTT", 3306: "MySQL", 3389: "RDP",
    5432: "PostgreSQL", 5672: "AMQP", 6379: "Redis",
    8080: "HTTP-Alt", 8086: "InfluxDB", 8443: "HTTPS-Alt",
    8883: "MQTT-TLS", 9090: "Prometheus",
}


@dataclass
class SummaryFlushBatch:
    traffic: List[TrafficSummaryRecord]
    hosts: List[HostSummaryRecord]
    services: List[ServiceSummaryRecord]


class SummaryAggregator:
    """
    Collects finalized flows into bounded, dashboard-friendly summary records.
    """

    def __init__(self, top_k: int = 10):
        self.top_k = top_k
        self._lock = Lock()
        self.total_packets = 0
        self.total_bytes = 0
        self.total_flows = 0
        self.protocol_packets = Counter()
        self.protocol_bytes = Counter()
        self.protocol_flows = Counter()
        self.host_packets = Counter()
        self.host_bytes = Counter()
        self.host_flows = Counter()
        self.service_packets = Counter()
        self.service_bytes = Counter()
        self.service_flows = Counter()
        self._last_flush_time = time.time()

    def update_flow(self, flow: FlowRecord, direction: str) -> None:
        with self._lock:
            self.total_packets += flow.packet_count
            self.total_bytes += flow.byte_count
            self.total_flows += 1

            # aggregate by protocol + direction
            proto_dir = f"{flow.protocol}:{direction}"
            self.protocol_packets[proto_dir] += flow.packet_count
            self.protocol_bytes[proto_dir] += flow.byte_count
            self.protocol_flows[proto_dir] += 1

            # hosts (keep per-host counters independent of direction for ranking)
            self.host_packets[flow.src_ip] += flow.packet_count
            self.host_packets[flow.dst_ip] += flow.packet_count
            self.host_bytes[flow.src_ip] += flow.byte_count
            self.host_bytes[flow.dst_ip] += flow.byte_count
            self.host_flows[flow.src_ip] += 1
            self.host_flows[flow.dst_ip] += 1

            service_key = self._service_key(flow.protocol, flow.dst_port)
            self.service_packets[service_key] += flow.packet_count
            self.service_bytes[service_key] += flow.byte_count
            self.service_flows[service_key] += 1

    def flush(self) -> SummaryFlushBatch:
        with self._lock:
            now = time.time()
            elapsed = max(now - self._last_flush_time, 1.0)
            traffic = []
            # protocol keys now encoded as protocol:direction
            for proto_dir, packet_count in self.protocol_packets.most_common(self.top_k):
                protocol, direction = proto_dir.split(":", 1)
                traffic.append(
                    TrafficSummaryRecord(
                        timestamp=now,
                        protocol=protocol,
                        direction=direction,
                        packet_count=packet_count,
                        byte_count=self.protocol_bytes[proto_dir],
                        flow_count=self.protocol_flows[proto_dir],
                        packets_per_second=float(packet_count) / elapsed,
                        bytes_per_second=float(self.protocol_bytes[proto_dir]) / elapsed,
                    )
                )

            hosts = [
                HostSummaryRecord(
                    timestamp=now,
                    host_ip=host_ip,
                    role="both",
                    packet_count=packet_count,
                    byte_count=self.host_bytes[host_ip],
                    flow_count=self.host_flows[host_ip],
                )
                for host_ip, packet_count in self.host_packets.most_common(self.top_k)
            ]

            services = [
                ServiceSummaryRecord(
                    timestamp=now,
                    service=service_key,
                    protocol=self._protocol_from_service(service_key),
                    port=self._port_from_service(service_key),
                    packet_count=packet_count,
                    byte_count=self.service_bytes[service_key],
                    flow_count=self.service_flows[service_key],
                )
                for service_key, packet_count in self.service_packets.most_common(self.top_k)
            ]

            self._reset()
            self._last_flush_time = now
            return SummaryFlushBatch(traffic=traffic, hosts=hosts, services=services)

    def _reset(self) -> None:
        self.total_packets = 0
        self.total_bytes = 0
        self.total_flows = 0
        self.protocol_packets.clear()
        self.protocol_bytes.clear()
        self.protocol_flows.clear()
        self.host_packets.clear()
        self.host_bytes.clear()
        self.host_flows.clear()
        self.service_packets.clear()
        self.service_bytes.clear()
        self.service_flows.clear()

    @staticmethod
    def _service_key(protocol: str, port: Optional[int]) -> str:
        if port is None:
            return f"{protocol}:unknown"
        name = PORT_TO_SERVICE.get(port)
        if name:
            return name
        return f"{protocol}:{port}"

    @staticmethod
    def _protocol_from_service(service_key: str) -> str:
        if ":" in service_key:
            return service_key.split(":", 1)[0]
        # Resolved well-known name (e.g. "HTTP") — no embedded protocol.
        return service_key

    @staticmethod
    def _port_from_service(service_key: str) -> Optional[int]:
        if ":" not in service_key:
            # Reverse-lookup: resolved name → port number.
            for port, name in PORT_TO_SERVICE.items():
                if name == service_key:
                    return port
            return None
        _, port_text = service_key.split(":", 1)
        if port_text == "unknown":
            return None
        try:
            return int(port_text)
        except ValueError:
            return None