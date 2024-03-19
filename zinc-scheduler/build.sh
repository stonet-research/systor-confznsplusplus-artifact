#!/bin/bash

cp Makefile linux-6.4/block/
cp zinc.c linux-6.4/block/
pushd linux-6.4/block/
make

# Remove from kernel
if lsmod | grep -wq "zinc"; then
    sudo rmmod zinc
fi

# Insert in kernel
sudo insmod zinc.ko
