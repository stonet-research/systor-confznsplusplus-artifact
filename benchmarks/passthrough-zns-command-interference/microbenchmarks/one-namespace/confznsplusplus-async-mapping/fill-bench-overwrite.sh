#!/bin/bash

set -e

SCRIPT_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
cd ${SCRIPT_DIR}
source ../common.sh

sudo ${FIO} \
    --zonemode=zbd \
    --ioengine=io_uring_cmd \
    --direct=0 \
    --sqthread_poll=1 \
    --filename=/dev/ng0n1 \
    --name=fill \
    --rw=write \
    --size=48z \
    --bs=256k \
    --numjobs=1 \
    --lat_percentiles=1 \
    --thread=1 \
    --offset_increment=1z \
    --output-format=json \
    --output=./data/sync-fill-256kthread.json \
    --group_reporting=1

sudo ${FIO} \
    --zonemode=zbd \
    --ioengine=io_uring_cmd \
    --direct=0 \
    --sqthread_poll=1 \
    --filename=/dev/ng0n1 \
    --name=fill \
    --rw=write \
    --size=15z \
    --bs=16k \
    --numjobs=1 \
    --lat_percentiles=1 \
    --thread=1 \
    --offset_increment=8z \
    --output-format=json \
    --output=./data/async-seqfill-overwrite.json \
    --group_reporting=1 \
    --write_lat_log=./data/sync-seqfill-overwrite-log
