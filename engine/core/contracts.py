from dataclasses import dataclass
from typing import Optional

@dataclass
class PacketRecord:
    """
    Minimal packet metadata after capture and header parsing.
    Uses __slots__ for memory efficiency in the high-velocity capture path.
    """
    __slots__ = ['timestamp', 'src_ip', 'dst_ip', 'src_port', 'dst_port', 'protocol', 'size', 'flags']
    
    timestamp: float
    src_ip: str
    dst_ip: str
    src_port: Optional[int]
    dst_port: Optional[int]
    protocol: str
    size: int
    flags: str

@dataclass
class FlowRecord:
    """
    Normalized flow summary produced by the flow processor.
    """
    __slots__ = [
        'flow_key', 'start_time', 'last_seen', 'src_ip', 'dst_ip', 
        'src_port', 'dst_port', 'protocol', 'packet_count', 'byte_count', 
        'duration', 'packets_per_second', 'bytes_per_second', 'is_finalized',
        'syn_count', 'unique_dst_ports'
    ]
    
    flow_key: str
    start_time: float
    last_seen: float
    src_ip: str
    dst_ip: str
    src_port: Optional[int]
    dst_port: Optional[int]
    protocol: str
    packet_count: int
    byte_count: int
    duration: float
    packets_per_second: float
    bytes_per_second: float
    is_finalized: bool
    syn_count: int
    unique_dst_ports: set

@dataclass
class AlertRecord:
    """
    Structured detection output produced by the rule engine.
    """
    __slots__ = ['timestamp', 'rule_name', 'severity', 'direction', 'src_ip', 'dst_ip', 'description', 'flow_key']
    
    timestamp: float
    rule_name: str
    severity: str
    src_ip: str
    dst_ip: str
    description: str
    flow_key: str
    direction: str

@dataclass
class TrafficSummaryRecord:
    """
    Low-cardinality traffic rollup used by Grafana dashboard panels.
    """
    __slots__ = ['timestamp', 'protocol', 'direction', 'packet_count', 'byte_count', 'flow_count', 'packets_per_second', 'bytes_per_second']

    timestamp: float
    protocol: str
    direction: str
    packet_count: int
    byte_count: int
    flow_count: int
    packets_per_second: float
    bytes_per_second: float

@dataclass
class HostSummaryRecord:
    """
    Top-host rollup used for Sniffnet-style dashboard rankings.
    """
    __slots__ = ['timestamp', 'host_ip', 'role', 'packet_count', 'byte_count', 'flow_count']

    timestamp: float
    host_ip: str
    role: str
    packet_count: int
    byte_count: int
    flow_count: int

@dataclass
class ServiceSummaryRecord:
    """
    Top-service rollup used for Sniffnet-style service rankings.
    """
    __slots__ = ['timestamp', 'service', 'protocol', 'port', 'packet_count', 'byte_count', 'flow_count']

    timestamp: float
    service: str
    protocol: str
    port: Optional[int]
    packet_count: int
    byte_count: int
    flow_count: int
