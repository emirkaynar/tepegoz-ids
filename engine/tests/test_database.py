import time

from core import database as database_module
from core.contracts import AlertRecord, FlowRecord
from influxdb_client.client.write_api import SYNCHRONOUS, WriteOptions


class FakeWriteAPI:
    def __init__(self):
        self.calls = []
        self.should_fail = False
        self.closed = False

    def write(self, bucket, org, record):
        if self.should_fail:
            raise RuntimeError("simulated write failure")
        self.calls.append((bucket, org, record))

    def close(self):
        self.closed = True


class FakeInfluxDBClient:
    last_instance = None

    def __init__(self, url, token, org):
        self.url = url
        self.token = token
        self.org = org
        self.write_api_calls = []
        self.closed = False
        FakeInfluxDBClient.last_instance = self

    def write_api(self, write_options):
        api = FakeWriteAPI()
        self.write_api_calls.append((write_options, api))
        return api

    def close(self):
        self.closed = True


class InitFailingInfluxDBClient:
    def __init__(self, url, token, org):
        raise RuntimeError("client init failed")


def _sample_flow():
    return FlowRecord(
        flow_key="10.0.0.1:1234->10.0.0.2:80|TCP",
        start_time=time.time() - 1,
        last_seen=time.time(),
        src_ip="10.0.0.1",
        dst_ip="10.0.0.2",
        src_port=1234,
        dst_port=80,
        protocol="TCP",
        packet_count=10,
        byte_count=1000,
        duration=1.0,
        packets_per_second=10.0,
        bytes_per_second=1000.0,
        is_finalized=True,
        syn_count=3,
        unique_dst_ports={80},
    )


def _sample_alert():
    return AlertRecord(
        timestamp=time.time(),
        rule_name="DoS SYN Flood",
        severity="Critical",
        src_ip="10.0.0.1",
        dst_ip="10.0.0.2",
        description="SYN ratio exceeded threshold",
        flow_key="10.0.0.1:1234->10.0.0.2:80|TCP",
        direction="unknown",
    )


def test_database_manager_creates_batched_and_immediate_writers(monkeypatch):
    monkeypatch.setenv("INFLUXDB_TOKEN", "token")
    monkeypatch.setattr(database_module, "InfluxDBClient", FakeInfluxDBClient)

    manager = database_module.DatabaseManager()
    calls = FakeInfluxDBClient.last_instance.write_api_calls

    assert len(calls) == 2
    assert isinstance(calls[0][0], WriteOptions)
    assert calls[1][0] == SYNCHRONOUS
    assert manager.metrics_write_api is calls[0][1]
    assert manager.alerts_write_api is calls[1][1]


def test_record_flow_and_alert_use_separate_writers(monkeypatch):
    monkeypatch.setenv("INFLUXDB_TOKEN", "token")
    monkeypatch.setattr(database_module, "InfluxDBClient", FakeInfluxDBClient)

    manager = database_module.DatabaseManager()
    flow = _sample_flow()
    alert = _sample_alert()

    manager.record_flow(flow)
    manager.record_alert(alert)

    metrics_api = manager.metrics_write_api
    alerts_api = manager.alerts_write_api

    assert len(metrics_api.calls) == 1
    assert len(alerts_api.calls) == 1

    flow_record = metrics_api.calls[0][2]
    alert_record = alerts_api.calls[0][2]

    assert "net_flow" in flow_record.to_line_protocol()
    assert "alerts" in alert_record.to_line_protocol()


def test_missing_token_disables_writes_without_crashing(monkeypatch):
    monkeypatch.delenv("INFLUXDB_TOKEN", raising=False)
    monkeypatch.setattr(database_module, "InfluxDBClient", FakeInfluxDBClient)

    manager = database_module.DatabaseManager()

    assert manager.client is None
    assert manager.metrics_write_api is None
    assert manager.alerts_write_api is None

    manager.record_flow(_sample_flow())
    manager.record_alert(_sample_alert())
    manager.close()


def test_failed_writes_increment_counters(monkeypatch):
    monkeypatch.setenv("INFLUXDB_TOKEN", "token")
    monkeypatch.setattr(database_module, "InfluxDBClient", FakeInfluxDBClient)

    manager = database_module.DatabaseManager()
    manager.metrics_write_api.should_fail = True
    manager.alerts_write_api.should_fail = True

    manager.record_flow(_sample_flow())
    manager.record_alert(_sample_alert())

    assert manager.failed_flow_writes == 1
    assert manager.failed_alert_writes == 1


def test_client_init_failure_keeps_manager_safe(monkeypatch):
    monkeypatch.setenv("INFLUXDB_TOKEN", "token")
    monkeypatch.setattr(database_module, "InfluxDBClient", InitFailingInfluxDBClient)

    manager = database_module.DatabaseManager()

    assert manager.client is None
    assert manager.metrics_write_api is None
    assert manager.alerts_write_api is None

    manager.record_flow(_sample_flow())
    manager.record_alert(_sample_alert())
    manager.close()


def test_close_shuts_down_both_writers_and_client(monkeypatch):
    monkeypatch.setenv("INFLUXDB_TOKEN", "token")
    monkeypatch.setattr(database_module, "InfluxDBClient", FakeInfluxDBClient)

    manager = database_module.DatabaseManager()
    client = manager.client
    metrics_api = manager.metrics_write_api
    alerts_api = manager.alerts_write_api

    manager.close()

    assert metrics_api.closed
    assert alerts_api.closed
    assert client.closed
