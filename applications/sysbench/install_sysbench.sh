#!/bin/bash
# Dependencies
sudo apt-get update
sudo apt-get installi libssl-dev libmysqlclient-dev

# Get Percona server for MySQL
wget https://repo.percona.com/apt/percona-release_latest.$(lsb_release -sc)_all.deb
sudo apt install gnupg2 lsb-release ./percona-release_latest.*_all.deb
sudo percona-release setup ps80

sudo apt install percona-server-server
sudo apt install percona-server-rocksdb

# Setup sysbench
git clone https://github.com/akopytov/sysbench.git sysbench
cd sysbench || exit 1
./autogen.sh
./configure
make -j
