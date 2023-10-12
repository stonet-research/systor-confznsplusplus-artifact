#!/bin/bash

sudo LD_LIBRARY_PATH="/home/user/src/WALTZ/plugin/spdk/build/lib/:/home/user/src/WALTZ/plugin/spdk/dpdk/build/lib/" ./db_bench --benchmarks=enablewaltzmode,fillrandom --waltz_pcie_addr=0000:00:06.0 --fs_uri=zenfs://dev:ultra #--waltz_test_type=0

sudo LD_LIBRARY_PATH="/home/user/src/WALTZ/plugin/spdk/build/lib/:/home/user/src/WALTZ/plugin/spdk/dpdk/build/lib/" ./zenfs list --zns_pci=0000:00:06.0 --zbd=Ultra --path=rocksdbtest/dbbench