from scapy.all import sniff, IP, TCP, UDP, Ether
import time
from typing import Callable, Optional
from .contracts import PacketRecord

class PacketSniffer:
    """
    Captures network packets using Scapy and parses metadata.
    """
    def __init__(self, interface: str, callback: Callable[[PacketRecord], None]):
        self.interface = interface
        self.callback = callback
        self.is_running = False

    def start(self):
        """
        Begins the sniffing loop.
        """
        print(f"[PacketSniffer] Starting capture on interface: {self.interface}")
        self.is_running = True
        # BPF filter: capture only IP traffic
        # store=False: critical for performance/memory
        sniff(
            iface=self.interface,
            filter="ip",
            prn=self._packet_handler,
            store=False,
            stop_filter=lambda x: not self.is_running
        )

    def stop(self):
        """
        Stops the sniffing loop.
        """
        print(f"[PacketSniffer] Stopping capture on interface: {self.interface}")
        self.is_running = False

    def _packet_handler(self, packet):
        """
        Callback for each captured packet. Extracts metadata and invokes the sniffer callback.
        """
        if not IP in packet:
            return

        timestamp = time.time()
        src_ip = packet[IP].src
        dst_ip = packet[IP].dst
        protocol = "OTHER"
        src_port = None
        dst_port = None
        flags = ""
        size = len(packet)

        if TCP in packet:
            protocol = "TCP"
            src_port = packet[TCP].sport
            dst_port = packet[TCP].dport
            flags = str(packet[TCP].flags)
        elif UDP in packet:
            protocol = "UDP"
            src_port = packet[UDP].sport
            dst_port = packet[UDP].dport

        record = PacketRecord(
            timestamp=timestamp,
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=src_port,
            dst_port=dst_port,
            protocol=protocol,
            size=size,
            flags=flags
        )
        
        self.callback(record)
