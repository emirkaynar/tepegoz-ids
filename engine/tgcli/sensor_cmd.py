import os

from core.settings import parse_key_value_file
from tgcli.provisioning import service_is_active, service_restart
from tgcli.shared import get_sensor_config_path, update_key_value_file


def handle_sensor(args):
    if not args:
        print("Usage: tepegoz sensor <iface|status> ...")
        return 2

    subcommand = args[0]

    if subcommand == "iface":
        if len(args) != 3 or args[1] != "set":
            print("Usage: tepegoz sensor iface set <name>")
            return 2

        iface_name = args[2].strip()
        if not iface_name:
            print("Interface name cannot be empty")
            return 2

        config_path = get_sensor_config_path()
        update_key_value_file(config_path, "IDS_INTERFACE", iface_name)
        service_name = os.getenv("TEPEGOZ_SENSOR_SERVICE", "tepegoz-ids.service")
        restarted = service_restart(service_name)
        print(f"Updated IDS_INTERFACE={iface_name} in {config_path}")
        if restarted:
            print(f"Restarted service: {service_name}")
        else:
            print(f"Restart sensor service to apply: sudo systemctl restart {service_name}")
        return 0

    if subcommand == "status":
        config_path = get_sensor_config_path()
        config = parse_key_value_file(config_path)
        interface = config.get("IDS_INTERFACE", "eth0")
        service_name = os.getenv("TEPEGOZ_SENSOR_SERVICE", "tepegoz-ids.service")
        service_active = service_is_active(service_name)
        service_text = "unknown"
        if service_active is True:
            service_text = "active"
        elif service_active is False:
            service_text = "inactive"
        print(f"Sensor config path: {config_path}")
        print(f"Configured IDS interface: {interface}")
        print(f"Sensor service ({service_name}): {service_text}")
        return 0

    print(f"Unknown sensor subcommand: {subcommand}")
    return 2
