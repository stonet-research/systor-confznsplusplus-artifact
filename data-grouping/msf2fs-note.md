## Setup with hot/warm/cold streams (2/5/6)

GC calls: 1961 (BG: 1)
  - data segments : 43009 (0)
  - node segments : 222 (0)
  - Reclaimed segs : Normal (43231), Idle CB (0), Idle Greedy (0), Idle AT (0), Urgent High (0), Urgent Mid (0), Urgent Low (
0)
Try to move 21474203 blocks (BG: 0)
  - data blocks : 21452222 (0)
  - node blocks : 21981 (0)
BG skip : IO: 14, Other: 1

root@stosys:/home/user# cat /sys/kernel/debug/f2fs/status | grep -A56 -i 'main'
[SB: 1] [CP: 2] [SIT: 4] [NAT: 116] [SSA: 134] [MAIN: 32768(OverProv:6468 Resv:3874)]

Current Time Sec: 5960 / Mounted Time Sec: 1161

Utilization: 82% (11165832 valid blocks, 0 discard blocks)
  - Node: 12345 (Inode: 796, Other: 11549)
  - Data: 11153487
  - Inline_xattr Inode: 795
  - Inline_data Inode: 3
  - Inline_dentry Inode: 1
  - Compressed Inode: 0, Blocks: 0
  - Orphan/Append/Update Inode: 0, 0, 0

Main area: 32768 segs, 256 secs 256 zones

    Multi-Stream INFO:
  - Stream Allocation:
         Policy: SPF
  - Maximum Streams: 16
  - Active Streams: 16
  - STREAMS:
        Maximum:  [  2  5  6  1  1  1  ]
         Active:  [  2  5  6  1  1  1  ]
      EXCLUSIVE:  [  0  0  0  0  0  0  ]
  - ACTIVE STREAM BITMAPS:
       HOT_DATA   [ 1 1 0 0 0 0 0 0 0 0 0 ]
       WARM_DATA  [ 1 1 1 1 1 0 0 0 0 0 0 ]
       COLD_DATA  [ 1 1 1 1 1 1 0 0 0 0 0 ]
       HOT_NODE   [ 1 0 0 0 0 0 0 0 0 0 0 ]
       WARM_NODE  [ 1 0 0 0 0 0 0 0 0 0 0 ]
       COLD_NODE  [ 1 0 0 0 0 0 0 0 0 0 0 ]
  - EXCLUSIVE STREAM BITMAPS:
       HOT_DATA   [ - 0 ]
       WARM_DATA  [ - 0 0 0 0 ]
       COLD_DATA  [ - 0 0 0 0 0 ]
       HOT_NODE   [ - ]
       WARM_NODE  [ - ]
       COLD_NODE  [ - ]
  - EXCLUSIVE STREAM INO-MAP:
       HOT_DATA   [ - 0 ]
       WARM_DATA  [ - 0 0 0 0 ]
       COLD_DATA  [ - 0 0 0 0 0 ]
       HOT_NODE   [ - ]
       WARM_NODE  [ - ]
       COLD_NODE  [ - ]

    TYPE       STREAM    segno    secno   zoneno  dirty_seg   full_seg  valid_blk
  - HOT  data:      0      413        3        3         15          0        640
  - HOT  data:      1      794        6        6         10         17       9513
  - WARM data:      0    31024      242      242         44       1026     541552
  - WARM data:      1    29044      226      226         46       1122     592435
  - WARM data:      2    27958      218      218         43        922     486258
  - WARM data:      3    32168      251      251         29        721     378202
  - WARM data:      4    20198      157      157         23        774     406609
  - COLD data:      0     1008        7        7        108       2938    1540112
  - COLD data:      1     1452       11       11         62       2277    1189337
  - COLD data:      2     1246        9        9        104       3141    1645330
  - COLD data:      3     1107        8        8         88       3035    1586245
  - COLD data:      4     1586       12       12         69       2458    1285034
  - COLD data:      5    19240      150      150         96       2834    1492201
  - HOT  node:      0       10        0        0          1          0          2
  - WARM node:      0     1371       10       10         83          0      11590
  - COLD node:      0      275        2        2         10          0        753
  - Pinned file:            -1       -1       -1
  - ATGC   data:            -1       -1       -1

  - Valid: 21281
  - Dirty: 816
  - Prefree: 142
  - Free: 10529 (31)


  user@stosys:~/src/rocksdb$ sudo  ./db_bench --db=/mnt/f2fs --benchmarks=fillrandom,levelstats,overwrite,levelstats --use_direct_io_for_flush_and_compaction -value_size=3980 --key_size=16 --num=10000000 --compression_type=none --max_bytes_for_level_multiplier=4 --threads=1 --histogram --wal_dir=/mnt/f2fs/wal --seed=42
