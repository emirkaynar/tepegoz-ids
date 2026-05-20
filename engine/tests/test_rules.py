import pytest  # type: ignore
import time
from core.contracts import FlowRecord
from core.rules import RuleEngine


@pytest.fixture
def rule_engine(tmp_path):
    config_file = tmp_path / "rules.yaml"
    config_content = """
rules:
  - name: "Port Scan"
    enabled: true
    severity: "High"
    logic: "all"
    conditions:
      - field: "cross_unique_dst_ports"
        op: "gte"
        value: 5
    description: "Scanned {cross_unique_dst_ports} ports"

  - name: "DoS SYN Flood"
    enabled: true
    severity: "Critical"
    logic: "all"
    conditions:
      - field: "cross_syn_ratio"
        op: "gte"
        value: 0.8
      - field: "cross_pps"
        op: "gte"
        value: 10
    description: "Cross-flow SYN ratio {cross_syn_ratio:.2f} at {cross_pps:.0f} pps"

  - name: "Volumetric Flood (PPS)"
    enabled: true
    severity: "Medium"
    logic: "all"
    conditions:
      - field: "packets_per_second"
        op: "gte"
        value: 1000
      - field: "packet_count"
        op: "gte"
        value: 500
    description: "Volume PPS: {packets_per_second:.1f} pps over {packet_count} packets"

  - name: "Volumetric Flood (Bps)"
    enabled: true
    severity: "Medium"
    logic: "all"
    conditions:
      - field: "bytes_per_second"
        op: "gte"
        value: 5000000
      - field: "byte_count"
        op: "gte"
        value: 10000000
    description: "Volume Bps: {bytes_per_second:.1f} Bps (total {byte_count} bytes)"

  - name: "UDP Flood"
    enabled: true
    severity: "High"
    logic: "all"
    conditions:
      - field: "protocol"
        op: "eq"
        value: "UDP"
      - field: "packets_per_second"
        op: "gte"
        value: 500
    description: "UDP flood at {packets_per_second:.0f} pps"

  - name: "Outbound Exfil"
    enabled: true
    severity: "High"
    logic: "all"
    conditions:
      - field: "direction"
        op: "eq"
        value: "outbound"
      - field: "byte_count"
        op: "gte"
        value: 1000000
    description: "Large outbound transfer: {byte_count} bytes"

  - name: "Disabled Rule"
    enabled: false
    severity: "Low"
    logic: "all"
    conditions:
      - field: "packet_count"
        op: "gte"
        value: 1
    description: "This should never fire"

  - name: "ICMP Flood"
    enabled: true
    severity: "High"
    logic: "all"
    conditions:
      - field: "protocol"
        op: "eq"
        value: "ICMP"
      - field: "cross_pps"
        op: "gte"
        value: 10
      - field: "cross_flow_count"
        op: "gte"
        value: 5
    description: "ICMP flood at {cross_pps:.0f} pps across {cross_flow_count} flows"

  - name: "SSH Brute Force"
    enabled: true
    severity: "High"
    logic: "all"
    conditions:
      - field: "protocol"
        op: "eq"
        value: "TCP"
      - field: "dst_port"
        op: "eq"
        value: 22
      - field: "cross_flow_count"
        op: "gte"
        value: 5
      - field: "cross_pps"
        op: "gte"
        value: 3
    description: "SSH brute force: {cross_flow_count} attempts at {cross_pps:.0f} pps"

  - name: "RDP Brute Force"
    enabled: true
    severity: "High"
    logic: "all"
    conditions:
      - field: "protocol"
        op: "eq"
        value: "TCP"
      - field: "dst_port"
        op: "eq"
        value: 3389
      - field: "cross_flow_count"
        op: "gte"
        value: 5
      - field: "cross_pps"
        op: "gte"
        value: 3
    description: "RDP brute force: {cross_flow_count} attempts at {cross_pps:.0f} pps"
"""
    config_file.write_text(config_content)
    # Disable cooldown for most tests so repeated evaluations aren't suppressed
    return RuleEngine(str(config_file), cooldown_seconds=0)


