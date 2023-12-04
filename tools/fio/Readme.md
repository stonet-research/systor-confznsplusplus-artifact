Stonet Research fio fork with zone finish benchmarking support
--------------------------------------------------------------

This modification adds support to benchmark ZNS finish operations in `io_uring_cmd` (io_uring passthrough) mode.
By specifying `finish=1` on a trim workload, fio will finish the zone instead of trimming it (resetting).
It requires that a zone be open and written to (i.e., a 4KiB write before a finish), and that threads are used.

**It requires that `thread=1` is used, and `io_uring_cmd` is set.**
Also pay attention to the max active zones supported by the device, such that setting concurrent finish jobs not higher than this, as the zones must be opened with writes before.

**NOTE** it also requires all zones to be reset before the run (otherwise the full zones will be ignored to avoid reset overheads in the benchmark.
Run:

```bash
sudo nvme zns reset-zone /dev/nvme0n2 -a
```

Example job for running finish benchmark, with 1 write of 4K then 1 finishe on the first ZNS zones, then write the 2nd zone and finish this zone.
Note, that each write and finish are configured as new jobs (with the only difference of the offset), such that not the same zone is finished every time (it will be reset between runs however!).
It can also be configured to finish the same zone again by just specifying one set of `fill-prep` and `finish` jobs, and setting globally `loops=100` or any desired value.

```bash
[global]
name=loaded-reset
filename=/dev/${DEV}
ioengine=io_uring_cmd 
sqthread_poll=1
size=1z
bs=4K
group_reporting
zonemode=zbd
thread=1
lat_percentiles=1

[fill-prep]
iodepth=1
rw=write
numjobs=1
offset_increment=1z
io_limit=4K

[finish]
stonewall
rw=trim
iodepth=1
numjobs=1
bs=2147483648
finish=1

[fill-prep2]
stonewall
iodepth=1
rw=write
numjobs=1
offset=1z
offset_increment=1z
io_limit=4K

[finish2]
stonewall
rw=trim
iodepth=1
numjobs=1
bs=2147483648
offset=1z
finish=1
```

Execute example job (there is an example job provided in [`example-job-finish.fio`](example-job-finish.fio)):

```bash
sudo env DEV=ng0n2 BS=2147486438 ./fio --output-format=json --output=test.json example-job-finish.fio
```
