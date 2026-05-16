import time

from core.summary import SummaryAggregator
from core.contracts import FlowRecord


def _flow(src_ip, dst_ip, protocol, dst_port, packets, bytes_count):
    return FlowRecord(
        flow_key=f"{src_ip}:1234->{dst_ip}:{dst_port}|{protocol}",
        start_time=time.time() - 1,
        last_seen=time.time(),
        src_ip=src_ip,
        dst_ip=dst_ip,
        src_port=1234,
        dst_port=dst_port,
        protocol=protocol,
        packet_count=packets,
        byte_count=bytes_count,
        duration=1.0,
        packets_per_second=float(packets),
        bytes_per_second=float(bytes_count),
        is_finalized=True,
        syn_count=1,
        unique_dst_ports={dst_port},
    )


def test_summary_aggregator_rolls_up_finalized_flows():
    aggregator = SummaryAggregator(top_k=5)
    aggregator.update_flow(_flow("10.0.0.1", "10.0.0.2", "TCP", 80, 10, 1000), "outbound")
    aggregator.update_flow(_flow("10.0.0.1", "10.0.0.3", "UDP", 53, 6, 600), "outbound")
    aggregator.update_flow(_flow("10.0.0.4", "10.0.0.2", "TCP", 443, 4, 400), "inbound")

    batch = aggregator.flush()

    assert len(batch.traffic) == 3
    assert any(item.protocol == "TCP" for item in batch.traffic)
    assert any(item.protocol == "UDP" for item in batch.traffic)

    assert len(batch.hosts) <= 5
    assert batch.hosts[0].byte_count >= batch.hosts[-1].byte_count

    assert len(batch.services) == 3
    assert any(item.service == "TCP:80" for item in batch.services)
    assert any(item.service == "UDP:53" for item in batch.services)
    assert any(item.service == "TCP:443" for item in batch.services)


def test_summary_aggregator_resets_after_flush():
    aggregator = SummaryAggregator(top_k=5)
    aggregator.update_flow(_flow("10.0.0.1", "10.0.0.2", "TCP", 80, 10, 1000), "outbound")

    first_batch = aggregator.flush()
    second_batch = aggregator.flush()

    assert len(first_batch.traffic) == 1
    assert len(second_batch.traffic) == 0
    assert len(second_batch.hosts) == 0
    assert len(second_batch.services) == 0
