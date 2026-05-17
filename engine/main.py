import os
import time
import threading
from dotenv import load_dotenv
from core.capture import PacketSniffer
from core.flow import FlowProcessor
from core.rules import RuleEngine
from core.database import DatabaseManager
from core.summary import SummaryAggregator
from core.networks import parse_networks_csv, resolve_excluded_networks, ip_in_any_network
from core.settings import get_bool_setting, get_setting

def main():
    config_path = os.getenv("TEPEGOZ_SENSOR_CONFIG_PATH", "/etc/tepegoz-ids/sensor.conf")
    load_dotenv(config_path)
    
    print("--- Lightweight Hybrid IDS Engine Starting ---")
    print(f"Environment: {os.getenv('APP_ENV', 'development')}")
    
    # Configuration
    interface = get_setting("IDS_INTERFACE", "eth0", config_path)
    idle_timeout = float(get_setting("FLOW_IDLE_TIMEOUT", "15.0", config_path))
    max_duration = float(get_setting("FLOW_MAX_DURATION", "120.0", config_path))
    summary_flush_interval = float(get_setting("SUMMARY_FLUSH_INTERVAL", "5.0", config_path))
    rules_config = get_setting("RULES_CONFIG_PATH", "config/rules.yaml", config_path)
    auto_detect_container_nets = get_bool_setting("AUTO_DETECT_CONTAINER_NETS", True, config_path)
    suppress_excluded_internal = get_bool_setting("SUPPRESS_EXCLUDED_INTERNAL", True, config_path)
    
    # Initialize components
    rule_engine = RuleEngine(config_path=rules_config)
    db_manager = DatabaseManager()
    processor = FlowProcessor(idle_timeout=idle_timeout, max_duration=max_duration)
    summary_aggregator = SummaryAggregator(top_k=10)

    # Parse LOCAL_NETS from env (default RFC1918)
    DEFAULT_LOCAL_NETS = "10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"
    local_nets = parse_networks_csv(get_setting("LOCAL_NETS", DEFAULT_LOCAL_NETS, config_path))
    excluded_nets = resolve_excluded_networks(
        get_setting("EXCLUDE_NETS", "", config_path),
        auto_detect_container_nets=auto_detect_container_nets,
    )

    # If auto-detection was enabled but found nothing, attempt a conservative
    # set of common Docker/Hyper-V bridge subnets as a fallback so users on
    # Docker Desktop / Windows still get suppression without hardcoding.
    if auto_detect_container_nets and not excluded_nets:
        fallback_csv = get_setting(
            "FALLBACK_DOCKER_EXCLUDE_NETS",
            "172.17.0.0/16,192.168.65.0/24,10.0.75.0/24",
            config_path,
        )
        fallback_nets = parse_networks_csv(fallback_csv)
        if fallback_nets:
            excluded_nets = resolve_excluded_networks(
                ",".join(str(n) for n in fallback_nets),
                auto_detect_container_nets=False,
            )
            print("[Engine] Using fallback Docker exclude nets:", ", ".join(str(n) for n in excluded_nets))

    if excluded_nets:
        print("[Engine] Excluded internal networks:", ", ".join(str(n) for n in excluded_nets))
    else:
        print("[Engine] No excluded internal networks configured/detected")

    def ip_is_local(ip: str) -> bool:
        return ip_in_any_network(ip, local_nets)

    suppression_stats = {"excluded_internal_flows": 0}
    
    # Define callback for finalized flows
    def on_flow_finalized(flow):
        # 1. Determine direction first so suppression can happen before expensive work
        if ip_is_local(flow.src_ip) and not ip_is_local(flow.dst_ip):
            direction = "outbound"
        elif ip_is_local(flow.dst_ip) and not ip_is_local(flow.src_ip):
            direction = "inbound"
        elif ip_is_local(flow.src_ip) and ip_is_local(flow.dst_ip):
            direction = "internal"
        else:
            direction = "external"

        # 2. Suppress known container/bridge internal jitter when configured.
        if (
            suppress_excluded_internal
            and direction == "internal"
            and ip_in_any_network(flow.src_ip, excluded_nets)
            and ip_in_any_network(flow.dst_ip, excluded_nets)
        ):
            suppression_stats["excluded_internal_flows"] += 1
            if suppression_stats["excluded_internal_flows"] % 250 == 1:
                print(
                    "[Engine] Suppressed excluded internal flows:",
                    suppression_stats["excluded_internal_flows"],
                )
            return

        # 3. Evaluate rules
        alerts = rule_engine.evaluate(flow)
        
        # 4. Persist metrics
        db_manager.record_flow(flow)

        summary_aggregator.update_flow(flow, direction)
        
        # 5. Log and Persist alerts
        for alert in alerts:
            # attach direction to alert object for persistence
            try:
                setattr(alert, 'direction', direction)
            except Exception:
                pass
            print(f"[ALERT] {alert.severity} | {alert.rule_name} | {alert.src_ip} -> {alert.dst_ip} | {alert.description} | dir={direction}")
            db_manager.record_alert(alert)
            
        if not alerts:
            print(f"[FlowProcessor] Benign Flow: {flow.flow_key} | Pkts: {flow.packet_count} | Bytes: {flow.byte_count}")

    processor.on_flow_finalized = on_flow_finalized
    
    sniffer = PacketSniffer(interface=interface, callback=processor.process_packet)

    def summary_flush_loop():
        while True:
            time.sleep(summary_flush_interval)
            batch = summary_aggregator.flush()
            for traffic_summary in batch.traffic:
                db_manager.record_traffic_summary(traffic_summary)
            for host_summary in batch.hosts:
                db_manager.record_host_summary(host_summary)
            for service_summary in batch.services:
                db_manager.record_service_summary(service_summary)
    
    # Background thread for flow cleanup (expiring idle flows)
    def cleanup_loop():
        while True:
            processor.cleanup_expired_flows()
            time.sleep(5) # Run cleanup every 5 seconds
            
    summary_thread = threading.Thread(target=summary_flush_loop, daemon=True)
    summary_thread.start()

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
        batch = summary_aggregator.flush()
        for traffic_summary in batch.traffic:
            db_manager.record_traffic_summary(traffic_summary)
        for host_summary in batch.hosts:
            db_manager.record_host_summary(host_summary)
        for service_summary in batch.services:
            db_manager.record_service_summary(service_summary)
        sniffer.stop()
        db_manager.close()
        print("Engine stopped.")

if __name__ == "__main__":
    main()