def _flow(src_ip="1.1.1.1", dst_ip="2.2.2.2", protocol="TCP",
          src_port=1234, dst_port=80, packets=10, bytes_count=1000,
          duration=1.0, syn_count=1, unique_dst_ports=None):
    if unique_dst_ports is None:
        unique_dst_ports = {dst_port}
    pps = float(packets) / duration if duration > 0 else 0.0
    bps = float(bytes_count) / duration if duration > 0 else 0.0
    return FlowRecord(
        flow_key=f"{src_ip}:{src_port}->{dst_ip}:{dst_port}|{protocol}",
        start_time=time.time() - duration,
        last_seen=time.time(),
        src_ip=src_ip,
        dst_ip=dst_ip,
        src_port=src_port,
        dst_port=dst_port,
        protocol=protocol,
        packet_count=packets,
        byte_count=bytes_count,
        duration=duration,
        packets_per_second=pps,
        bytes_per_second=bps,
        is_finalized=True,
        syn_count=syn_count,
        unique_dst_ports=unique_dst_ports,
    )


# ------------------------------------------------------------------
# Cross-flow: Port Scan
# ------------------------------------------------------------------

def test_port_scan_detection_cross_flow(rule_engine):
    """Port scan across 6 separate flows (each with 1 unique port) should trigger."""
    for port in range(80, 86):
        flow = _flow(src_ip="1.1.1.1", dst_port=port, src_port=40000 + port)
        alerts = rule_engine.evaluate(flow, "outbound")

    # After 6 flows from same src_ip, cross_unique_dst_ports = 6 >= 5
    assert any(a.rule_name == "Port Scan" for a in alerts)


def test_port_scan_does_not_trigger_on_single_flow(rule_engine):
    """A single flow to one port should not trigger port scan."""
    flow = _flow(src_ip="9.9.9.9", dst_port=80)
    alerts = rule_engine.evaluate(flow, "outbound")
    assert not any(a.rule_name == "Port Scan" for a in alerts)


# ------------------------------------------------------------------
# Cross-flow: SYN Flood
# ------------------------------------------------------------------

def test_syn_flood_cross_flow(rule_engine):
    """Many short SYN-only flows from the same source should trigger."""
    alerts = []
    for i in range(20):
        flow = _flow(
            src_ip="3.3.3.3", dst_ip="2.2.2.2", dst_port=80,
            src_port=50000 + i, packets=1, bytes_count=60,
            duration=0.0, syn_count=1,
        )
        alerts = rule_engine.evaluate(flow, "inbound")

    # cross_total_syn=20, cross_total_packets=20, ratio=1.0, cross_pps > 10
    assert any(a.rule_name == "DoS SYN Flood" for a in alerts)


# ------------------------------------------------------------------
# Per-flow: Volumetric
# ------------------------------------------------------------------

def test_volumetric_pps_flood(rule_engine):
    """Volumetric PPS rule requires both rate and packet count to exceed thresholds."""
    # Scenario A: Rate is high, but packet count is low -> no alert
    flow_low_count = _flow(src_ip="4.4.4.4", packets=10, bytes_count=1000, duration=0.005)
    alerts = rule_engine.evaluate(flow_low_count, "inbound")
    assert not any(a.rule_name == "Volumetric Flood (PPS)" for a in alerts)

    # Scenario B: Both rate and packet count are high -> alert
    flow_high = _flow(src_ip="4.4.4.4", packets=2000, bytes_count=2000, duration=1.0)
    alerts = rule_engine.evaluate(flow_high, "inbound")
    assert any(a.rule_name == "Volumetric Flood (PPS)" for a in alerts)


def test_volumetric_bps_flood(rule_engine):
    """Volumetric Bps rule requires both rate and byte count to exceed thresholds."""
    # Scenario A: Rate is high, but byte count is low -> no alert
    flow_low_bytes = _flow(src_ip="5.5.5.5", packets=1, bytes_count=1000, duration=0.0001)
    alerts = rule_engine.evaluate(flow_low_bytes, "inbound")
    assert not any(a.rule_name == "Volumetric Flood (Bps)" for a in alerts)

    # Scenario B: Both rate and byte count are high -> alert
    flow_high = _flow(src_ip="5.5.5.5", packets=10, bytes_count=10000000, duration=1.0)
    alerts = rule_engine.evaluate(flow_high, "inbound")
    assert any(a.rule_name == "Volumetric Flood (Bps)" for a in alerts)


# ------------------------------------------------------------------
# Per-flow: UDP Flood
# ------------------------------------------------------------------

def test_udp_flood_detection(rule_engine):
    flow = _flow(src_ip="6.6.6.6", protocol="UDP", packets=600, bytes_count=60000, duration=1.0)
    alerts = rule_engine.evaluate(flow, "inbound")
    assert any(a.rule_name == "UDP Flood" for a in alerts)


def test_udp_flood_does_not_trigger_on_tcp(rule_engine):
    """UDP Flood rule should not fire for TCP traffic."""
    flow = _flow(src_ip="7.7.7.7", protocol="TCP", packets=600, bytes_count=60000, duration=1.0)
    alerts = rule_engine.evaluate(flow, "inbound")
    assert not any(a.rule_name == "UDP Flood" for a in alerts)


