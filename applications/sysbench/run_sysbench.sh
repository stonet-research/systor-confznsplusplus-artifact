#!/bin/bash
# based on https://zonedstorage.io/docs/benchmarking/myrocks and https://web.archive.org/web/20230326192014/https://docs.percona.com/percona-server/8.0/myrocks/zenfs.html#known-limitations

# Move to current dir
scriptdir=$(cd $(dirname "$0") && pwd)

if [ $# != 1 ]; then
    echo "Usage: zns (shortname)"
    exit 1
fi

sysbenchbinarydir="./sysbench/src/lua"
resultsdir="results"
auxdir="/tmp/mysql_aux_$1"
conffile="/etc/mysql/mysql.conf.d/mysqld.cnf" 
tablesize=1000 #250000000
tables=10 #20

mkdir -p "$resultsdir"
echo "Setting environment"

# Create ZenFS file system
sudo service mysql stop
sudo rm -r $auxdir
sudo -H -u mysql zenfs mkfs --zbd=$1 --aux_path=$auxdir --finish_threshold=0 --force
sudo chown mysql:mysql $auxdir
sudo chmod 750 $auxdir
sudo service mysql start

# Generate database if needed
sudo mysql -u root -e 'CREATE DATABASE IF NOT EXISTS sbtest'

# Prepare for fill
sudo -s -- <<EOF
service mysql stop
cp "$conffile" /etc/mysql/mysql.conf.d/mysqld-default-bkup.cnf
cp ./default-mysqld.cnf "$conffile"
cat rocksdb-mysqld-template.cnf >>  "$conffile"
sed "s/REPLACE/$1/g"  -i "$conffile"
cat rocksdb-bulkload-mysqld.cnf >>  "$conffile"
service mysql restart
EOF

# Run fill
echo "Filling database"
sudo $sysbenchbinarydir/oltp_write_only.lua \
    --db-driver=mysql \
    --mysql-user=root \
    --time=0 \
    --create_secondary=off \
    --mysql-password=password \
    --mysql-host=localhost \
    --mysql-db=sbtest \
    --mysql-storage-engine=rocksdb \
    --table-size=$tablesize \
    --tables=$tables \
    --threads=64 \
    --report-interval=5 \
    prepare 1> "$resultsdir/fill-$(date +%s).out" 2> "$resultsdir/fill-$(date +%s).err";

# Prepare for run
sudo -s -- <<EOF
service mysql stop
cp "$conffile" /etc/mysql/mysql.conf.d/mysqld-default-bkup.cnf
cp ./default-mysqld.cnf "$conffile"
cat rocksdb-mysqld-template.cnf >>  "$conffile"
sed "s/REPLACE/$1/g"  -i "$conffile"
cat rocksdb-workload-mysqld.cnf >>  "$conffile"
service mysql restart
EOF

echo "OLTP update index"
sudo $sysbenchbinarydir/oltp_update_index.lua \
    --db-driver=mysql \
    --mysql-user=root \
    --time=600 \
    --create_secondary=off \
    --mysql-password=password \
    --mysql-host=localhost \
    --mysql-db=sbtest \
    --mysql-storage-engine=rocksdb \
    --table-size=$tablesize \
    --tables=$tables \
    --threads=64 \
    --report-interval=5 \
    --warmup-time=20 \
    run 1> "$resultsdir/run-$(date +%s).out" 2> "$resultsdir/run-$(date +%s).err"

echo "Cleanup database"
sudo $sysbenchbinarydir/oltp_update_index.lua \
    --db-driver=mysql \
    --mysql-user=root \
    --time=60 \
    --create_secondary=off \
    --mysql-password=password \
    --mysql-host=localhost \
    --mysql-db=sbtest \
    --mysql-storage-engine=rocksdb \
    --table-size=$tablesize \
    --tables=$tables \
    --threads=64 \
    --report-interval=5 \
    cleanup 1> "$resultsdir/cleanup-$(date +%s).out" 2> "$resultsdir/cleanup-$(date +%s).err"

# Destroy database
sudo mysql -u root -e 'DROP DATABASE IF EXISTS sbtest'

# Reset
sudo -s -- <<EOF
service mysql stop
cp "$conffile" /etc/mysql/mysql.conf.d/mysqld-default-bkup.cnf
cp ./default-mysqld.cnf "$conffile"
cat rocksdb-mysqld-template.cnf >>  "$conffile"
sed "s/REPLACE/$1/g"  -i "$conffile"
service mysql restart
EOF
