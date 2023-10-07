# Install MyRocks with ZenFS and Sysbench

BEWARE MyRocks is installed globally.

```bash
sudo ./install_sysbench.sh
```

# Usage

On EACH bootup of the OS run and follow the instructions carefully:

```bash
sudo ./setup_mysql.sh
```

Then run the benchmarks with :

```bash
sudo ./run_sysbench.sh
```

If the benchmark does not shutdown cleanly it can become corrupt. Destroy all of MySQL in that case with:

```bash
sudo ./reinit_mysql.sh
```

Debug with:

```bash
tail /var/log/mysql/error # Check MySQL errors
sudo mysql -u root -p
show engines; # is there a RocksDB?
quit;
# Is ZenFS used?
/usr/bin/sudo -H -u mysql zenfs list --zbd=$1 --aux_path=/tmp/aux --finish_threshold=0 --force --path=.rocksdb'
```
