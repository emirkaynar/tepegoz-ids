import os

from tgcli.provisioning import (
    provision_companion_services,
    service_is_active,
    service_start,
    service_stop,
)
from tgcli.shared import get_dash_state_path, read_dash_state, utc_now_iso, write_dash_state


def _default_state():
    now = utc_now_iso()
    return {
        "installed": True,
        "running": True,
        "provider": "apt",
        "offline_fallback": "bundled_deb",
        "created_at": now,
        "updated_at": now,
    }


def handle_dash(args):
    if not args:
        print("Usage: tepegoz dash <setup|on|off|status>")
        return 2

    if hasattr(os, "geteuid") and os.geteuid() != 0:
        print("Error: 'tepegoz dash' commands must be run with sudo.")
        return 1

    subcommand = args[0]
    path = get_dash_state_path()
    state = read_dash_state(path)
    influx_service = os.getenv("TEPEGOZ_INFLUXDB_SERVICE", "influxdb")
    grafana_service = os.getenv("TEPEGOZ_GRAFANA_SERVICE", "grafana-server")

    if subcommand == "setup":
        if state.get("installed"):
            state["updated_at"] = utc_now_iso()
            write_dash_state(path, state)
            print("Dash is already set up; no changes required")
            return 0

        influx_package = os.getenv("TEPEGOZ_INFLUXDB_PACKAGE", "influxdb2")
        grafana_package = os.getenv("TEPEGOZ_GRAFANA_PACKAGE", "grafana")
        offline_bundle_dir = os.getenv("TEPEGOZ_OFFLINE_BUNDLE_DIR", "")

        ok, provider = provision_companion_services(
            influx_package=influx_package,
            grafana_package=grafana_package,
            offline_bundle_dir=offline_bundle_dir,
        )
        if not ok:
            print("Dash setup failed: companion packages could not be installed")
            print("Sensor runtime is unaffected")
            return 1

        # Auto-start services after setup
        service_start(influx_service)
        service_start(grafana_service)
        
        # Configuration pass
        from tgcli.provisioning import configure_influxdb, configure_grafana, service_restart
        token = configure_influxdb()
        if token:
            configure_grafana(token)
            service_restart(grafana_service)
            # Restart sensor to pick up the new token
            service_restart("tepegoz-ids.service")

        new_state = _default_state()
        new_state["provider"] = provider
        new_state["offline_fallback"] = "bundled_deb" if provider == "bundled_deb" else "none"
        write_dash_state(path, new_state)
        print("Dash setup completed. Services started and configured.")
        
        print("You can access the dashboard at http://localhost:3000")
        return 0

    if subcommand == "on":
        if not state.get("installed"):
            print("Dash is not set up. Run: sudo tepegoz dash setup")
            return 2
        start_influx = service_start(influx_service)
        start_grafana = service_start(grafana_service)
        if not (start_influx and start_grafana):
            print("Dash ON failed: unable to start one or more companion services")
            return 1
        state["running"] = True
        state["updated_at"] = utc_now_iso()
        write_dash_state(path, state)
        print("Dash is ON")
        return 0

    if subcommand == "off":
        if not state.get("installed"):
            print("Dash is not set up. Run: sudo tepegoz dash setup")
            return 2
        stop_influx = service_stop(influx_service)
        stop_grafana = service_stop(grafana_service)
        if not (stop_influx and stop_grafana):
            print("Dash OFF failed: unable to stop one or more companion services")
            return 1
        state["running"] = False
        state["updated_at"] = utc_now_iso()
        write_dash_state(path, state)
        print("Dash is OFF")
        return 0

    if subcommand == "status":
        if not state:
            print("Dash state: not-setup")
            return 0

        influx_active = service_is_active(influx_service)
        grafana_active = service_is_active(grafana_service)
        if influx_active is None or grafana_active is None:
            computed_running = state.get("running", False)
        else:
            computed_running = influx_active and grafana_active

        running = "on" if state.get("running") else "off"
        computed = "on" if computed_running else "off"
        print(f"Dash state: setup, {running} (services: {computed})")
        print(f"State file: {path}")
        return 0

    print(f"Unknown dash subcommand: {subcommand}")
    return 2
