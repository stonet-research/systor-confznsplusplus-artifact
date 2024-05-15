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
    --bs=512k \
    --loops=48 \
    --lat_percentiles=1 \
    --thread=1 \
    --output-format=json \
    --output=./data/async-repeat-8thread.json \
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
    --loops=15 \
    --bs=8k \
    --numjobs=1 \
    --lat_percentiles=1 \
    --thread=1 \
    --offset_increment=8z \
    --output-format=json \
    --output=./data/async-repeatzone-overwrite.json \
    --group_reporting=1
