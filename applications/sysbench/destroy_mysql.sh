#!/bin/bash

sudo service mysql stop
sudo mv /var/lib/mysql /var/lib/mysql-bkup
conffile="/etc/mysql/mysql.conf.d/mysqld.cnf"
cp ./default-mysqld.cnf "$conffile"
conffile="/etc/mysql/conf.d/mysqld.cnf"
cp ./default-mysqld.cnf "$conffile"
sudo service mysql start
