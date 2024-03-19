#!/bin/bash

set -e

git clone https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git linux-6.4
pushd linux-6.4
git checkout v6.4
# We need to build part of Linux in order to build the scheduler. You can control+C once the relevant files are initialized
cp /usr/src/linux-headers-$(uname -r)/.config .config
scripts/config --disable SYSTEM_TRUSTED_KEYS
scripts/config --disable SYSTEM_REVOCATION_KEYS
scripts/config --disable DEBUG_INFO
make menuconfig
make -j10 bindeb-pkg LOCALVERSION=-local
popd
rm *.deb
