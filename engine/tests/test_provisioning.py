import tgcli.provisioning as provisioning


def test_provision_companion_services_prefers_apt(monkeypatch):
    monkeypatch.setattr(provisioning, "apt_install", lambda _packages: True)
    monkeypatch.setattr(provisioning, "install_bundled_debs", lambda _path: True)

    ok, provider = provisioning.provision_companion_services("influxdb2", "grafana", "/tmp/bundle")

    assert ok is True
    assert provider == "apt"


def test_provision_companion_services_falls_back_to_bundle(monkeypatch):
    monkeypatch.setattr(provisioning, "apt_install", lambda _packages: False)
    monkeypatch.setattr(provisioning, "install_bundled_debs", lambda _path: True)

    ok, provider = provisioning.provision_companion_services("influxdb2", "grafana", "/tmp/bundle")

    assert ok is True
    assert provider == "bundled_deb"


def test_provision_companion_services_reports_failure(monkeypatch):
    monkeypatch.setattr(provisioning, "apt_install", lambda _packages: False)
    monkeypatch.setattr(provisioning, "install_bundled_debs", lambda _path: False)

    ok, provider = provisioning.provision_companion_services("influxdb2", "grafana", "/tmp/bundle")

    assert ok is False
    assert provider == "failed"
