import glob
import os
import subprocess
from typing import Iterable, Optional, Tuple


def _run_command(command: list[str], shell: bool = False, env: Optional[dict] = None, capture_output: bool = True) -> subprocess.CompletedProcess:
    cmd_str = " ".join(command) if not shell else command[0]
    print(f"[Debug] Executing: {cmd_str}")
    
    # Merge env if provided
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
        
    stdout = subprocess.PIPE if capture_output else None
    stderr = subprocess.PIPE if capture_output else None
        
    result = subprocess.run(command, capture_output=False, stdout=stdout, stderr=stderr, text=True, check=False, shell=shell, env=run_env)
    if result.returncode != 0 and capture_output:
        print(f"[Debug] Command failed with exit code {result.returncode}")
        if result.stdout:
            print(f"[Debug] Stdout: {result.stdout.strip()}")
        if result.stderr:
            print(f"[Debug] Stderr: {result.stderr.strip()}")
    elif result.returncode != 0:
        print(f"[Debug] Command failed with exit code {result.returncode}")
        
    return result


def systemctl_available() -> bool:
    try:
        # Use simple subprocess here to avoid debug spam for version check
        result = subprocess.run(["systemctl", "--version"], capture_output=True, text=True, check=False)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def service_is_active(service_name: str) -> Optional[bool]:
    if not systemctl_available():
        return None

    result = _run_command(["systemctl", "is-active", service_name])
    return result.returncode == 0


def service_start(service_name: str) -> bool:
    if not systemctl_available():
        return False

    result = _run_command(["systemctl", "start", service_name])
    return result.returncode == 0


def service_stop(service_name: str) -> bool:
    if not systemctl_available():
        return False

    result = _run_command(["systemctl", "stop", service_name])
    return result.returncode == 0


def service_restart(service_name: str) -> bool:
    if not systemctl_available():
        return False

    result = _run_command(["systemctl", "restart", service_name])
    return result.returncode == 0


def setup_repositories(packages: Iterable[str]) -> bool:
    pkg_list = list(packages)
    needs_influx = any("influxdb" in p for p in pkg_list)
    needs_grafana = any("grafana" in p for p in pkg_list)

    if not needs_influx and not needs_grafana:
        return True

    print("[Dash] Configuring 3rd-party repositories...")

    # 1. Prerequisites (force non-interactive)
    apt_env = {"DEBIAN_FRONTEND": "noninteractive"}
    res = _run_command(["apt-get", "install", "-y", "apt-transport-https", "wget", "gnupg", "software-properties-common", "curl"], env=apt_env)
    if res.returncode != 0:
        print("[Dash] Failed to install prerequisites")
        return False

    if needs_influx:
        print("[Dash] Adding InfluxData repository...")
        _run_command(["mkdir", "-p", "/etc/apt/keyrings"])
        
        # Use a unique temporary file and enforce non-interactive GPG with --batch --yes
        influx_pipeline = (
            "curl -fsSL https://repos.influxdata.com/influxdata-archive.key > /tmp/influx_key_$$ "
            "&& gpg --show-keys --with-fingerprint --with-colons /tmp/influx_key_$$ 2>&1 "
            "| grep -q '^fpr:\\+24C975CBA61A024EE1B631787C3D57159FC2F927:$' "
            "&& cat /tmp/influx_key_$$ | gpg --dearmor --batch --yes -o /etc/apt/keyrings/influxdata-archive.gpg "
            "&& echo 'deb [signed-by=/etc/apt/keyrings/influxdata-archive.gpg] https://repos.influxdata.com/debian stable main' | tee /etc/apt/sources.list.d/influxdata.list "
            "&& rm -f /tmp/influx_key_$$"
        )
        _run_command([influx_pipeline], shell=True)

    if needs_grafana:
        print("[Dash] Adding Grafana repository...")
        _run_command(["mkdir", "-p", "/etc/apt/keyrings"])
        # Enforce non-interactive GPG with --batch --yes
        _run_command(["sh", "-c", "curl -fsSL https://apt.grafana.com/gpg-full.key | gpg --dearmor --batch --yes -o /etc/apt/keyrings/grafana.gpg"])
        _run_command(["chmod", "644", "/etc/apt/keyrings/grafana.gpg"])
        _run_command(["sh", "-c", 'echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | tee /etc/apt/sources.list.d/grafana.list'])

    return True


