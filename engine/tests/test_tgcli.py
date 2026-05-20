import json

import tgcli.dash_cmd as dash_cmd
import tgcli.provisioning as provisioning
import tgcli.sensor_cmd as sensor_cmd
from tgcli.main import run


def test_sensor_iface_set_updates_config(tmp_path, monkeypatch):
    config_file = tmp_path / "sensor.conf"
    monkeypatch.setenv("TEPEGOZ_SENSOR_CONFIG_PATH", str(config_file))
    monkeypatch.setattr(sensor_cmd, "service_restart", lambda _name: False)

    exit_code = run(["sensor", "iface", "set", "eth7"])
    assert exit_code == 0

    content = config_file.read_text(encoding="utf-8")
    assert "IDS_INTERFACE=eth7" in content


def test_sensor_status_prints_service_state(tmp_path, monkeypatch, capsys):
    config_file = tmp_path / "sensor.conf"
    config_file.write_text("IDS_INTERFACE=eth3\n", encoding="utf-8")
    monkeypatch.setenv("TEPEGOZ_SENSOR_CONFIG_PATH", str(config_file))
    monkeypatch.setattr(sensor_cmd, "service_is_active", lambda _name: True)

    exit_code = run(["sensor", "status"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Configured IDS interface: eth3" in output
    assert "Sensor service (tepegoz-ids.service): active" in output


def test_sensor_iface_set_reports_restart_when_successful(tmp_path, monkeypatch, capsys):
    config_file = tmp_path / "sensor.conf"
    monkeypatch.setenv("TEPEGOZ_SENSOR_CONFIG_PATH", str(config_file))
    monkeypatch.setattr(sensor_cmd, "service_restart", lambda _name: True)

    exit_code = run(["sensor", "iface", "set", "eth5"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Restarted service: tepegoz-ids.service" in output


def test_dash_setup_is_idempotent(tmp_path, monkeypatch):
    state_file = tmp_path / "dash-state.json"
    monkeypatch.setenv("TEPEGOZ_DASH_STATE_PATH", str(state_file))
    monkeypatch.setattr(dash_cmd, "provision_companion_services", lambda **_: (True, "apt"))
    monkeypatch.setattr(provisioning, "configure_influxdb", lambda: "dummy-token")
    monkeypatch.setattr(provisioning, "configure_grafana", lambda _t: True)

    first = run(["dash", "setup"])
    second = run(["dash", "setup"])

    assert first == 0
    assert second == 0

    state = json.loads(state_file.read_text(encoding="utf-8"))
    assert state["installed"] is True


def test_dash_on_off_status_flow(tmp_path, monkeypatch, capsys):
    state_file = tmp_path / "dash-state.json"
    monkeypatch.setenv("TEPEGOZ_DASH_STATE_PATH", str(state_file))
    monkeypatch.setattr(dash_cmd, "provision_companion_services", lambda **_: (True, "apt"))
    monkeypatch.setattr(provisioning, "configure_influxdb", lambda: "dummy-token")
    monkeypatch.setattr(provisioning, "configure_grafana", lambda _t: True)
    monkeypatch.setattr(dash_cmd, "service_start", lambda _name: True)
    monkeypatch.setattr(dash_cmd, "service_stop", lambda _name: True)
    monkeypatch.setattr(dash_cmd, "service_is_active", lambda _name: False)

    run(["dash", "setup"])
    run(["dash", "off"])
    run(["dash", "status"])

    output = capsys.readouterr().out
    assert "Dash state: setup, off" in output


def test_dash_setup_provisioning_failure_returns_error(tmp_path, monkeypatch):
    state_file = tmp_path / "dash-state.json"
    monkeypatch.setenv("TEPEGOZ_DASH_STATE_PATH", str(state_file))
    monkeypatch.setattr(dash_cmd, "provision_companion_services", lambda **_: (False, "failed"))

    exit_code = run(["dash", "setup"])

    assert exit_code == 1
    assert not state_file.exists()


def test_dash_on_fails_when_service_start_fails(tmp_path, monkeypatch):
    state_file = tmp_path / "dash-state.json"
    monkeypatch.setenv("TEPEGOZ_DASH_STATE_PATH", str(state_file))
    monkeypatch.setattr(dash_cmd, "provision_companion_services", lambda **_: (True, "apt"))
    monkeypatch.setattr(provisioning, "configure_influxdb", lambda: "dummy-token")
    monkeypatch.setattr(provisioning, "configure_grafana", lambda _t: True)
    monkeypatch.setattr(dash_cmd, "service_start", lambda _name: False)

    run(["dash", "setup"])
    exit_code = run(["dash", "on"])

    assert exit_code == 1


def test_no_args_prints_welcome_banner(capsys):
    """Running tepegoz with no args should print the welcome banner."""
    exit_code = run([])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Tepegoz IDS" in output
    assert "QUICK START" in output
    assert "tepegoz sensor iface set" in output


def test_help_flag_prints_welcome_banner(capsys):
    """Running tepegoz --help should print the welcome banner."""
    exit_code = run(["--help"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Tepegoz IDS" in output
    assert "CONFIGURATION FILES" in output


def test_unknown_command_suggests_help(capsys):
    """Running tepegoz with an unknown command should suggest --help."""
    exit_code = run(["bogus"])

    assert exit_code == 2
    output = capsys.readouterr().out
    assert "--help" in output
