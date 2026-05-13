import os
import time
import threading
from dotenv import load_dotenv
from core.capture import PacketSniffer
from core.flow import FlowProcessor
from core.rules import RuleEngine
from core.database import DatabaseManager

def main():
    load_dotenv()
    
    print("--- Lightweight Hybrid IDS Engine Starting ---")
    print(f"Environment: {os.getenv('APP_ENV', 'development')}")
    
    # Configuration
    interface = os.getenv("IDS_INTERFACE", "eth0")
    idle_timeout = float(os.getenv("FLOW_IDLE_TIMEOUT", "15.0"))
    max_duration = float(os.getenv("FLOW_MAX_DURATION", "120.0"))
    rules_config = os.getenv("RULES_CONFIG_PATH", "config/rules.yaml")
    
    # Initialize components
    rule_engine = RuleEngine(config_path=rules_config)
    db_manager = DatabaseManager()
    processor = FlowProcessor(idle_timeout=idle_timeout, max_duration=max_duration)
    
    # Define callback for finalized flows
    def on_flow_finalized(flow):
        # 1. Evaluate rules
        alerts = rule_engine.evaluate(flow)
        
        # 2. Persist metrics
        db_manager.record_flow(flow)
        
        # 3. Log and Persist alerts
        for alert in alerts:
            print(f"[ALERT] {alert.severity} | {alert.rule_name} | {alert.src_ip} -> {alert.dst_ip} | {alert.description}")
            db_manager.record_alert(alert)
            
        if not alerts:
            print(f"[FlowProcessor] Benign Flow: {flow.flow_key} | Pkts: {flow.packet_count} | Bytes: {flow.byte_count}")

    processor.on_flow_finalized = on_flow_finalized
    
    sniffer = PacketSniffer(interface=interface, callback=processor.process_packet)
    
    # Background thread for flow cleanup (expiring idle flows)
    def cleanup_loop():
        while True:
            processor.cleanup_expired_flows()
            time.sleep(5) # Run cleanup every 5 seconds
            
    cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
    cleanup_thread.start()
    
    try:
        # Start sniffing (blocks until stopped)
        sniffer.start()
    except KeyboardInterrupt:
        print("\nEngine shutting down...")
    except Exception as e:
        print(f"\nCritical Error: {e}")
    finally:
        sniffer.stop()
        db_manager.close()
        print("Engine stopped.")

if __name__ == "__main__":
    main()
