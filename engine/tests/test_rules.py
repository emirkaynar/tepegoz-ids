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
      - field: "unique_dst_ports_count"
        op: "gte"
        value: 5
    description: "Scanned {unique_dst_ports_count} ports"

  - name: "DoS SYN Flood"
    enabled: true
    severity: "Critical"
    logic: "all"
    conditions:
      - field: "syn_ratio"
        op: "gte"
        value: 0.8
      - field: "packets_per_second"
        op: "gte"
        value: 10
    description: "SYN ratio {syn_ratio:.2f} at {packets_per_second:.1f} pps"

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
    return RuleEngine(str(config_file))


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
# Existing detection behaviour preserved
# ------------------------------------------------------------------

def test_port_scan_detection(rule_engine):
    flow = _flow(unique_dst_ports={80, 81, 82, 83, 84, 85})
    alerts = rule_engine.evaluate(flow, "outbound")
    assert len(alerts) >= 1
    assert any(a.rule_name == "Port Scan" for a in alerts)
    assert "6" in alerts[0].description  # unique port count rendered


def test_syn_flood_detection(rule_engine):
    flow = _flow(packets=20, syn_count=18, duration=1.0)
    alerts = rule_engine.evaluate(flow, "inbound")
    assert any(a.rule_name == "DoS SYN Flood" for a in alerts)


def test_benign_flow(rule_engine):
    flow = _flow(packets=10, bytes_count=1000, duration=10.0, syn_count=1)
    alerts = rule_engine.evaluate(flow, "internal")
    assert len(alerts) == 0


# ------------------------------------------------------------------
# New detection patterns
# ------------------------------------------------------------------

def test_volumetric_any_logic_pps(rule_engine):
    """Volumetric uses 'any' logic — only PPS threshold exceeded."""
    flow = _flow(packets=2000, bytes_count=2000, duration=1.0)
    alerts = rule_engine.evaluate(flow, "inbound")
    assert any(a.rule_name == "Volumetric Flood" for a in alerts)


def test_volumetric_any_logic_bps(rule_engine):
    """Volumetric uses 'any' logic — only BPS threshold exceeded."""
    flow = _flow(packets=10, bytes_count=10000000, duration=1.0)
    alerts = rule_engine.evaluate(flow, "inbound")
    assert any(a.rule_name == "Volumetric Flood" for a in alerts)


def test_udp_flood_detection(rule_engine):
    flow = _flow(protocol="UDP", packets=600, bytes_count=60000, duration=1.0)
    alerts = rule_engine.evaluate(flow, "inbound")
    assert any(a.rule_name == "UDP Flood" for a in alerts)


def test_udp_flood_does_not_trigger_on_tcp(rule_engine):
    """UDP Flood rule should not fire for TCP traffic."""
    flow = _flow(protocol="TCP", packets=600, bytes_count=60000, duration=1.0)
    alerts = rule_engine.evaluate(flow, "inbound")
    assert not any(a.rule_name == "UDP Flood" for a in alerts)


def test_direction_based_exfil(rule_engine):
    flow = _flow(bytes_count=2000000, duration=60.0, packets=500)
    alerts = rule_engine.evaluate(flow, "outbound")
    assert any(a.rule_name == "Outbound Exfil" for a in alerts)


def test_direction_based_exfil_not_inbound(rule_engine):
    """Exfil rule should not fire for inbound traffic."""
    flow = _flow(bytes_count=2000000, duration=60.0, packets=500)
    alerts = rule_engine.evaluate(flow, "inbound")
    assert not any(a.rule_name == "Outbound Exfil" for a in alerts)


def test_disabled_rule_does_not_fire(rule_engine):
    flow = _flow(packets=100)
    alerts = rule_engine.evaluate(flow, "outbound")
    assert not any(a.rule_name == "Disabled Rule" for a in alerts)


def test_description_template_renders(rule_engine):
    """Verify that template placeholders in descriptions are filled."""
    flow = _flow(packets=20, syn_count=18, duration=1.0)
    alerts = rule_engine.evaluate(flow, "inbound")
    syn_alerts = [a for a in alerts if a.rule_name == "DoS SYN Flood"]
    assert len(syn_alerts) == 1
    # Template should have rendered the syn_ratio and pps values
    assert "0.90" in syn_alerts[0].description
    assert "20.0" in syn_alerts[0].description
