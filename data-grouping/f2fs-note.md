GC calls: 685 (BG: 2)
  - data segments : 12721 (167)
  - node segments : 124 (0)
  - Reclaimed segs : Normal (12845), Idle CB (0), Idle Greedy (0), Idle AT (0), Urgent High (0), Urgent Mid (0), Urgent Low (
0)
Try to move 6348681 blocks (BG: 83910)
  - data blocks : 6340274 (83910)
  - node blocks : 8407 (0)
BG skip : IO: 61, Other: 3


Utilization: 88% (11873602 valid blocks, 0 discard blocks)
  - Node: 13117 (Inode: 873, Other: 12244)
  - Data: 11860485
  - Inline_xattr Inode: 872
  - Inline_data Inode: 3
  - Inline_dentry Inode: 1
  - Compressed Inode: 0, Blocks: 0
  - Orphan/Append/Update Inode: 0, 0, 0

Main area: 32768 segs, 256 secs 256 zones
    TYPE            segno    secno   zoneno  dirty_seg   full_seg  valid_blk
  - COLD   data:    15893      124      124        729      19961   10533857
  - WARM   data:    15627      122      122         97       2465    1300090
  - HOT    data:      469        3        3         32         49      26538
  - Dir   dnode:        9        0        0          1          0          2
  - File  dnode:     8053       62       62        108          0      12286
  - Indir nodes:      273        2        2         12          0        829
  - Pinned file:       -1       -1       -1
  - ATGC   data:       -1       -1       -1

  - Valid: 22481
  - Dirty: 973
  - Prefree: 23
  - Free: 9291 (30)

user@stosys:~/src/rocksdb$ sudo  ./db_bench --db=/mnt/f2fs --benchmarks=fillrandom,levelstats,overwrite,levelstats --use_direct_io_for_flush_and_compaction -value_size=3980 --key_size=16 --num=10000000 --compression_type=none --max_bytes_for_level_multiplier=4 --threads=1 --histogram --wal_dir=/mnt/f2fs/wal --seed=42
Initializing RocksDB Options from the specified file
Initializing RocksDB Options from command-line flags
Integrated BlobDB: blob cache disabled
RocksDB:    version 7.10.0
Date:       Tue Aug 15 14:20:54 2023
CPU:        10 * Intel(R) Xeon(R) Silver 4210R CPU @ 2.40GHz
CPUCache:   16384 KB
Keys:       16 bytes each (+ 0 bytes user-defined timestamp)
Values:     3980 bytes each (1990 bytes after compression)
Entries:    10000000
Prefix:    0 bytes
Keys per prefix:    0
RawSize:    38108.8 MB (estimated)
FileSize:   19130.7 MB (estimated)
Write rate: 0 bytes/second
Read rate: 0 ops/second
Compression: NoCompression
Compression sampling rate: 0
Memtablerep: SkipListFactory
Perf Level: 1
------------------------------------------------
Initializing RocksDB Options from the specified file
Initializing RocksDB Options from command-line flags
Integrated BlobDB: blob cache disabled
DB path: [/mnt/f2fs]
fillrandom   :     155.581 micros/op 6427 ops/sec 1555.815 seconds 10000000 operations;   24.5 MB/s
Microseconds per write:
Count: 10000000 Average: 155.5814  StdDev: 4672.42
Min: 3  Median: 8.9754  Max: 1448779
Percentiles: P50: 8.98 P75: 13.24 P99: 2671.60 P99.9: 2879.30 P99.99: 3017.80
------------------------------------------------------
(       2,       3 ]       24   0.000%   0.000%
(       3,       4 ]     8225   0.082%   0.082%
(       4,       6 ]   193694   1.937%   2.019%
(       6,      10 ]  6450324  64.503%  66.523% #############
(      10,      15 ]  1310068  13.101%  79.623% ###
(      15,      22 ]  1068123  10.681%  90.305% ##
(      22,      34 ]   300647   3.006%  93.311% #
(      34,      51 ]    67490   0.675%  93.986%
(      51,      76 ]     8524   0.085%  94.071%
(      76,     110 ]     1703   0.017%  94.088%
(     110,     170 ]     1289   0.013%  94.101%
(     170,     250 ]      800   0.008%  94.109%
(     250,     380 ]      562   0.006%  94.115%
(     380,     580 ]      537   0.005%  94.120%
(     580,     870 ]       70   0.001%  94.121%
(     870,    1300 ]   152904   1.529%  95.650%
(    1300,    1900 ]      670   0.007%  95.657%
(    1900,    2900 ]   433316   4.333%  99.990% #
(    2900,    4400 ]      382   0.004%  99.994%
(    4400,    6600 ]       83   0.001%  99.994%
(    6600,    9900 ]       54   0.001%  99.995%
(    9900,   14000 ]       25   0.000%  99.995%
(   14000,   22000 ]        4   0.000%  99.995%
(   22000,   33000 ]        2   0.000%  99.995%
(   75000,  110000 ]        1   0.000%  99.995%
(  170000,  250000 ]        1   0.000%  99.995%
(  250000,  380000 ]       11   0.000%  99.995%
(  380000,  570000 ]      213   0.002%  99.997%
(  570000,  860000 ]      189   0.002%  99.999%
(  860000, 1200000 ]       59   0.001% 100.000%
( 1200000, 1900000 ]        6   0.000% 100.000%


