COMMON_SCRIPT_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)

# Binaries
# To debug fio
if [[ -z "${DEBUG_FIO}" ]]; then
    FIO="${COMMON_SCRIPT_DIR}/../../../../tools/fio/fio"
else
    FIO="${COMMON_SCRIPT_DIR}/../../../../tools/fio/fio --showcmd"
fi

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

baseline_finish() {
    DEV_CHAR=$1
    FILL_SIZE=$2
    echo "Benchmarking ZNS Device Finish baseline Limit"
    sudo nvme zns reset-zone /dev/${DEV_CHAR} -a > /dev/null
    sudo env "DEV=${DEV_CHAR}" "FINISH_SIZE=${FILL_SIZE}" ${FIO} \
        --output-format=json \
        --output=data/bw.json \
        ${COMMON_SCRIPT_DIR}/common-jobs/job-finish-baseline.fio
    if [[ -z "${DEBUG_FIO}" ]]; then
        export FINISH_BW=$(cat data/bw.json | grep -i "bw_bytes" | awk 'FNR == 2 {print $3}' | sed 's/,//g')
    else
        export FINISH_BW=100
    fi
    echo "Found Sustainable BW for Finish: ${FINISH_BW} B/sec"    
}

baseline_reset() {
    DEV_CHAR=$1
    FILL_SIZE=$2
    CONCUR_FILL=4 # concurrent fill jobs to speedup filling
    CONCUR_FILL_SIZE=$(echo "scale=0; ${FILL_SIZE} / ${CONCUR_FILL}" | bc)

    echo "Benchmarking ZNS Device Reset baseline Limit"
    sudo nvme zns reset-zone /dev/${DEV_CHAR} -a
    sudo env "DEV=${DEV_CHAR}" "BS=${DEV_ZONE_SIZE}" \
        "CONCUR_FILL_SIZE=${CONCUR_FILL_SIZE}" "CONCUR_FILL=${CONCUR_FILL}" \
        "FILL_SIZE=${DEV_ZONES}" "TRIM_IODEPTH=1" ${FIO} \
            --output-format=json \
            --output=data/bw.json \
        ${COMMON_SCRIPT_DIR}/common-jobs/job-reset-baseline.fio
    if [[ -z "${DEBUG_FIO}" ]]; then
        export RESET_BW=$(cat data/bw.json | grep -i "bw_bytes" | awk 'FNR == 6 {print $3}' | sed 's/,//g')
    else
        export RESET_BW=100
    fi
    echo "Found Sustainable BW for Reset: ${RESET_BW} B/sec" 
}

baseline_append() {
    DEV_CHAR=$1
    APPEND_SIZE=$2
    echo "Benchmarking ZNS Device Append Rate Limit"
    sudo nvme zns reset-zone /dev/${DEV_CHAR} -a
    sudo env "DEV=${DEV_CHAR}" "APPEND_SIZE=${APPEND_SIZE}" ${FIO} \
        --output-format=json \
        --output=data/bw.json \
        ${COMMON_SCRIPT_DIR}/common-jobs/job-append-baseline.fio
    if [[ -z "${DEBUG_FIO}" ]]; then
        export APPEND_BW=$(cat data/bw.json | grep -i "bw_bytes" | awk 'FNR == 2 {print $3}' | sed 's/,//g')
    else
        export APPEND_BW=100
    fi
    echo "Found Sustainable BW for Append Rate Limiting: ${APPEND_BW} B/sec"  
}

baseline_read() {
    DEV_CHAR=$1
    READ_SIZE=$2
    echo "Benchmarking ZNS Device Read Rate Limit"
    sudo nvme zns reset-zone /dev/${DEV_CHAR} -a
    sudo env "DEV=${DEV_CHAR}" "WRITE_ZONES=${READ_SIZE}" ${FIO} \
        --output-format=json \
        --output=data/bw.json \
        ${COMMON_SCRIPT_DIR}/common-jobs/job-read-baseline.fio
    if [[ -z "${DEBUG_FIO}" ]]; then
        export READ_BW=$(cat data/bw.json | grep -i "bw_bytes" | awk 'FNR == 2 {print $3}' | sed 's/,//g')
    else
        export READ_BW=100
    fi
    echo "Found Sustainable BW for Read Rate Limiting: ${READ_BW} B/sec"  
}

baseline_write() {
    DEV_CHAR=$1
    WRITE_SIZE=$2
    echo "Benchmarking ZNS Device Write Rate Limit"
    sudo nvme zns reset-zone /dev/${DEV_CHAR} -a
    sudo env "DEV=${DEV_CHAR}" "WRITE_ZONES=${WRITE_SIZE}" ${FIO} \
        --output-format=json \
        --output=data/bw.json \
        ${COMMON_SCRIPT_DIR}/common-jobs/job-write-baseline.fio
    if [[ -z "${DEBUG_FIO}" ]]; then    
        export WRITE_BW=$(cat data/bw.json | grep -i "bw_bytes" | awk 'FNR == 2 {print $3}' | sed 's/,//g')
    else
        export WRITE_BW=100
    fi
    echo "Found Sustainable BW for Write Rate Limiting: ${WRITE_BW} B/sec" 
}