Stonet Research fio fork with zone finish benchmarking support
--------------------------------------------------------------

This modification adds support to benchmark ZNS finish operations in `io_uring_cmd` (io_uring passthrough) mode.
By specifying `finish=1` on a trim workload, fio will finish the zone instead of trimming it (resetting).
It requires that a zone be open and written to (i.e., a 4KiB write before a finish), and that threads are used.

**It requires that `io_uring_cmd` is set.**

```bash
sudo nvme zns reset-zone /dev/nvme0n2 -a
```

Example job for running finish benchmark (replacd `${DEV}` with the device name, and `${SIZE}` with the size in zones of the number of zones to finish). The job is configured with 1 write of 4K then 1 finish on the ZNS zone. A single write is required to open the zone and write a single block (or write as much data as `bs` is set to), as less allocated zones have a higher finish latency (e.g., 10% filled zone has higher latency than 60% filled zone).
Fio will issue the configured block size `bs` as a single I/O and then immediately issues a finish. The finish currently only tracks the number of I/Os and the bandwidth (latency is not being tracked currently).
The `finish` are submitted as nvme commands with ioctl through io_uring passthrough (bypassing the I/O scheduler). Hence, the finish is done synchronous with only a single finish at a time.
If the desired behavior is to finish zones concurrently, using concurrent jobs at `offset_increment` jobs with each a finish workload can issue concurrent finish commands.

```bash
[global]
name=finish
filename=/dev/${DEV}
ioengine=io_uring_cmd 
sqthread_poll=1
size=${SIZE}z
bs=4K
group_reporting
zonemode=zbd
thread=1
lat_percentiles=1

[finish]
rw=write
iodepth=1
numjobs=1
bs=4K
finish=1
```
``