# ------------------------------------------------------------------
# Direction-based
# ------------------------------------------------------------------

def test_direction_based_exfil(rule_engine):
    flow = _flow(src_ip="8.8.8.8", bytes_count=2000000, duration=60.0, packets=500)
    alerts = rule_engine.evaluate(flow, "outbound")
    assert any(a.rule_name == "Outbound Exfil" for a in alerts)


def test_direction_based_exfil_not_inbound(rule_engine):
    """Exfil rule should not fire for inbound traffic."""
    flow = _flow(src_ip="10.10.10.10", bytes_count=2000000, duration=60.0, packets=500)
    alerts = rule_engine.evaluate(flow, "inbound")
    assert not any(a.rule_name == "Outbound Exfil" for a in alerts)


# ------------------------------------------------------------------
# Misc
# ------------------------------------------------------------------

def test_disabled_rule_does_not_fire(rule_engine):
    flow = _flow(src_ip="11.11.11.11", packets=100)
    alerts = rule_engine.evaluate(flow, "outbound")
    assert not any(a.rule_name == "Disabled Rule" for a in alerts)


def test_benign_flow(rule_engine):
    flow = _flow(
        src_ip="12.12.12.12", packets=10, bytes_count=1000,
        duration=10.0, syn_count=1,
    )
    alerts = rule_engine.evaluate(flow, "internal")
    assert len(alerts) == 0


def test_description_template_renders(rule_engine):
    """Verify cross-flow template placeholders are filled."""
    for port in range(80, 86):
        flow = _flow(src_ip="13.13.13.13", dst_port=port, src_port=40000 + port)
        alerts = rule_engine.evaluate(flow, "outbound")

    scan_alerts = [a for a in alerts if a.rule_name == "Port Scan"]
    assert len(scan_alerts) == 1
    assert "6" in scan_alerts[0].description



def test_parse_ports_csv():
    from core.rules import parse_ports_csv
    assert parse_ports_csv("80,443") == {80, 443}
    assert parse_ports_csv("8000-8005,9000") == {8000, 8001, 8002, 8003, 8004, 8005, 9000}
    assert parse_ports_csv("") == set()


def test_port_scan_filtering_ephemeral_and_flag_aware(tmp_path):
    """Verify that EXCLUDE_PORTS and syn_count=0 (TCP return traffic) are filtered out of port scans."""
    config_file = tmp_path / "rules_exclude.yaml"
    config_file.write_text("""
rules:
  - name: "Port Scan"
    enabled: true
    severity: "High"
    logic: "all"
    conditions:
      - field: "cross_unique_dst_ports"
        op: "gte"
        value: 3
    description: "Scanned {cross_unique_dst_ports} ports"
""")
    # Exclude ports 8000 and 8080
    engine = RuleEngine(str(config_file), cooldown_seconds=0, exclude_ports={8000, 8080})

    # Scenario A: Flow to excluded port (8000) -> should not count
    flow1 = _flow(src_ip="20.20.20.20", dst_port=8000, syn_count=1)
    alerts = engine.evaluate(flow1, "inbound")
    assert len(alerts) == 0

    # Scenario B: TCP return traffic flow (syn_count=0, e.g. on port 9001) -> should not count
    flow2 = _flow(src_ip="20.20.20.20", dst_port=9001, syn_count=0)
    alerts = engine.evaluate(flow2, "inbound")
    assert len(alerts) == 0

    # Scenario C: Flows to allowed ports with syn_count=1 -> should trigger after 3 unique ports
    for port in [80, 443, 22]:
        flow = _flow(src_ip="20.20.20.20", dst_port=port, syn_count=1)
        alerts = engine.evaluate(flow, "inbound")
    
    assert any(a.rule_name == "Port Scan" for a in alerts)


