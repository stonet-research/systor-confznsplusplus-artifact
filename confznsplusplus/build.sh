#!/bin/bash

mkdir -p build
cd build
../configure \
    --target-list=x86_64-softmmu \
    --enable-kvm \
    --enable-linux-aio \
    --enable-trace-backends=log \
    --disable-werror \
    --disable-gtk
make -j 
