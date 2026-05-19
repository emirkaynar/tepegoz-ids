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

  - name: "Volumetric Flood"
    enabled: true
    severity: "Medium"
    logic: "any"
    conditions:
      - field: "packets_per_second"
        op: "gte"
        value: 1000
      - field: "bytes_per_second"
        op: "gte"
        value: 5000000
    description: "Volume: {packets_per_second:.1f} pps / {bytes_per_second:.1f} Bps"

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

def test_volumetric_any_logic_pps(rule_engine):
    """Volumetric uses 'any' logic — only PPS threshold exceeded."""
    flow = _flow(src_ip="4.4.4.4", packets=2000, bytes_count=2000, duration=1.0)
    alerts = rule_engine.evaluate(flow, "inbound")
    assert any(a.rule_name == "Volumetric Flood" for a in alerts)


def test_volumetric_any_logic_bps(rule_engine):
    """Volumetric uses 'any' logic — only BPS threshold exceeded."""
    flow = _flow(src_ip="5.5.5.5", packets=10, bytes_count=10000000, duration=1.0)
    alerts = rule_engine.evaluate(flow, "inbound")
    assert any(a.rule_name == "Volumetric Flood" for a in alerts)


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


def test_cooldown_suppresses_duplicate_alerts(tmp_path):
    """With cooldown enabled, the same rule+src_ip should not fire twice."""
    config_file = tmp_path / "rules_cd.yaml"
    config_file.write_text("""
rules:
  - name: "Test Rule"
    enabled: true
    severity: "High"
    logic: "all"
    conditions:
      - field: "packet_count"
        op: "gte"
        value: 1
    description: "Test"
""")
    engine = RuleEngine(str(config_file), cooldown_seconds=60.0)

    flow1 = _flow(src_ip="99.99.99.99", packets=5)
    flow2 = _flow(src_ip="99.99.99.99", packets=10)

    alerts1 = engine.evaluate(flow1, "inbound")
    alerts2 = engine.evaluate(flow2, "inbound")

    assert len(alerts1) == 1  # First fires
    assert len(alerts2) == 0  # Second is suppressed by cooldown

