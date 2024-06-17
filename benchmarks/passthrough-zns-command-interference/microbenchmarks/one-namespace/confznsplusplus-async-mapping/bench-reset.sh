#! /bin/bash

set -e

SCRIPT_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
cd ${SCRIPT_DIR}
source ../common.sh

if [ $# != 1 ]; then
    echo "Usage: $0 <ZNS device (e.g., nvme0n2)>"
    exit 1
fi
DEV=$1

# Device info
get_device_info ${DEV}
baseline_reset ${DEV_CHAR} 20
mv data/bw.json data/reset-sync.json