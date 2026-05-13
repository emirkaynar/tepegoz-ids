from scapy.all import PcapReader, IP, TCP, UDP
import time
import sys
import os

# Add engine directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.contracts import PacketRecord
from core.flow import FlowProcessor
from core.rules import RuleEngine

def replay_pcap(pcap_path, rules_path):
    print(f"--- PCAP Replayer Starting ---")
    print(f"PCAP: {pcap_path}")
    print(f"Rules: {rules_path}")

    # Initialize components
    rule_engine = RuleEngine(config_path=rules_path)
    processor = FlowProcessor()
    
    def on_flow_finalized(flow):
        alerts = rule_engine.evaluate(flow)
        for alert in alerts:
            print(f"[REPLAY-ALERT] {alert.severity} | {alert.rule_name} | {alert.src_ip} -> {alert.dst_ip}")
        # Benign flows are silenced for massive PCAPs to save console I/O
        # if not alerts:
        #     print(f"[REPLAY] Benign Flow: {flow.flow_key}")

    processor.on_flow_finalized = on_flow_finalized

    print(f"Starting streaming processing. This will process packets one-by-one to save memory...")
    count = 0
    
    try:
        # PcapReader reads one packet at a time, preventing OOM on 8-12GB files
        with PcapReader(pcap_path) as pcap_reader:
            for packet in pcap_reader:
                count += 1
                if count % 100000 == 0:
                    print(f"Processed {count} packets...")
                    # Periodically clean up flows to prevent memory bloat during long replays
                    processor.cleanup_expired_flows()

                if IP in packet:
                    timestamp = float(packet.time)
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
                    processor.process_packet(record)

    except Exception as e:
        print(f"Error reading PCAP: {e}")
        return

    # Final sweep
    processor.cleanup_expired_flows()
    print(f"--- PCAP Replayer Finished. Total packets: {count} ---")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pcap_replay.py <pcap_file> [rules_file]")
        sys.exit(1)
    
    pcap = sys.argv[1]
    rules = sys.argv[2] if len(sys.argv) > 2 else "../config/rules.yaml"
    replay_pcap(pcap, rules)
