#!/bin/bash
# based on https://zonedstorage.io/docs/benchmarking/myrocks and https://web.archive.org/web/20230326192014/https://docs.percona.com/percona-server/8.0/myrocks/zenfs.html#known-limitations

# Move to current dir
scriptdir=$(cd $(dirname "$0") && pwd)

if [ $# != 1 ]; then
    echo "Usage: zns (shortname)"
    exit 1
fi

sysbenchbinary="$scriptdir/sysbench/sysbench"
resultsdir="$scriptdir/results"
auxdir="/tmp/mysql_aux_$1"

mkdir -p "$resultdir"

# Create file system
sudo service mysql stop
sudo rm -r $auxdir
sudo mkdir -p $auxdir
echo "Please edit [mysqlid] in /etc/m,ysql.conf.d/mysql.cnf to add:"
echo "loose-rocksdb-fs-uri=zenfs://dev:$1"
echo "plugin-load-add=rocksdb=ha_rocksdb.so"
echo "default-storage-engine=rocksdb"
echo "Also try 'sudo ps-admin --enable-rocksdb -u root -p' if it keeps failing"
read
sudo -H -u mysql zenfs mkfs --zbd=$1 --aux_path=$auxdir --finish_threshold=0 --force
sudo service mysql start

# Prepare for fill
sudo mv /etc/mysql/mysql.conf.d/mysqld.cnf /etc/mysql/mysql.conf.d/mysqld.cnf-bkup
sudo cp ./bulkload-mysqld.cnf /etc/mysql/mysql.conf.d/mysqld.cnf
sed "s/REPLACE/$1/g"  /etc/mysql/mysql.conf.d/mysqld.cnf
service mysql restart

# Run fill
/usr/local/share/sysbench/oltp_write_only.lua --db-driver=mysql --mysql-user=root --time=0 --create_secondary=off --mysql-password=password --mysql-host=localhost --mysql-db=sbtest --mysql-storage-engine=rocksdb --table-size=250000000 --tables=20 --threads=64 --report-interval=5 prepare 1> "$resultsdir/fill-$(date +%s).out" 2> "$resultsdir/fill-$(date +%s).err";

sudo mv /etc/mysql/mysql.conf.d/mysqld.cnf /etc/mysql/mysql.conf.d/mysqld.cnf-bulkoad-bkup
sudo cp ./workload-mysqld.cnf /etc/mysql/mysql.conf.d/mysqld.cnf
sed "s/REPLACE/$1/g"  /etc/mysql/mysql.conf.d/mysqld.cnf
service mysql restart

/usr/local/share/sysbench/oltp_update_index.lua --db-driver=mysql --mysql-user=root --time=60 --create_secondary=off --mysql-password=<password> --mysql-host=localhost --mysql-db=sbtest --mysql-storage-engine=rocksdb --table-size=250000000 --tables=20 --threads=64 --report-interval=5 run 1> "$resultsdir/run-$(date +%s).out" 2> "$resultsdir/run-$(date +%s).err"

/usr/local/share/sysbench/oltp_update_index.lua --db-driver=mysql --mysql-user=root --time=60 --create_secondary=off --mysql-password=<password> --mysql-host=localhost --mysql-db=sbtest --mysql-storage-engine=rocksdb --table-size=250000000 --tables=20 --threads=64 --report-interval=5 cleanup 1> "$resultsdir/cleanup-$(date +%s).out" 2> "$resultsdir/cleanup-$(date +%s).err"
