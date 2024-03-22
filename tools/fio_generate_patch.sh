#!/bin/bash

set -e

git clone https://github.com/axboe/fio.git fio-patch
pushd fio-patch
git checkout 4a0c766
popd
echo "Cloned fio"
rm -r fio-patch/*
cp -r fio/* fio-patch/
echo "Update fio-patch code"
pushd fio-patch
echo "Generated patch"
git diff > ../fio.4a0c766.patch
popd
sudo rm -r fio-patch
echo "Cleanup"
