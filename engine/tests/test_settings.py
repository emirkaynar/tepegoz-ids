from core.settings import get_bool_setting, get_setting


def test_get_setting_uses_config_then_default(tmp_path, monkeypatch):
    config_file = tmp_path / "sensor.conf"
    config_file.write_text("IDS_INTERFACE=eth9\n", encoding="utf-8")

    monkeypatch.delenv("IDS_INTERFACE", raising=False)
    value = get_setting("IDS_INTERFACE", "eth0", str(config_file))
    assert value == "eth9"

    fallback = get_setting("NOT_SET", "default-value", str(config_file))
    assert fallback == "default-value"


def test_get_setting_env_overrides_config(tmp_path, monkeypatch):
    config_file = tmp_path / "sensor.conf"
    config_file.write_text("IDS_INTERFACE=eth9\n", encoding="utf-8")

    monkeypatch.setenv("IDS_INTERFACE", "eth10")
    value = get_setting("IDS_INTERFACE", "eth0", str(config_file))
    assert value == "eth10"


def test_get_bool_setting_parses_common_true_values(tmp_path, monkeypatch):
    config_file = tmp_path / "sensor.conf"
    config_file.write_text("SUPPRESS_EXCLUDED_INTERNAL=yes\n", encoding="utf-8")

    monkeypatch.delenv("SUPPRESS_EXCLUDED_INTERNAL", raising=False)
    assert get_bool_setting("SUPPRESS_EXCLUDED_INTERNAL", False, str(config_file))

    monkeypatch.setenv("SUPPRESS_EXCLUDED_INTERNAL", "off")
    assert not get_bool_setting("SUPPRESS_EXCLUDED_INTERNAL", True, str(config_file))
