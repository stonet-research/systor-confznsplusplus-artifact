#!/bin/bash

sudo ~/src/test/zincgit/tools/fio/fio \
    --zonemode=zbd \
    --ioengine=io_uring_cmd \
    --direct=0 \
    --sqthread_poll=1 \
    --filename=/dev/ng0n1 \
    --name=fill \
    --rw=write \
    --size=8z \
    --bs=8k \
    --numjobs=6 \
    --lat_percentiles=1 \
    --thread=1 \
    --offset_increment=8z \
    --output-format=json \
    --output=./data/sync-fill.json \
    --group_reporting=1

sudo ~/src/test/zincgit/tools/fio/fio \
    --zonemode=zbd \
    --ioengine=io_uring_cmd \
    --direct=0 \
    --sqthread_poll=1 \
    --filename=/dev/ng0n1 \
    --name=fill \
    --rw=write \
    --size=8z \
    --bs=8k \
    --numjobs=6 \
    --lat_percentiles=1 \
    --thread=1 \
    --offset_increment=8z \
    --output-format=json \
    --output=./data/sync-fill-second.json \
    --group_reporting=1