get_default_rocksdb_vars() {
    DEV=$1
    export CAP_SECTORS=$(sudo blkzone report -c 5 /dev/${DEV} | grep -oP '(?<=cap )[0-9xa-f]+' | head -1)
    export ZONE_CAP=$((${CAP_SECTORS} * 512))
    export WB_SIZE=$((2 * 1024 * 1024 * 1024))
}

COMMON_SCHEDULER_SCRIPT_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
source ${COMMON_SCHEDULER_SCRIPT_DIR}/../../common.sh
