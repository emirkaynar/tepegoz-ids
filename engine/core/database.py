import os
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS, WriteOptions
from .contracts import FlowRecord, AlertRecord

class DatabaseManager:
    """
    Manages persistence of flow metrics and security alerts to InfluxDB.
    Implements batched writes for performance (ADR-005).
    """
    def __init__(self):
        self.url = os.getenv("INFLUXDB_URL", "http://localhost:8086")
        self.token = os.getenv("INFLUXDB_TOKEN")
        self.org = os.getenv("INFLUXDB_ORG", "tepegoz")
        self.bucket = os.getenv("INFLUXDB_BUCKET", "ids_data")
        self.metrics_batch_size = int(os.getenv("INFLUXDB_BATCH_SIZE", "500"))
        self.metrics_flush_interval_ms = int(os.getenv("INFLUXDB_FLUSH_INTERVAL_MS", "1000"))
        self.failed_flow_writes = 0
        self.failed_alert_writes = 0
        self.metrics_write_api = None
        self.alerts_write_api = None
        self.client = None
        
        if not self.token:
            print("[DatabaseManager] WARNING: INFLUXDB_TOKEN not set. Persistence will fail.")
            return

        try:
            self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
            # Metrics are buffered in batches to reduce I/O overhead.
            self.metrics_write_api = self.client.write_api(
                write_options=WriteOptions(
                    batch_size=self.metrics_batch_size,
                    flush_interval=self.metrics_flush_interval_ms,
                )
            )
            # Alerts are written immediately for low-latency operational visibility.
            self.alerts_write_api = self.client.write_api(write_options=SYNCHRONOUS)
            print(f"[DatabaseManager] Initialized for bucket: {self.bucket}")
        except Exception as e:
            print(f"[DatabaseManager] Critical Error initializing client: {e}")
            self.metrics_write_api = None
            self.alerts_write_api = None

    def record_flow(self, flow: FlowRecord):
        """
        Writes a flow summary as a metric to InfluxDB.
        """
        if not self.metrics_write_api:
            return

        point = Point("net_flow") \
            .tag("flow_key", flow.flow_key) \
            .tag("protocol", flow.protocol) \
            .field("packets", flow.packet_count) \
            .field("bytes", flow.byte_count) \
            .field("duration", flow.duration) \
            .field("pps", flow.packets_per_second) \
            .field("bps", flow.bytes_per_second) \
            .time(int(flow.last_seen * 1e9), WritePrecision.NS)

        try:
            self.metrics_write_api.write(bucket=self.bucket, org=self.org, record=point)
        except Exception as exc:
            self.failed_flow_writes += 1
            if self.failed_flow_writes == 1 or self.failed_flow_writes % 100 == 0:
                print(f"[DatabaseManager] Flow metric write failed ({self.failed_flow_writes}): {exc}")

    def record_alert(self, alert: AlertRecord):
        """
        Writes a security alert to InfluxDB.
        """
        if not self.alerts_write_api:
            return

        point = Point("alerts") \
            .tag("rule_name", alert.rule_name) \
            .tag("severity", alert.severity) \
            .tag("src_ip", alert.src_ip) \
            .tag("dst_ip", alert.dst_ip) \
            .field("description", alert.description) \
            .field("flow_key", alert.flow_key) \
            .time(int(alert.timestamp * 1e9), WritePrecision.NS)

        try:
            self.alerts_write_api.write(bucket=self.bucket, org=self.org, record=point)
        except Exception as exc:
            self.failed_alert_writes += 1
            if self.failed_alert_writes == 1 or self.failed_alert_writes % 100 == 0:
                print(f"[DatabaseManager] Alert write failed ({self.failed_alert_writes}): {exc}")

    def close(self):
        """
        Flushes all buffers and closes the client connection.
        """
        if not self.client:
            return

        print("[DatabaseManager] Flushing buffers and closing connection...")
        try:
            if self.metrics_write_api:
                self.metrics_write_api.close()
        except Exception as exc:
            print(f"[DatabaseManager] Error while closing metrics writer: {exc}")
        try:
            if self.alerts_write_api:
                self.alerts_write_api.close()
        except Exception as exc:
            print(f"[DatabaseManager] Error while closing alerts writer: {exc}")
        try:
            self.client.close()
        except Exception as exc:
            print(f"[DatabaseManager] Error while closing client: {exc}")
