#!/bin/bash
# based on https://zonedstorage.io/docs/benchmarking/myrocks and https://web.archive.org/web/20230326192014/https://docs.percona.com/percona-server/8.0/myrocks/zenfs.html#known-limitations

# Move to current dir
scriptdir=$(cd $(dirname "$0") && pwd)

if [ $# != 1 ]; then
    echo "Usage: zns (shortname)"
    exit 1
fi

znsdevice="/dev/$1"

# Ensure device is setup
echo "Add the following to '/etc/security/limits.conf' if not already done:"
echo "root       hard  nofile    500000"
echo "root       hard  nofile    500000" 
echo ""
echo "Also add the following to '/etc/pam.d/common-session':"
echo "session required        pam_limits.so"
echo ""
echo "And the following to /etc/sysctl.conf:"
echo "fs.file-max = 2097152"
read

echo "Run systemctl edit --full mysql"
echo "LimitNoFILE = 500000"

systemctl daemon-reload

# Setup device
sudo chown mysql:mysql $znsdevice
sudo chmod 640 $znsdevice
echo mq-deadline | sudo tee "/sys/block/$1/queue/scheduler"

auxdir="/tmp/mysql_aux_$1"
sudo rm -r $auxdir
sudo mkdir -p $auxdir
sudo chown mysql:mysql $auxdir
sudo chmod 750 $auxdir

# Force RocksDB to be enabled in MySQL (it will not be by default...)
sudo service mysql stop
echo "Comment out 'loose-rocksdb-fs-uri' and 'default-storage-engine' in /etc/mysql/conf.d/mysql.cnf"
read
sudo service mysql start
sudo ps-admin --enable-rocksdb -u root -p

# Create file system, this ttme do add RocksDB configuration
sudo service mysql stop
echo "Please edit [mysqlid] in /etc/mysql/conf.d/mysql.cnf to add:"
echo "pid-file    = /var/run/mysqld/mysqld.pid"
echo "socket      = /var/run/mysqld/mysqld.sock"
echo "datadir     = /var/lib/mysql"
echo "log-error   = /var/log/mysql/error.log"
echo ""
echo "rocksdb"
echo "default-storage-engine        =   rocksdb"
echo "skip-innodb"
echo "default-tmp-storage-engine    =   MyISAM"
echo "log-error                     =   /var/log/mysql/error.log"
echo "loose-rocksdb-fs-uri          =   zenfs://dev:$1"
read
sudo -H -u mysql zenfs mkfs --zbd=$1 --aux_path=$auxdir --finish_threshold=0 --force
sudo service mysql start
