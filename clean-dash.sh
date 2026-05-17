#!/bin/bash
set -x

echo "--- Forcing Removal of Broken Maintainer Scripts ---"
sudo rm -f /var/lib/dpkg/info/influxdb2.*
sudo rm -f /var/lib/dpkg/info/grafana.*

echo "--- Purging InfluxDB and Grafana ---"
sudo dpkg --remove --force-remove-reinstreq influxdb2 grafana 2>/dev/null || true
sudo apt-get purge -y influxdb2 influxdb2-cli grafana grafana-enterprise 2>/dev/null || true
sudo apt-get autoremove -y
sudo apt-get clean

echo "--- Removing Repositories and Keyrings ---"
sudo rm -f /etc/apt/sources.list.d/influxdata.list
sudo rm -f /etc/apt/sources.list.d/grafana.list
sudo rm -f /etc/apt/keyrings/influxdata-archive.gpg
sudo rm -f /etc/apt/keyrings/grafana.gpg
sudo rm -f /etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg

echo "--- Cleaning Data and Config Directories ---"
sudo rm -rf /var/lib/influxdb /etc/influxdb /var/log/influxdb
sudo rm -rf /var/lib/grafana /etc/grafana /var/log/grafana
sudo rm -f /etc/default/grafana-server /etc/default/influxdb2

echo "--- Cleaning Tepegoz Dash State ---"
sudo rm -f /var/lib/tepegoz-ids/dash-state.json
# Keep sensor.conf but clear the token if it exists
sudo sed -i '/INFLUXDB_TOKEN/d' /etc/tepegoz-ids/sensor.conf 2>/dev/null || true

sudo apt-get update
echo "--- Cleanup Complete ---!"
