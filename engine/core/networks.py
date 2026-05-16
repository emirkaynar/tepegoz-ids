import ipaddress
import socket
import struct
from typing import Iterable, List


def parse_networks_csv(value: str) -> List[ipaddress._BaseNetwork]:
    """Parse a comma-separated CIDR list into network objects."""
    networks: List[ipaddress._BaseNetwork] = []
    if not value:
        return networks

    for raw in value.split(","):
        cidr = raw.strip()
        if not cidr:
            continue
        try:
            networks.append(ipaddress.ip_network(cidr, strict=False))
        except ValueError:
            # Invalid items are ignored so one bad value does not break startup.
            continue
    return networks


def _hex_le_to_ipv4(hex_value: str) -> str:
    return socket.inet_ntoa(struct.pack("<L", int(hex_value, 16)))


def detect_container_networks_from_route_table(
    route_table_path: str = "/proc/net/route",
    interface_prefixes: Iterable[str] = ("docker", "br-"),
) -> List[ipaddress._BaseNetwork]:
    """Detect bridge/container IPv4 networks from Linux route table."""
    try:
        with open(route_table_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return []

    if not lines:
        return []

    detected: List[ipaddress._BaseNetwork] = []

    for line in lines[1:]:
        fields = line.strip().split()
        if len(fields) < 8:
            continue

        iface = fields[0]
        if not any(iface.startswith(prefix) for prefix in interface_prefixes):
            continue

        destination_hex = fields[1]
        mask_hex = fields[7]

        try:
            destination = _hex_le_to_ipv4(destination_hex)
            mask = _hex_le_to_ipv4(mask_hex)
            if mask == "0.0.0.0":
                continue
            detected.append(ipaddress.ip_network(f"{destination}/{mask}", strict=False))
        except (ValueError, OSError):
            continue

    return merge_unique_networks(detected)


def merge_unique_networks(*groups: Iterable[ipaddress._BaseNetwork]) -> List[ipaddress._BaseNetwork]:
    """Merge multiple network iterables and deduplicate while preserving sort order."""
    by_key = {}
    for group in groups:
        for network in group:
            by_key[str(network)] = network
    return sorted(by_key.values(), key=lambda n: (n.version, int(n.network_address), n.prefixlen))


def resolve_excluded_networks(explicit_csv: str, auto_detect_container_nets: bool = True) -> List[ipaddress._BaseNetwork]:
    """Resolve excluded networks from explicit env config and optional auto-detection."""
    explicit = parse_networks_csv(explicit_csv)
    if not auto_detect_container_nets:
        return merge_unique_networks(explicit)
    detected = detect_container_networks_from_route_table()
    return merge_unique_networks(explicit, detected)


def ip_in_any_network(ip_value: str, networks: Iterable[ipaddress._BaseNetwork]) -> bool:
    try:
        address = ipaddress.ip_address(ip_value)
    except ValueError:
        return False
    return any(address in network for network in networks)
