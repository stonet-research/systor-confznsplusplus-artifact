#!/bin/bash

# Git
git clone https://github.com/SNU-ARC/WALTZ.git WALTZ
cd WALTZ || exit 1
git checkout 1a30ac01e11a1716aa7382f5f670d586d362f6fd

# Monkey patch
# TODO: Fix patch to be generic
git apply WALTZ.patch

cd scriptdir
./rel_build.sh
cd ..
sudo DEBUG_LEVEL=0 ROCKSDB_PLUGINS=zenfs make -j4 install

pushd plugin/zenfs/util
LD_LIBRARY_PATH="/home/user/src/WALTZ/plugin/spdk/build/lib/:/home/user/src/WALTZ/plugin/spdk/dpdk/build/lib/" make
popd


