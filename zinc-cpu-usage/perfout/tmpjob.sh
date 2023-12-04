#!/bin/bash
sudo /home/user/src/zns-contract-bench/fio/fio --ioengine=io_uring --size=813z --bs=64K --direct=1 --group_reporting --zonemode=zbd --thread=1 --lat_percentiles=1 --filename=/dev/nvme0n2 --sqthread_poll=1 --name=fill-prep --iodepth=1 --rw=write --numjobs=1 --size=813z --name=trim --stonewall --rw=randtrim --iodepth=1 --numjobs=1 --bs=2147483648 --rate=,,62042991939.50 --size=813z 
