#!/bin/bash
scriptdir=$(cd $(dirname "$0") && pwd)

# Dependencies
sudo apt-get update
sudo apt-get installi libssl-dev libmysqlclient-dev

# Get Percona server for MySQL

## From apt, recommended by Percona but does not work...
# wget https://repo.percona.com/apt/percona-release_latest.$(lsb_release -sc)_all.deb
# sudo apt install gnupg2 lsb-release ./percona-release_latest.*_all.deb
# sudo percona-release setup ps80
# sudo apt install percona-server-server
# sudo apt install percona-server-rocksdb

## From source, does work
git clone https://github.com/percona/percona-server.git percona-server
cd percona-server
git checkout  0fe62c853e2c710ef2e3804cc9bef9c09466de0
mkdir build && cd build
cmake -DBUILD_CONFIG=mysql_release \
                -DCMAKE_INSTALL_PREFIX=/usr \
                -DINSTALL_DOCDIR=share/mysql/docs \
                -DINSTALL_DOCREADMEDIR=share/mysql \
                -DINSTALL_INCLUDEDIR=include/mysql \
                -DINSTALL_INFODIR=share/mysql/docs \
                -DINSTALL_LIBDIR=lib/$(DEB_HOST_MULTIARCH) \
                -DINSTALL_MANDIR=share/man \
                -DINSTALL_MYSQLSHAREDIR=share/mysql \
                -DINSTALL_MYSQLTESTDIR=lib/mysql-test \
                -DINSTALL_PLUGINDIR=lib/mysql/plugin/debug \
                -DINSTALL_SBINDIR=sbin \
                -DINSTALL_SCRIPTDIR=bin \
                -DINSTALL_SUPPORTFILESDIR=share/mysql \
                -DSYSCONFDIR=/etc/mysql \
                -DMYSQL_UNIX_ADDR=/var/run/mysqld/mysqld.sock \
                -DCMAKE_BUILD_TYPE=Release \
                -DCOMPILATION_COMMENT=$(COMPILATION_COMMENT_DEBUG) \
                -DSYSTEM_TYPE="debian-linux-gnu" \
                -DINSTALL_LAYOUT=DEB \
                -DWITH_INNODB_MEMCACHED=ON \
                -DWITH_MECAB=system \
                -DWITH_ARCHIVE_STORAGE_ENGINE=ON \
                -DWITH_BLACKHOLE_STORAGE_ENGINE=ON \
                -DWITH_FEDERATED_STORAGE_ENGINE=ON \
                -DWITH_PAM=OFF \
                -DWITH_ROCKSDB=ON \
                -DROCKSDB_DISABLE_AVX2=1 \
                -DROCKSDB_DISABLE_MARCH_NATIVE=1 \
                -DFORCE_INSOURCE_BUILD=1 \
                -DDOWNLOAD_BOOST=1 \
                -DWITH_BOOST=libboost \
                -DWITH_PACKAGE_FLAGS=OFF \
                -DWITH_SYSTEM_LIBS=ON \
                -DWITH_PROTOBUF=bundled \
                -DWITH_RAPIDJSON=bundled \
                -DWITH_ICU=bundled \
                -DWITH_ZSTD=bundled \
                -DWITH_ZLIB=bundled \
                -DWITH_LZ4=bundled \
                -DWITH_LIBEVENT=bundled \
                -DWITH_FIDO=bundled \
                -DWITH_ENCRYPTION_UDF=ON \
                -DWITH_NUMA=ON \
                -DWITH_LDAP=system \
                -DWITH_EXTRA_CHARSETS=all $(TOKUDB_OPTS_DEBUG) \
                -DROCKSDB_PLUGINS=zenfs \
                -DWITH_ZENFS_UTILITY=ON \
                -DWITH_ZBD=bundled  ..
make -j
sudo make install

# Setup sysbench
git clone https://github.com/akopytov/sysbench.git sysbench
cd sysbench || exit 1
./autogen.sh
./configure
make -j
