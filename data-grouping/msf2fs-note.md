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

## Setup with 2/5/6

Every 1.0s: cat /sys/kernel/debug/f2fs/status | grep -A7 -i 'gc calls'                      stosys: Fri Aug 18 17:06:41 2023

GC calls: 2983 (BG: 1)
  - data segments : 11493 (0)
  - node segments : 440 (0)
  - Reclaimed segs : Normal (11933), Idle CB (0), Idle Greedy (0), Idle AT (0), Urgent High (0), Urgent Mid (0), Urgent Low
(0)
Try to move 5449567 blocks (BG: 0)
  - data blocks : 5389841 (0)
  - node blocks : 59726 (0)
BG skip : IO: 12, Other: 1

root@stosys:/home/user# cat /sys/kernel/debug/f2fs/status | grep -A56 -i 'main'
[SB: 1] [CP: 2] [SIT: 4] [NAT: 116] [SSA: 70] [MAIN: 32768(OverProv:3076 Resv:1697)]

Current Time Sec: 4326 / Mounted Time Sec: 68

Utilization: 86% (13178595 valid blocks, 0 discard blocks)
  - Node: 14511 (Inode: 916, Other: 13595)
  - Data: 13164084
  - Inline_xattr Inode: 915
  - Inline_data Inode: 3
  - Inline_dentry Inode: 1
  - Compressed Inode: 0, Blocks: 0
  - Orphan/Append/Update Inode: 0, 0, 0

Main area: 32768 segs, 1024 secs 1024 zones

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
  - HOT  data:      0     2656       83       83          1          0        101
  - HOT  data:      1      202        6        6         11          0        398
  - WARM data:      0    25760      805      805        104       2932    1537517
  - WARM data:      1    31898      996      996         98       2526    1329276
  - WARM data:      2    32076     1002     1002        112       3018    1583738
  - WARM data:      3      104        3        3         99       2750    1443783
  - WARM data:      4      139        4        4         99       2828    1482783
  - COLD data:      0    29846      932      932         95       2041    1077305
  - COLD data:      1    31968      999      999        113       1632     871445
  - COLD data:      2     1037       32       32        117       2088    1110382
  - COLD data:      3     1432       44       44        108       1615     863886
  - COLD data:      4     1510       47       47        110       2270    1202708
  - COLD data:      5    28853      901      901         55       1202     638065
  - HOT  node:      0       11        0        0          1          0          2
  - WARM node:      0    14535      454      454         71          0      13642
  - COLD node:      0       87        2        2         19          0        867
  - Pinned file:            -1       -1       -1
  - ATGC   data:            -1       -1       -1

  - Valid: 24908
  - Dirty: 1197
  - Prefree: 10
  - Free: 6653 (54)

