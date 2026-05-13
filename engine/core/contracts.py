from dataclasses import dataclass
from typing import Optional, Dict

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
    __slots__ = ['timestamp', 'rule_name', 'severity', 'src_ip', 'dst_ip', 'description', 'flow_key']
    
    timestamp: float
    rule_name: str
    severity: str
    src_ip: str
    dst_ip: str
    description: str
    flow_key: str
