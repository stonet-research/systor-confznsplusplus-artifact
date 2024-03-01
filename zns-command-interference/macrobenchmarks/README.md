# rocksdb-with-interference

Experiments used to measure the effect of resets on RocksDB. In the directory `zones` we test interference within one namespace, with `namespaces` we test interferences across multiple namespaces. Experiments with `bench-f2fs` use the F2FS file system and `benc-zenfs` use the ZenFS file system. Preferably, only use ZenFS as the F2FS experiments has out of space issues.

The workload itself consists out of a db_bench fillrandom workload and a concurrent write workload to saturate the device (otherwise there is no observable interference). The concurrent reset workload can be enabled/disabled to test the effect with and without reset. Additionally, the scheduler can be set directly (to zinc or mq-deadline).

# zenfs-with-one-workload

Baseline benchmark to test ZenFS performance with mq-deadline with one concurrent "fio" write workload.
This experiment can be used to test to see if they can concurrently reach peak performance.

# rocksdb-fs-average-rq-size

Experiments to measure the average request size send to ZNS in RocksDB. This includes sizes of RocksDB requests (WAL, SSTable...) and block layer (are I/O requests merged?). We test this for both ZenFS and F2FS.
The main intend is to see what are common request sizes, so we know what to optimize for.
Note this experiment is currently broken with some versions of BPFtrace (preferably also iostat concurrently and look at fio's output).