def apt_install(packages: Iterable[str]) -> bool:
    package_list = [p for p in packages if p]
    if not package_list:
        return True

    # Setup 3rd party repos if needed (InfluxDB, Grafana)
    if not setup_repositories(package_list):
        return False

    print("[Dash] Updating package lists...")
    apt_env = {"DEBIAN_FRONTEND": "noninteractive"}
    # Capture output for update
    update_result = _run_command(["apt-get", "update"], env=apt_env, capture_output=False)
    if update_result.returncode != 0:
        return False

    print(f"[Dash] Installing packages: {', '.join(package_list)}")
    # Add non-interactive dpkg options and stream output so user sees progress
    install_cmd = [
        "apt-get", "install", "-y",
        "-o", "Dpkg::Options::=--force-confdef",
        "-o", "Dpkg::Options::=--force-confold",
        *package_list
    ]
    install_result = _run_command(install_cmd, env=apt_env, capture_output=False)
    return install_result.returncode == 0


def install_bundled_debs(bundle_dir: str) -> bool:
    debs = sorted(glob.glob(os.path.join(bundle_dir, "*.deb")))
    if not debs:
        return False

    install_result = _run_command(["dpkg", "-i", *debs])
    if install_result.returncode != 0:
        fix_result = _run_command(["apt-get", "-f", "install", "-y"])
        return fix_result.returncode == 0

    return True


def configure_influxdb() -> Optional[str]:
    print("[Dash] Configuring InfluxDB initial setup...")
    # 1. Run initial setup
    setup_res = _run_command([
        "influx", "setup",
        "--bucket", "ids_data",
        "--org", "tepegoz",
        "--username", "admin",
        "--password", "adminadmin",
        "--force"
    ])
    
    # 2. Generate an all-access token
    print("[Dash] Generating InfluxDB access token...")
    token_res = _run_command([
        "influx", "auth", "create",
        "--org", "tepegoz",
        "--all-access",
        "--json"
    ])
    
    if token_res.returncode != 0:
        print("[Dash] Failed to generate InfluxDB token")
        return None
        
    try:
        import json
        data = json.loads(token_res.stdout)
        token = data.get("token")
        if token:
            from tgcli.shared import update_key_value_file, get_sensor_config_path
            update_key_value_file(get_sensor_config_path(), "INFLUXDB_TOKEN", token)
            print("[Dash] InfluxDB token generated and saved to sensor.conf")
            return token
    except Exception as e:
        print(f"[Dash] Error parsing InfluxDB token: {e}")
        
    return None


def configure_grafana(influx_token: str):
    print("[Dash] Provisioning Grafana dashboards and datasources...")
    
    # 1. Inject token into Grafana environment
    grafana_env_path = "/etc/default/grafana-server"
    if os.path.exists(grafana_env_path):
        from tgcli.shared import update_key_value_file
        update_key_value_file(grafana_env_path, "INFLUXDB_TOKEN", influx_token)
    
    # 2. Copy provisioning files
    _run_command(["mkdir", "-p", "/etc/grafana/provisioning/datasources"])
    _run_command(["mkdir", "-p", "/etc/grafana/provisioning/dashboards"])
    _run_command(["mkdir", "-p", "/var/lib/grafana/dashboards"])
    
    # Use shell for globbing copy
    _run_command(["sh", "-c", "cp -r /opt/tepegoz-ids/grafana/provisioning/datasources/* /etc/grafana/provisioning/datasources/"])
    _run_command(["sh", "-c", "cp -r /opt/tepegoz-ids/grafana/provisioning/dashboards/* /etc/grafana/provisioning/dashboards/"])
    _run_command(["sh", "-c", "cp -r /opt/tepegoz-ids/grafana/dashboards/* /var/lib/grafana/dashboards/"])
    
    print("[Dash] Grafana provisioning complete")


def provision_companion_services(
    influx_package: str,
    grafana_package: str,
    offline_bundle_dir: str = "",
) -> Tuple[bool, str]:
    packages = [influx_package, grafana_package, "influxdb2-cli"]
    if apt_install(packages):
        return True, "apt"

    if offline_bundle_dir and install_bundled_debs(offline_bundle_dir):
        return True, "bundled_deb"

    return False, "failed"
