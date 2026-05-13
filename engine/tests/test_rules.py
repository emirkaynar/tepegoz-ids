import pytest # type: ignore
import time
from core.contracts import PacketRecord, FlowRecord
from core.flow import FlowProcessor
from core.rules import RuleEngine

@pytest.fixture
def rule_engine(tmp_path):
    config_file = tmp_path / "rules.yaml"
    config_content = """
rules:
  - name: "Port Scan"
    type: "SCANNING"
    enabled: true
    severity: "High"
    port_limit: 5
    description: "Detects port scans."
  - name: "DoS SYN Flood"
    type: "PROTOCOL_ANOMALY"
    enabled: true
    severity: "Critical"
    syn_ratio_threshold: 0.8
    pps_threshold: 10
    description: "Detects SYN floods."
"""
    config_file.write_text(config_content)
    return RuleEngine(str(config_file))

def test_port_scan_detection(rule_engine):
    # Simulate a flow connecting to 6 unique ports (limit is 5)
    flow = FlowRecord(
        flow_key="1.1.1.1:1234->2.2.2.2:80|TCP",
        start_time=time.time(),
        last_seen=time.time(),
        src_ip="1.1.1.1",
        dst_ip="2.2.2.2",
        src_port=1234,
        dst_port=80,
        protocol="TCP",
        packet_count=6,
        byte_count=600,
        duration=1.0,
        packets_per_second=6.0,
        bytes_per_second=600.0,
        is_finalized=True,
        syn_count=6,
        unique_dst_ports={80, 81, 82, 83, 84, 85}
    )
    
    alerts = rule_engine.evaluate(flow)
    assert len(alerts) == 1
    assert alerts[0].rule_name == "Port Scan"
    assert "Unique destination ports (6)" in alerts[0].description

def test_syn_flood_detection(rule_engine):
    # Simulate a flow with high SYN ratio and high PPS
    flow = FlowRecord(
        flow_key="1.1.1.1:1234->2.2.2.2:80|TCP",
        start_time=time.time(),
        last_seen=time.time() + 1.0,
        src_ip="1.1.1.1",
        dst_ip="2.2.2.2",
        src_port=1234,
        dst_port=80,
        protocol="TCP",
        packet_count=20,
        byte_count=1200,
        duration=1.0,
        packets_per_second=20.0,
        bytes_per_second=1200.0,
        is_finalized=True,
        syn_count=18, # 18/20 = 0.9 ratio
        unique_dst_ports={80}
    )
    
    alerts = rule_engine.evaluate(flow)
    assert any(a.rule_name == "DoS SYN Flood" for a in alerts)

def test_benign_flow(rule_engine):
    flow = FlowRecord(
        flow_key="1.1.1.1:1234->2.2.2.2:80|TCP",
        start_time=time.time(),
        last_seen=time.time() + 10.0,
        src_ip="1.1.1.1",
        dst_ip="2.2.2.2",
        src_port=1234,
        dst_port=80,
        protocol="TCP",
        packet_count=10,
        byte_count=1000,
        duration=10.0,
        packets_per_second=1.0,
        bytes_per_second=100.0,
        is_finalized=True,
        syn_count=1,
        unique_dst_ports={80}
    )
    
    alerts = rule_engine.evaluate(flow)
    assert len(alerts) == 0
