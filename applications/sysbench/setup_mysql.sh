#!/bin/bash
# based on https://zonedstorage.io/docs/benchmarking/myrocks and https://web.archive.org/web/20230326192014/https://docs.percona.com/percona-server/8.0/myrocks/zenfs.html#known-limitations

# Move to current dir
scriptdir=$(cd $(dirname "$0") && pwd)

if [ $# != 1 ]; then
    echo "Usage: zns (shortname)"
    exit 1
fi

znsdevice="/dev/$1"
auxdir="/tmp/mysql_aux_$1"
conffile="/etc/mysql/mysql.conf.d/mysqld.cnf" 

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
echo "Press <ENTER> if done"
read

echo "Run systemctl edit --full mysql and ensure:"
echo "LimitNoFILE = 500000"
echo "Press <ENTER> if done"
read

systemctl daemon-reload

# Setup device
sudo chown mysql:mysql $znsdevice
sudo chmod 640 $znsdevice
echo mq-deadline | sudo tee "/sys/block/$1/queue/scheduler" > /dev/null

# Force RocksDB to be enabled in MySQL (it will not be by default...)
sudo -s -- <<EOF
service mysql stop
echo "Setting up MySQL without MyRocks first (need to enable RocksDB as an engine first)"
cp "$conffile" /etc/mysql/mysql.conf.d/mysqld-original-bkup.cnf
cp ./default-mysqld.cnf "$conffile"
service mysql start
ps-admin --enable-rocksdb -u root -p
EOF

# Load RocksDB configuration
sudo -s -- <<EOF
service mysql stop
cp "$conffile" /etc/mysql/mysql.conf.d/mysqld-default-bkup.cnf
cp ./default-mysqld.cnf "$conffile"
cat rocksdb-mysqld-template.cnf >>  "$conffile"
sed "s/REPLACE/$1/g"  -i "$conffile"
EOF

# Create ZenFS file system for MyRocks
sudo rm -rf $auxdir
sudo -H -u mysql zenfs mkfs --zbd=$1 --aux_path=$auxdir --finish_threshold=0 --force
sudo chown mysql:mysql $auxdir
sudo chmod 750 $auxdir
sudo service mysql start

echo "If there is a failure:"
echo "  *Check the log with: 'tail /var/log/mysql/error'"
echo "  *Check if RocksDB is enabled/defaulted with: 'sudo mysql -u root -p' followed by 'show engines;'"
echo "  *Check if ZenFS is used with: '/usr/bin/sudo -H -u mysql zenfs list --zbd=$1 \
    --aux_path=/tmp/aux --finish_threshold=0 --force --path=.rocksdb'"
echo "  *Check the log withh: 'tail /var/log/mysql/error'"
