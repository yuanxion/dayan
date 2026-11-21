#!/usr/bin/env bash
set -euo pipefail

export no_proxy=127.0.0.1,intel.com,.intel.com,10.0.0.0/8,192.168.0.0/16,localhost,.local,127.0.0.0/8,134.134.0.0/16

install_dir="${ONEAPI_INSTALL_DIR:-$HOME/yuanx/tools/oneapi}"
download_dir="$HOME/yuanx/tools/downloads"
installer="intel-oneapi-toolkit-2026.2.0.667_offline.sh"
url="https://registrationcenter-download.intel.com/akdlm/IRC_NAS/902d3dfc-ece4-4282-9a4a-48020ca454e6/$installer"

mkdir -p "$download_dir" "$install_dir"
wget -c -O "$download_dir/$installer" "$url"
sh "$download_dir/$installer" -a --silent --cli --eula accept --install-dir "$install_dir"

