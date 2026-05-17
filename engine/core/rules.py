import yaml
import time
from typing import List, Dict, Any, Optional
from .contracts import FlowRecord, AlertRecord

# Supported comparison operators for rule conditions.
_OPS = {
    "eq":  lambda a, b: a == b,
    "neq": lambda a, b: a != b,
    "gt":  lambda a, b: a > b,
    "gte": lambda a, b: a >= b,
    "lt":  lambda a, b: a < b,
    "lte": lambda a, b: a <= b,
}


class RuleEngine:
    """
    Schema-driven detection engine that evaluates FlowRecords against
    declarative YAML conditions.

    Each rule defines a list of {field, op, value} conditions and a
    logic mode ('all' or 'any').  Virtual fields (avg_packet_size,
    syn_ratio, unique_dst_ports_count, direction) are computed on demand
    from the FlowRecord without requiring upstream changes.
    """

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.rules: List[Dict[str, Any]] = []
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

    # ------------------------------------------------------------------
    # Virtual field computation
    # ------------------------------------------------------------------

    @staticmethod
    def _build_context(flow: FlowRecord, direction: str) -> Dict[str, Any]:
        """
        Build a flat dict of all fields available for condition evaluation.
        Includes raw FlowRecord attributes plus computed virtual fields.
        """
        pkt = flow.packet_count if flow.packet_count > 0 else 1

        ctx: Dict[str, Any] = {
            # Raw FlowRecord fields
            "flow_key": flow.flow_key,
            "src_ip": flow.src_ip,
            "dst_ip": flow.dst_ip,
            "src_port": flow.src_port,
            "dst_port": flow.dst_port,
            "protocol": flow.protocol,
            "packet_count": flow.packet_count,
            "byte_count": flow.byte_count,
            "duration": flow.duration,
            "packets_per_second": flow.packets_per_second,
            "bytes_per_second": flow.bytes_per_second,
            "syn_count": flow.syn_count,
            # Computed virtual fields
            "avg_packet_size": flow.byte_count / pkt,
            "syn_ratio": flow.syn_count / pkt,
            "unique_dst_ports_count": len(flow.unique_dst_ports),
            "direction": direction,
        }
        return ctx

    # ------------------------------------------------------------------
    # Condition evaluation
    # ------------------------------------------------------------------

    @staticmethod
    def _evaluate_condition(ctx: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """
        Evaluate a single {field, op, value} condition against the context.
        Returns False (safe) if the field is missing or the operator is unknown.
        """
        field = condition.get("field")
        op_name = condition.get("op")
        expected = condition.get("value")

        if field is None or op_name is None or expected is None:
            return False

        actual = ctx.get(field)
        if actual is None:
            return False

        op_fn = _OPS.get(op_name)
        if op_fn is None:
            return False

        try:
            return op_fn(actual, expected)
        except TypeError:
            return False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(self, flow: FlowRecord, direction: str = "unknown") -> List[AlertRecord]:
        """
        Evaluates a finalized flow against all enabled rules.
        """
        ctx = self._build_context(flow, direction)
        alerts: List[AlertRecord] = []

        for rule in self.rules:
            if not rule.get('enabled', True):
                continue

            conditions = rule.get('conditions', [])
            if not conditions:
                continue

            logic = rule.get('logic', 'all')

            if logic == 'any':
                triggered = any(
                    self._evaluate_condition(ctx, c) for c in conditions
                )
            else:
                triggered = all(
                    self._evaluate_condition(ctx, c) for c in conditions
                )

            if triggered:
                # Build description from template with context values
                desc_template = rule.get('description', '')
                try:
                    reason = desc_template.format(**ctx)
                except (KeyError, ValueError, IndexError):
                    reason = desc_template

                alert = AlertRecord(
                    timestamp=time.time(),
                    rule_name=rule.get('name', 'Unknown'),
                    severity=rule.get('severity', 'Medium'),
                    src_ip=flow.src_ip,
                    dst_ip=flow.dst_ip,
                    description=reason,
                    flow_key=flow.flow_key,
                )
                alerts.append(alert)

        return alerts
