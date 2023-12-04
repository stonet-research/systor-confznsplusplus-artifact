# README

The zns-scheduler is based on Linux 6.3.8.

## How to use

First clone the linux block layer for [6.3](https://github.com/torvalds/linux/tree/v6.3/block).
Copy the linux directory into this repository.

```bash
cp Makefile linux-6.3.8/block/
cp zinc.c linux-6.3.8/block/
cd linux-6.3.8/block/

# Make module
make
# Instal the module
sudo insmod zinc.ko
```

Then it can be used as an I/O scheduler `echo zinc | sudo tee /sys/block/nvme*n*/queue/scheduler`, the name of the scheduler is 'zinc'.

## How to configure

Zinc has four configuration options (in `/sys/block/nvme*n*/queue/iosched/`):

* reset_timer_interval: window when to retry issuing a reset in milliseconds
* write_ratio: the number of write requests before a reset can be issued (in 8 KiB units)
* pending_requests_threshold: below this number of in-flight write requests, resets are not stalled (no scheduling, also in 8 kiB units)
* max_priority: number of retries for reset (to prevent reset starvation)
