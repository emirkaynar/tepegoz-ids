import yaml
import time
from typing import List, Dict
from .contracts import FlowRecord, AlertRecord

class RuleEngine:
    """
    Deterministic detection engine that evaluates FlowRecords against thresholds.
    """
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.rules = []
        self.load_rules()

    def load_rules(self):
        """
        Parses the YAML configuration file to initialize detection logic.
        """
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                self.rules = config.get('rules', [])
                print(f"[RuleEngine] Loaded {len(self.rules)} rules from {self.config_path}")
        except Exception as e:
            print(f"[RuleEngine] Error loading rules: {e}")
            self.rules = []

    def evaluate(self, flow: FlowRecord) -> List[AlertRecord]:
        """
        Evaluates a finalized flow against all enabled rules.
        """
        alerts = []
        for rule in self.rules:
            if not rule.get('enabled', True):
                continue
            
            triggered = False
            reason = ""
            
            rule_type = rule.get('type')
            
            if rule_type == 'SCANNING':
                # Port Scan: Unique destination ports exceeded
                port_count = len(flow.unique_dst_ports)
                if port_count >= rule.get('port_limit', 20):
                    triggered = True
                    reason = f"Unique destination ports ({port_count}) exceeded limit ({rule.get('port_limit')})"
            
            elif rule_type == 'PROTOCOL_ANOMALY':
                # SYN Flood: High SYN ratio and high PPS
                syn_ratio = flow.syn_count / flow.packet_count if flow.packet_count > 0 else 0
                pps = flow.packets_per_second
                
                ratio_threshold = rule.get('syn_ratio_threshold', 0.8)
                pps_threshold = rule.get('pps_threshold', 100)
                
                if syn_ratio >= ratio_threshold and pps >= pps_threshold:
                    triggered = True
                    reason = f"SYN ratio ({syn_ratio:.2f}) and PPS ({pps:.1f}) exceeded thresholds"
            
            elif rule_type == 'VOLUMETRIC':
                # Generic Volumetric Flood: High PPS or BPS
                pps = flow.packets_per_second
                bps = flow.bytes_per_second
                
                pps_t = rule.get('pps_threshold', 1000)
                bps_t = rule.get('bps_threshold', 5000000)
                
                if pps >= pps_t or bps >= bps_t:
                    triggered = True
                    reason = f"Volumetric thresholds exceeded (PPS: {pps:.1f}/{pps_t}, BPS: {bps:.1f}/{bps_t})"

            if triggered:
                alert = AlertRecord(
                    timestamp=time.time(),
                    rule_name=rule.get('name', 'Unknown'),
                    severity=rule.get('severity', 'Medium'),
                    src_ip=flow.src_ip,
                    dst_ip=flow.dst_ip,
                    description=reason,
                    flow_key=flow.flow_key
                )
                alerts.append(alert)
        
        return alerts
