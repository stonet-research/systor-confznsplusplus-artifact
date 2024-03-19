COMMON_SCRIPT_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)

# Binaries
# To debug fio
if [[ -z "${DEBUG_FIO}" ]]; then
    FIO="${COMMON_SCRIPT_DIR}/../tools/fio/fio"
else
    FIO="${COMMON_SCRIPT_DIR}/../tools/fio/fio --showcmd"
fi

# Binaries
DBBENCH="${COMMON_SCRIPT_DIR}/../tools/rocksdb/db_bench"
ZENFS="${COMMON_SCRIPT_DIR}/../tools/rocksdb/plugin/zenfs/util/zenfs"
NULLBLK="${COMMON_SCRIPT_DIR}/../util/nullblk_create"

# Common functions
get_device_info() {
    DEV=$1
    export DEV_CHAR=$(echo ${DEV} | sed 's/vme/g/g')
    export DEV_SECT_SIZE=$(cat /sys/block/${DEV}/queue/hw_sector_size)
    export DEV_ZONE_SIZE_BLOCKS=$(cat /sys/block/${DEV}/queue/chunk_sectors)
    export DEV_ZONE_SIZE=$(echo "${DEV_ZONE_SIZE_BLOCKS} * 512" | bc)
    export DEV_ZONES=$(cat /sys/block/${DEV}/queue/nr_zones)  
    export DEV_ZONE_BYTES=$(echo "${DEV_SECT_SIZE} * ${DEV_ZONE_SIZE}" | bc)
    export BS=$(echo "${DEV_SECT_SIZE} * ${DEV_ZONE_SIZE}" | bc)

    echo "#########################################################"
    echo "####################### ZNS  SETUP ######################"
    echo "#########################################################"
    echo "---------------------------------------------------------"
    printf 'DEV: %52s\n' "/dev/${DEV}"
    echo "---------------------------------------------------------"
    printf 'SECTOR_SIZE: %44s\n' "${DEV_SECT_SIZE}"
    echo "---------------------------------------------------------"
    printf 'ZONE_SIZE_BLOCKS: %39s\n' "${DEV_ZONE_SIZE_BLOCKS}"
    echo "---------------------------------------------------------"
    printf 'ZONE_SIZE_BYTES: %40s\n' "${DEV_ZONE_SIZE}"
    echo "---------------------------------------------------------"
    printf 'DEV_ZONES: %46s\n' "${DEV_ZONES}"
    echo "---------------------------------------------------------"
    echo ""
}

quit_if_zinc_not_enabled() {
    if [ $(lsmod | grep -w 'zinc' | wc -l) != 1 ]; then
        echo "Missing ZINC I/O Scheduler Kernel module"
        echo "Follow the Readme Instructions to build and install the ZINC I/O Scheduler".
        exit 1
    fi
}