user@stosys:~/src/rocksdb$ sudo  ./db_bench --db=/mnt/f2fs --benchmarks=fillrandom,levelstats,overwrite,levelstats --use_direct_io_for_flush_and_compaction -value_size=3980 --key_size=16 --num=11000000 --compression_type=none --threads=1 --histogram --wal_dir=/mnt/f2fs/wal --seed=42
Initializing RocksDB Options from the specified file
Initializing RocksDB Options from command-line flags
RocksDB:    version 7.3
Date:       Fri Aug 18 15:56:36 2023
CPU:        10 * Intel(R) Xeon(R) Silver 4210R CPU @ 2.40GHz
CPUCache:   16384 KB
Keys:       16 bytes each (+ 0 bytes user-defined timestamp)
Values:     3980 bytes each (1990 bytes after compression)
Entries:    11000000
Prefix:    0 bytes
Keys per prefix:    0
RawSize:    41919.7 MB (estimated)
FileSize:   21043.8 MB (estimated)
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
fillrandom   :     154.501 micros/op 6472 ops/sec;   24.7 MB/s
Microseconds per write:
Count: 11000000 Average: 154.5005  StdDev: 279.27
Min: 3  Median: 8.8413  Max: 1002204
Percentiles: P50: 8.84 P75: 13.54 P99: 2697.58 P99.9: 2882.37 P99.99: 3954.18
------------------------------------------------------
(       2,       3 ]      117   0.001%   0.001%
(       3,       4 ]    22295   0.203%   0.204%
(       4,       6 ]   493874   4.490%   4.694% #
(       6,      10 ]  7016142  63.783%  68.477% #############
(      10,      15 ]  1013615   9.215%  77.691% ##
(      15,      22 ]  1434747  13.043%  90.734% ###
(      22,      34 ]   232116   2.110%  92.845%
(      34,      51 ]    39458   0.359%  93.203%
(      51,      76 ]     6562   0.060%  93.263%
(      76,     110 ]     1195   0.011%  93.274%
(     110,     170 ]      486   0.004%  93.278%
(     170,     250 ]      135   0.001%  93.279%
(     250,     380 ]      372   0.003%  93.283%
(     380,     580 ]      130   0.001%  93.284%
(     580,     870 ]     1052   0.010%  93.294%
(     870,    1300 ]   199918   1.817%  95.111%
(    1300,    1900 ]      494   0.004%  95.116%
(    1900,    2900 ]   535738   4.870%  99.986% #
(    2900,    4400 ]      646   0.006%  99.992%
(    4400,    6600 ]      302   0.003%  99.994%
(    6600,    9900 ]       70   0.001%  99.995%
(    9900,   14000 ]       20   0.000%  99.995%
(   14000,   22000 ]       13   0.000%  99.995%
(  110000,  170000 ]        1   0.000%  99.995%
(  170000,  250000 ]       63   0.001%  99.996%
(  250000,  380000 ]      246   0.002%  99.998%
(  380000,  570000 ]      181   0.002% 100.000%
(  570000,  860000 ]       11   0.000% 100.000%
(  860000, 1200000 ]        1   0.000% 100.000%


Level Files Size(MB)
--------------------
  0       22     1404
  1       42     2358
  2      279    16531
  3      178    10691
  4        0        0
  5        0        0
  6        0        0

DB path: [/mnt/f2fs]
overwrite    :     225.181 micros/op 4440 ops/sec;   16.9 MB/s
Microseconds per write:
Count: 11000000 Average: 225.1813  StdDev: 328.41
Min: 3  Median: 9.6380  Max: 666231
Percentiles: P50: 9.64 P75: 18.20 P99: 2770.30 P99.9: 2889.29 P99.99: 4081.31
------------------------------------------------------
(       2,       3 ]       77   0.001%   0.001%
(       3,       4 ]    14386   0.131%   0.131%
(       4,       6 ]   275159   2.501%   2.633% #
(       6,      10 ]  5728870  52.081%  54.714% ##########
(      10,      15 ]  1271213  11.556%  66.270% ##
(      15,      22 ]  2103750  19.125%  85.395% ####
(      22,      34 ]   372484   3.386%  88.781% #
(      34,      51 ]    61704   0.561%  89.342%
(      51,      76 ]     9051   0.082%  89.424%
(      76,     110 ]     1761   0.016%  89.441%
(     110,     170 ]      639   0.006%  89.446%
(     170,     250 ]      251   0.002%  89.449%
(     250,     380 ]      183   0.002%  89.450%
(     380,     580 ]      123   0.001%  89.451%
(     580,     870 ]      143   0.001%  89.453%
(     870,    1300 ]   325265   2.957%  92.410% #
(    1300,    1900 ]      823   0.007%  92.417%
(    1900,    2900 ]   832032   7.564%  99.981% ##
(    2900,    4400 ]     1252   0.011%  99.992%
(    4400,    6600 ]      289   0.003%  99.995%
(    6600,    9900 ]       73   0.001%  99.996%
(    9900,   14000 ]       30   0.000%  99.996%
(   14000,   22000 ]       15   0.000%  99.996%
(   22000,   33000 ]        5   0.000%  99.996%
(   33000,   50000 ]        3   0.000%  99.996%
(   50000,   75000 ]        6   0.000%  99.996%
(   75000,  110000 ]        2   0.000%  99.996%
(  110000,  170000 ]        2   0.000%  99.996%
(  170000,  250000 ]       59   0.001%  99.997%
(  250000,  380000 ]      199   0.002%  99.999%
(  380000,  570000 ]      145   0.001% 100.000%
(  570000,  860000 ]        6   0.000% 100.000%


Level Files Size(MB)
--------------------
  0        2      128
  1       53     3095
  2      265    15866
  3      559    30642
  4        0        0
  5        0        0
  6        0        0





