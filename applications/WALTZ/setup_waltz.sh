#!/bin/bash

cd WALTZ || exit 1
sudo LD_LIBRARY_PATH="/home/user/src/WALTZ/plugin/spdk/build/lib/:/home/user/src/WALTZ/plugin/spdk/dpdk/build/lib/"  ./format_mkfs.sh Ultra