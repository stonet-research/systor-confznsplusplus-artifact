#!/bin/bash

sudo ~/src/test/zincgit/tools/fio/fio \
    --zonemode=zbd \
    --ioengine=io_uring_cmd \
    --direct=0 \
    --sqthread_poll=1 \
    --filename=/dev/ng1n1 \
    --name=fill \
    --rw=write \
    --size=1z \
    --loops=8 \
    --bs=8k \
    --numjobs=6 \
    --lat_percentiles=1 \
    --thread=1 \
    --offset_increment=8z \
    --output-format=json \
    --output=./data/sync-repeat.json \
    --group_reporting=1

sudo ~/src/test/zincgit/tools/fio/fio \
    --zonemode=zbd \
    --ioengine=io_uring_cmd \
    --direct=0 \
    --sqthread_poll=1 \
    --filename=/dev/ng1n1 \
    --name=fill \
    --rw=write \
    --size=1z \
    --loops=8 \
    --bs=8k \
    --numjobs=6 \
    --lat_percentiles=1 \
    --thread=1 \
    --offset_increment=8z \
    --output-format=json \
    --output=./data/sync-repeat-second.json \
    --group_reporting=1