def test_rule_specific_cooldown(tmp_path):
    """Verify that rule-specific cooldowns are respected and fall back correctly."""
    config_file = tmp_path / "rules_cooldown.yaml"
    config_file.write_text("""
rules:
  - name: "Port Scan"
    enabled: true
    severity: "High"
    logic: "all"
    cooldown_seconds: 2
    conditions:
      - field: "cross_unique_dst_ports"
        op: "gte"
        value: 2
    description: "Scanned {cross_unique_dst_ports} ports"
""")
    # Set fallback default cooldown to 1 second
    engine = RuleEngine(str(config_file), cooldown_seconds=1)

    # Trigger rule once
    flow1 = _flow(src_ip="30.30.30.30", dst_port=80, syn_count=1)
    engine.evaluate(flow1)
    flow2 = _flow(src_ip="30.30.30.30", dst_port=443, syn_count=1)
    alerts1 = engine.evaluate(flow2)
    assert len(alerts1) == 1  # Fired!

    # Immediate second trigger -> suppressed by the 2s cooldown
    flow3 = _flow(src_ip="30.30.30.30", dst_port=22, syn_count=1)
    alerts2 = engine.evaluate(flow3)
    assert len(alerts2) == 0  # Suppressed!

    # Wait 2.1 seconds for cooldown to expire
    time.sleep(2.1)

    # Should fire again
    flow4 = _flow(src_ip="30.30.30.30", dst_port=23, syn_count=1)
    alerts3 = engine.evaluate(flow4)
    assert len(alerts3) == 1  # Fired again!


# ------------------------------------------------------------------
# Cross-flow: ICMP Flood
# ------------------------------------------------------------------

def test_icmp_flood_detection(rule_engine):
    """Many ICMP flows from the same source should trigger ICMP Flood."""
    alerts = []
    for i in range(15):
        flow = _flow(
            src_ip="40.40.40.40", dst_ip=f"10.0.0.{i+1}", protocol="ICMP",
            src_port=None, dst_port=None, packets=5, bytes_count=400,
            duration=0.1, syn_count=0,
            unique_dst_ports=set(),
        )
        alerts = rule_engine.evaluate(flow, "outbound")

    assert any(a.rule_name == "ICMP Flood" for a in alerts)


def test_icmp_flood_not_triggered_on_tcp(rule_engine):
    """ICMP Flood rule should not fire for TCP traffic."""
    alerts = []
    for i in range(15):
        flow = _flow(
            src_ip="41.41.41.41", dst_ip=f"10.0.0.{i+1}", protocol="TCP",
            packets=5, bytes_count=400, duration=0.1, syn_count=1,
        )
        alerts = rule_engine.evaluate(flow, "outbound")

    assert not any(a.rule_name == "ICMP Flood" for a in alerts)


# ------------------------------------------------------------------
# Cross-flow: SSH Brute Force
# ------------------------------------------------------------------

def test_ssh_brute_force_detection(rule_engine):
    """Many short TCP flows to port 22 from the same source should trigger."""
    alerts = []
    for i in range(12):
        flow = _flow(
            src_ip="42.42.42.42", dst_ip="10.0.0.1", protocol="TCP",
            src_port=50000 + i, dst_port=22, packets=5, bytes_count=300,
            duration=0.5, syn_count=1,
        )
        alerts = rule_engine.evaluate(flow, "inbound")

    assert any(a.rule_name == "SSH Brute Force" for a in alerts)


def test_ssh_brute_force_not_triggered_on_low_count(rule_engine):
    """Only 2 flows to port 22 should not trigger brute force."""
    alerts = []
    for i in range(2):
        flow = _flow(
            src_ip="43.43.43.43", dst_ip="10.0.0.1", protocol="TCP",
            src_port=50000 + i, dst_port=22, packets=5, bytes_count=300,
            duration=0.5, syn_count=1,
        )
        alerts = rule_engine.evaluate(flow, "inbound")

    assert not any(a.rule_name == "SSH Brute Force" for a in alerts)


# ------------------------------------------------------------------
# Cross-flow: RDP Brute Force
# ------------------------------------------------------------------

def test_rdp_brute_force_detection(rule_engine):
    """Many short TCP flows to port 3389 from the same source should trigger."""
    alerts = []
    for i in range(12):
        flow = _flow(
            src_ip="44.44.44.44", dst_ip="10.0.0.1", protocol="TCP",
            src_port=50000 + i, dst_port=3389, packets=5, bytes_count=300,
            duration=0.5, syn_count=1,
        )
        alerts = rule_engine.evaluate(flow, "inbound")

    assert any(a.rule_name == "RDP Brute Force" for a in alerts)


def test_rdp_brute_force_not_triggered_on_wrong_port(rule_engine):
    """Flows to port 80 should not trigger RDP brute force."""
    alerts = []
    for i in range(12):
        flow = _flow(
            src_ip="45.45.45.45", dst_ip="10.0.0.1", protocol="TCP",
            src_port=50000 + i, dst_port=80, packets=5, bytes_count=300,
            duration=0.5, syn_count=1,
        )
        alerts = rule_engine.evaluate(flow, "inbound")

    assert not any(a.rule_name == "RDP Brute Force" for a in alerts)


