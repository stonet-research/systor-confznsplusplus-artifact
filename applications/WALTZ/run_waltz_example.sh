#!/bin/bash

sudo LD_LIBRARY_PATH="/home/user/src/WALTZ/plugin/spdk/build/lib/:/home/user/src/WALTZ/plugin/spdk/dpdk/build/lib/" ./db_bench --benchmarks=enablewaltzmode,fillrandom --waltz_pcie_addr=0000:00:06.0 --fs_uri=zenfs://dev:ultra #--waltz_test_type=0

sudo LD_LIBRARY_PATH="/home/user/src/WALTZ/plugin/spdk/build/lib/:/home/user/src/WALTZ/plugin/spdk/dpdk/build/lib/" ./zenfs list --zns_pci=0000:00:06.0 --zbd=Ultra --path=rocksdbtest/dbbench

# This one does work, there is a bug somewhere
 sudo LD_LIBRARY_PATH="/home/user/src/WALTZ/plugin/spdk/build/lib/:/home/user/src/WALTZ/plugin/spdk/dpdk/build/lib/" ./db_bench --benchmarks=enablewaltzmode,fillrandom --waltz_pcie_addr=0000:00:06.0 --fs_uri=zenfs://dev:ultra --waltz_test_type=0 --waltz_zipf_dist=0.99 --waltz_scan_max=100 --waltz_key_range=6400000 --max_background_compactions=4 --max_background_flushes=4 --max_background_jobs=8 --key_size=8 --prefix_size=8 --value_size=4000 --compression_type=none --sync=true --enable_pipelined_write=false --statistics=1 --histogram=true --use_direct_reads --use_direct_io_for_flush_and_compaction --num=10000