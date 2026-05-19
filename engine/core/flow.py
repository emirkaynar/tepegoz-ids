import time
from threading import Lock
from typing import Dict, Optional, Callable, List
from .contracts import PacketRecord, FlowRecord

class FlowProcessor:
    """
    Aggregates PacketRecords into FlowRecords and manages flow lifecycle.
    """
    def __init__(self, idle_timeout: float = 15.0, max_duration: float = 120.0):
        self.idle_timeout = idle_timeout
        self.max_duration = max_duration
        self.active_flows: Dict[str, FlowRecord] = {}
        self.on_flow_finalized: Optional[Callable[[FlowRecord], None]] = None
        self._lock = Lock()

    def process_packet(self, packet: PacketRecord):
        """
        Maps a packet to a flow and updates stats.
        """
        # Generate 5-tuple flow key: (src_ip, dst_ip, src_port, dst_port, protocol)
        flow_key = f"{packet.src_ip}:{packet.src_port}->{packet.dst_ip}:{packet.dst_port}|{packet.protocol}"
        flow_to_finalize = None
        
        with self._lock:
            if flow_key in self.active_flows:
                flow = self.active_flows[flow_key]
                flow.packet_count += 1
                flow.byte_count += packet.size
                flow.last_seen = packet.timestamp
                flow.duration = flow.last_seen - flow.start_time
                
                # Update metrics for rules (only count pure SYN packets, ignoring SYN-ACK responses)
                if 'S' in packet.flags and 'A' not in packet.flags:
                    flow.syn_count += 1
                if packet.dst_port:
                    flow.unique_dst_ports.add(packet.dst_port)
                
                # Check for TCP termination flags (FIN/RST)
                if 'F' in packet.flags or 'R' in packet.flags:
                    flow_to_finalize = self._pop_and_finalize_flow(flow_key)
                elif flow.duration >= self.max_duration:
                    flow_to_finalize = self._pop_and_finalize_flow(flow_key)
            else:
                # Create new flow
                new_flow = FlowRecord(
                    flow_key=flow_key,
                    start_time=packet.timestamp,
                    last_seen=packet.timestamp,
                    src_ip=packet.src_ip,
                    dst_ip=packet.dst_ip,
                    src_port=packet.src_port,
                    dst_port=packet.dst_port,
                    protocol=packet.protocol,
                    packet_count=1,
                    byte_count=packet.size,
                    duration=0.0,
                    packets_per_second=0.0,
                    bytes_per_second=0.0,
                    is_finalized=False,
                    syn_count=1 if ('S' in packet.flags and 'A' not in packet.flags) else 0,
                    unique_dst_ports={packet.dst_port} if packet.dst_port else set()
                )
                self.active_flows[flow_key] = new_flow

        if flow_to_finalize:
            self._trigger_callback(flow_to_finalize)

    def cleanup_expired_flows(self):
        """
        Checks for flows that have timed out.
        Should be called periodically (e.g., every few seconds).
        """
        current_time = time.time()
        flows_to_finalize = []
        
        with self._lock:
            expired_keys = [
                key for key, flow in self.active_flows.items()
                if current_time - flow.last_seen > self.idle_timeout
            ]
            for key in expired_keys:
                flow = self._pop_and_finalize_flow(key)
                if flow:
                    flows_to_finalize.append(flow)
        
        for flow in flows_to_finalize:
            self._trigger_callback(flow)

    def _pop_and_finalize_flow(self, flow_key: str) -> Optional[FlowRecord]:
        """
        Pops the flow from active_flows and computes final rates.
        Must be called while holding self._lock.
        """
        flow = self.active_flows.pop(flow_key, None)
        if flow:
            flow.is_finalized = True
            # Compute rates
            if flow.duration > 0:
                flow.packets_per_second = flow.packet_count / flow.duration
                flow.bytes_per_second = flow.byte_count / flow.duration
            return flow
        return None

    def _trigger_callback(self, flow: FlowRecord):
        """
        Triggers the finalization callback. Should be called outside the lock.
        """
        if self.on_flow_finalized:
            self.on_flow_finalized(flow)
        else:
            # Fallback log for Milestone 2 verification
            print(f"[FlowProcessor] Finalized Flow: {flow.flow_key} | Pkts: {flow.packet_count} | Bytes: {flow.byte_count}")
