#!/bin/bash


DEV=nvme0n2
DEV_SECT_SIZE=$(cat /sys/block/$DEV/queue/hw_sector_size)
DEV_ZONE_SIZE_BLOCKS=$(cat /sys/block/$DEV/queue/chunk_sectors)
DEV_ZONE_SIZE=$(echo "${DEV_ZONE_SIZE_BLOCKS} * 512" | bc)
DEV_ZONES=$(cat /sys/block/$DEV/queue/nr_zones)
DEV_ZONES=10

BLUE='\033[1;34m'
CLOSE='\033[0m'
RED='\033[1;31m'
GREEN=$'\033[1;32m'

FILL_SIZE=$(echo "scale=0; ${DEV_ZONES} * 0.9" | bc | sed 's/\.[0-9]*//g')
BW=$(cat data/bw.json | grep -i "bw_bytes" | awk 'FNR == 6 {print $3}' | sed 's/,//g')
trim_rate_limit=$(echo "scale=2; 50 / 100  * ${BW}" | bc) 

sudo env "DEV=$DEV" "BS=${DEV_ZONE_SIZE}" "FILL_SIZE=${FILL_SIZE}" "RESET_LIMIT=${trim_rate_limit}" ../fio/fio --output-format=json --output=data-reset_baseline-rflow-50.json job-reset-baseline.fio