Initializing RocksDB Options from the specified file
Initializing RocksDB Options from command-line flags
RocksDB:    version 7.3
Date:       Tue Aug 15 15:56:46 2023
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
DB path: [/mnt/f2fs]
fillrandom   :     173.745 micros/op 5755 ops/sec;   21.9 MB/s
Microseconds per write:
Count: 10000000 Average: 173.7448  StdDev: 364.63
Min: 3  Median: 9.0249  Max: 777917
Percentiles: P50: 9.02 P75: 14.58 P99: 2719.51 P99.9: 2885.04 P99.99: 4188.69
------------------------------------------------------
(       2,       3 ]       98   0.001%   0.001%
(       3,       4 ]    15102   0.151%   0.152%
(       4,       6 ]   338166   3.382%   3.534% #
(       6,      10 ]  6144424  61.444%  64.978% ############
(      10,      15 ]  1095164  10.952%  75.930% ##
(      15,      22 ]  1291141  12.911%  88.841% ###
(      22,      34 ]   297525   2.975%  91.816% #
(      34,      51 ]    60949   0.609%  92.426%
(      51,      76 ]     7797   0.078%  92.504%
(      76,     110 ]     1460   0.015%  92.518%
(     110,     170 ]      575   0.006%  92.524%
(     170,     250 ]      144   0.001%  92.525%
(     250,     380 ]       66   0.001%  92.526%
(     380,     580 ]       68   0.001%  92.527%
(     580,     870 ]      191   0.002%  92.529%
(     870,    1300 ]   200892   2.009%  94.538%
(    1300,    1900 ]      673   0.007%  94.544%
(    1900,    2900 ]   543699   5.437%  99.981% #
(    2900,    4400 ]     1008   0.010%  99.991%
(    4400,    6600 ]      286   0.003%  99.994%
(    6600,    9900 ]       77   0.001%  99.995%
(    9900,   14000 ]       31   0.000%  99.995%
(   14000,   22000 ]       16   0.000%  99.996%
(  110000,  170000 ]        2   0.000%  99.996%
(  170000,  250000 ]       21   0.000%  99.996%
(  250000,  380000 ]       53   0.001%  99.996%
(  380000,  570000 ]      354   0.004% 100.000%
(  570000,  860000 ]       18   0.000% 100.000%


Level Files Size(MB)
--------------------
  0        7      447
  1       56     3468
  2      129     7248
  3      333    18337
  4        0        0
  5        0        0
  6        0        0

DB path: [/mnt/f2fs]
overwrite    :     294.717 micros/op 3393 ops/sec;   12.9 MB/s
Microseconds per write:
Count: 10000000 Average: 294.7175  StdDev: 413.56
Min: 3  Median: 10.5004  Max: 4784982
Percentiles: P50: 10.50 P75: 19.93 P99: 2855.70 P99.9: 4238.53 P99.99: 6329.10
------------------------------------------------------
(       2,       3 ]       71   0.001%   0.001%
(       3,       4 ]    10793   0.108%   0.109%
(       4,       6 ]   215557   2.156%   2.264%
(       6,      10 ]  4657987  46.580%  48.844% #########
(      10,      15 ]  1155082  11.551%  60.395% ##
(      15,      22 ]  2071725  20.717%  81.112% ####
(      22,      34 ]   453971   4.540%  85.652% #
(      34,      51 ]    92263   0.923%  86.574%
(      51,      76 ]    11591   0.116%  86.690%
(      76,     110 ]     2014   0.020%  86.711%
(     110,     170 ]      884   0.009%  86.719%
(     170,     250 ]      250   0.003%  86.722%
(     250,     380 ]      161   0.002%  86.723%
(     380,     580 ]      113   0.001%  86.725%
(     580,     870 ]      120   0.001%  86.726%
(     870,    1300 ]   346609   3.466%  90.192% #
(    1300,    1900 ]     1133   0.011%  90.203%
(    1900,    2900 ]   920453   9.205%  99.408% ##
(    2900,    4400 ]    55161   0.552%  99.959%
(    4400,    6600 ]     3492   0.035%  99.994%
(    6600,    9900 ]      117   0.001%  99.995%
(    9900,   14000 ]       40   0.000%  99.996%
(   14000,   22000 ]       21   0.000%  99.996%
(   22000,   33000 ]        6   0.000%  99.996%
(   33000,   50000 ]        4   0.000%  99.996%
(   50000,   75000 ]        2   0.000%  99.996%
(   75000,  110000 ]        3   0.000%  99.996%
(  110000,  170000 ]        3   0.000%  99.996%
(  170000,  250000 ]       12   0.000%  99.996%
(  250000,  380000 ]       43   0.000%  99.997%
(  380000,  570000 ]      270   0.003% 100.000%
(  570000,  860000 ]       31   0.000% 100.000%
(  860000, 1200000 ]       10   0.000% 100.000%
( 1200000, 1900000 ]        3   0.000% 100.000%
( 1900000, 2900000 ]        2   0.000% 100.000%
( 2900000, 4300000 ]        2   0.000% 100.000%
( 4300000, 6500000 ]        1   0.000% 100.000%


Level Files Size(MB)
--------------------
  0       32     2042
  1       35     2151
  2      156     8796
  3      564    30522
  4        0        0
  5        0        0
  6        0        0

## Setup with 1/5/7