Level Files Size(MB)
--------------------
  0       21     1340
  1       36     2349
  2      122     7146
  3      352    18911
  4        0        0
  5        0        0
  6        0        0

DB path: [/mnt/f2fs]
overwrite    :     234.197 micros/op 4269 ops/sec 2341.974 seconds 10000000 operations;   16.3 MB/s
Microseconds per write:
Count: 10000000 Average: 234.1974  StdDev: 4447.88
Min: 3  Median: 9.9359  Max: 5596627
Percentiles: P50: 9.94 P75: 18.70 P99: 2769.53 P99.9: 2890.88 P99.99: 4250.73
------------------------------------------------------
(       2,       3 ]       14   0.000%   0.000%
(       3,       4 ]     4733   0.047%   0.047%
(       4,       6 ]   131113   1.311%   1.359%
(       6,      10 ]  4943355  49.434%  50.792% ##########
(      10,      15 ]  1437374  14.374%  65.166% ###
(      15,      22 ]  1859960  18.600%  83.765% ####
(      22,      34 ]   462526   4.625%  88.391% #
(      34,      51 ]    95545   0.955%  89.346%
(      51,      76 ]    11357   0.114%  89.460%
(      76,     110 ]     1824   0.018%  89.478%
(     110,     170 ]     1241   0.012%  89.490%
(     170,     250 ]     1341   0.013%  89.504%
(     250,     380 ]      774   0.008%  89.512%
(     380,     580 ]      646   0.006%  89.518%
(     580,     870 ]      148   0.001%  89.520%
(     870,    1300 ]   301895   3.019%  92.538% #
(    1300,    1900 ]     1264   0.013%  92.551%
(    1900,    2900 ]   741655   7.417%  99.968% #
(    2900,    4400 ]     2482   0.025%  99.992%
(    4400,    6600 ]      256   0.003%  99.995%
(    6600,    9900 ]       89   0.001%  99.996%
(    9900,   14000 ]       26   0.000%  99.996%
(   14000,   22000 ]       12   0.000%  99.996%
(   22000,   33000 ]        4   0.000%  99.996%
(   33000,   50000 ]        4   0.000%  99.996%
(   50000,   75000 ]        1   0.000%  99.996%
(  170000,  250000 ]        2   0.000%  99.996%
(  250000,  380000 ]       25   0.000%  99.997%
(  380000,  570000 ]      184   0.002%  99.999%
(  570000,  860000 ]      105   0.001% 100.000%
(  860000, 1200000 ]       31   0.000% 100.000%
( 1200000, 1900000 ]       10   0.000% 100.000%
( 1900000, 2900000 ]        3   0.000% 100.000%
( 4300000, 6500000 ]        1   0.000% 100.000%


Level Files Size(MB)
--------------------
  0       17     1085
  1       18     1039
  2       77     4500
  3      322    17792
  4      429    21793
  5        0        0
  6        0        0

