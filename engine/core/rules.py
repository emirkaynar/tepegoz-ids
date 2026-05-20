import yaml
import time
import threading
from collections import defaultdict
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


def parse_ports_csv(value: str) -> set:
    """
    Parse a comma-separated list of ports and port ranges (e.g. '80,8000-8080,32768-60999')
    into a set of integers.
    """
    ports = set()
    if not value:
        return ports
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            try:
                start_str, end_str = part.split("-", 1)
                start = int(start_str.strip())
                end = int(end_str.strip())
                start = max(1, min(start, 65535))
                end = max(1, min(end, 65535))
                if start <= end:
                    ports.update(range(start, end + 1))
            except ValueError:
                continue
        else:
            try:
                port = int(part)
                if 1 <= port <= 65535:
                    ports.add(port)
            except ValueError:
                continue
    return ports


class SourceTracker:
    """
    Lightweight cross-flow accumulator that tracks per-source-IP
    statistics over a sliding time window.

    This solves the fundamental issue where attacks spread across many
    micro-flows (random source ports in SYN floods, different dest ports
    in port scans) that individually look benign but collectively are
    malicious.
    """

    def __init__(self, window_seconds: float = 30.0, exclude_ports: set = None):
        self._window = window_seconds
        self._lock = threading.Lock()
        self.exclude_ports = exclude_ports or set()
        # Per source IP: list of (timestamp, dst_port, syn_count, packet_count, byte_count, dst_ip, protocol)
        self._entries: Dict[str, list] = defaultdict(list)

    def record(self, flow: FlowRecord):
        """Record a finalized flow's stats for its source IP."""
        entry = (
            flow.last_seen,
            flow.dst_port,
            flow.syn_count,
            flow.packet_count,
            flow.byte_count,
            flow.dst_ip,
            flow.protocol,
        )
        with self._lock:
            self._entries[flow.src_ip].append(entry)

    def get_stats(self, src_ip: str) -> Dict[str, Any]:
        """
        Return aggregated stats for a source IP within the time window.
        Prunes expired entries as a side effect.
        """
        cutoff = time.time() - self._window
        with self._lock:
            entries = self._entries.get(src_ip, [])
            # Prune expired
            active = [e for e in entries if e[0] >= cutoff]
            self._entries[src_ip] = active

        if not active:
            return {
                "cross_unique_dst_ports": 0,
                "cross_total_syn": 0,
                "cross_total_packets": 0,
                "cross_total_bytes": 0,
                "cross_flow_count": 0,
                "cross_unique_dst_ips": 0,
                "cross_pps": 0.0,
                "cross_bps": 0.0,
                "cross_syn_ratio": 0.0,
            }

        unique_ports = set()
        unique_dst_ips = set()
        total_syn = 0
        total_packets = 0
        total_bytes = 0

        for _, dst_port, syn_count, pkt_count, byte_count, dst_ip, protocol in active:
            if dst_port is not None and dst_port not in self.exclude_ports:
                # For TCP, only count ports where connection was initiated (syn_count > 0).
                # This filters out server responses to client ephemeral ports.
                if protocol != "TCP" or syn_count > 0:
                    unique_ports.add(dst_port)
            unique_dst_ips.add(dst_ip)
            total_syn += syn_count
            total_packets += pkt_count
            total_bytes += byte_count

        elapsed = active[-1][0] - active[0][0]
        elapsed = max(elapsed, 1.0)  # avoid division by zero
        
        return {
            "cross_unique_dst_ports": len(unique_ports),
            "cross_total_syn": total_syn,
            "cross_total_packets": total_packets,
            "cross_total_bytes": total_bytes,
            "cross_flow_count": len(active),
            "cross_unique_dst_ips": len(unique_dst_ips),
            "cross_pps": total_packets / elapsed,
            "cross_bps": total_bytes / elapsed,
            "cross_syn_ratio": total_syn / max(total_packets, 1),
        }

    def cleanup(self):
        """Remove all expired entries across all IPs."""
        cutoff = time.time() - self._window
        with self._lock:
            empty_keys = []
            for ip, entries in self._entries.items():
                self._entries[ip] = [e for e in entries if e[0] >= cutoff]
                if not self._entries[ip]:
                    empty_keys.append(ip)
            for ip in empty_keys:
                del self._entries[ip]


class RuleEngine:
    """
    Schema-driven detection engine that evaluates FlowRecords against
    declarative YAML conditions.

    Each rule defines a list of {field, op, value} conditions and a
    logic mode ('all' or 'any').  Virtual fields (avg_packet_size,
    syn_ratio, unique_dst_ports_count, direction) are computed on demand
    from the FlowRecord without requiring upstream changes.

    Cross-flow fields (cross_unique_dst_ports, cross_total_syn, etc.)
    are provided by the SourceTracker for detecting attacks that spread
    across many micro-flows.
    """

    def __init__(self, config_path: str, cooldown_seconds: float = 30.0, exclude_ports: set = None):
        self.config_path = config_path
        self.rules: List[Dict[str, Any]] = []
        self.source_tracker = SourceTracker(window_seconds=30.0, exclude_ports=exclude_ports)
        self._cooldown_seconds = cooldown_seconds
        # (rule_name, src_ip) -> last_alert_timestamp
        self._alert_cooldowns: Dict[tuple, float] = {}
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
    def _build_context(flow: FlowRecord, direction: str,
                       cross_stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a flat dict of all fields available for condition evaluation.
        Includes raw FlowRecord attributes, computed virtuals, and
        cross-flow aggregates from the SourceTracker.
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
            # Per-flow computed virtual fields
            "avg_packet_size": flow.byte_count / pkt,
            "syn_ratio": flow.syn_count / pkt,
            "unique_dst_ports_count": len(flow.unique_dst_ports),
            "direction": direction,
        }
        # Merge cross-flow stats
        ctx.update(cross_stats)
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
        Records the flow into the cross-flow tracker and merges
        cross-flow stats into the evaluation context.
        """
        # Record this flow for cross-flow correlation
        self.source_tracker.record(flow)

        # Build unified evaluation context
        cross_stats = self.source_tracker.get_stats(flow.src_ip)
        ctx = self._build_context(flow, direction, cross_stats)
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
                rule_name = rule.get('name', 'Unknown')
                now = time.time()

                # Build description from template with context values
                desc_template = rule.get('description', '')
                try:
                    reason = desc_template.format(**ctx)
                except (KeyError, ValueError, IndexError):
                    reason = desc_template

                alert = AlertRecord(
                    timestamp=now,
                    rule_name=rule_name,
                    severity=rule.get('severity', 'Medium'),
                    src_ip=flow.src_ip,
                    dst_ip=flow.dst_ip,
                    description=reason,
                    flow_key=flow.flow_key,
                    direction=direction
                )
                alerts.append(alert)

        return alerts
