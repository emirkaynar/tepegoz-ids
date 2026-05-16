from core.networks import (
    parse_networks_csv,
    detect_container_networks_from_route_table,
    resolve_excluded_networks,
    ip_in_any_network,
)


def test_parse_networks_csv_ignores_invalid_items():
    networks = parse_networks_csv("172.17.0.0/16, invalid, 192.168.65.0/24")
    assert [str(n) for n in networks] == ["172.17.0.0/16", "192.168.65.0/24"]


def test_detect_container_networks_from_route_table(tmp_path):
    route_file = tmp_path / "route"
    route_file.write_text(
        "Iface\tDestination\tGateway\tFlags\tRefCnt\tUse\tMetric\tMask\tMTU\tWindow\tIRTT\n"
        "eth0\t00000000\t010011AC\t0003\t0\t0\t0\t00000000\t0\t0\t0\n"
        "docker0\t000011AC\t00000000\t0001\t0\t0\t0\t0000FFFF\t0\t0\t0\n"
        "br-abcd\t0012A8C0\t00000000\t0001\t0\t0\t0\t00FFFFFF\t0\t0\t0\n",
        encoding="utf-8",
    )

    networks = detect_container_networks_from_route_table(str(route_file))
    assert [str(n) for n in networks] == ["172.17.0.0/16", "192.168.18.0/24"]


def test_resolve_excluded_networks_merges_detected_and_explicit(monkeypatch):
    monkeypatch.setattr(
        "core.networks.detect_container_networks_from_route_table",
        lambda: parse_networks_csv("172.17.0.0/16,192.168.65.0/24"),
    )

    merged = resolve_excluded_networks("172.17.0.0/16,10.10.0.0/16", auto_detect_container_nets=True)
    assert [str(n) for n in merged] == ["10.10.0.0/16", "172.17.0.0/16", "192.168.65.0/24"]


def test_ip_in_any_network_returns_expected_membership():
    networks = parse_networks_csv("10.0.0.0/8,172.17.0.0/16")
    assert ip_in_any_network("172.17.5.10", networks)
    assert not ip_in_any_network("8.8.8.8", networks)
