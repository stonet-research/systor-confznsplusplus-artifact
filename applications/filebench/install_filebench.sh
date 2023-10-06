#!/bin/bash

git clone https://github.com/filebench/filebench.git filebench
cd filebench || exit 1

# pin version
git checkout 22620e602cbbebad90c0bd041896ebccf70dbf5f

# Generate autotool scripts
libtoolize
aclocal
autoheader
automake --add-missing
autoconf

# Compile
./configure
make
