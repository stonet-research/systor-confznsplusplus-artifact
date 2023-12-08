# ZINC - A ZNS Interference-aware NVMe Command Scheduler

This repository contains ZINC, and a ZNS command (I/O and management) interference study. Despite ZNS’s promises, with the benchmarks (micro- and macro-level workloads) we identify that the new ZNS commands create complex interference patterns with I/O and each other that lead to significant losses in application performance. We introduce a first-of-its-kind interference model ([`interference_model`](./interference_model/quantification.py)) for ZNS to quantify and study the interference overheads of ZNS. Based on our interference study, we propose ZINC, a ZNS interface-aware NVMe command scheduler that mitigates the impact of interference by prioritizing user I/O commands over flash management commands (configurable).

## Building Benchmarks and ZINC

This section provides instructions for building each of the required tools used during our study.

### Build fio

Building the custom fio requires no modifications over the conventional fio building process:

```bash
pushd tools/fio
./configure
make -j
popd
```

### Build ZenFS

To build ZenFS to run the macro-level application workloads:

```bash
pushd tools/rocksdb
DEBUG_LEVEL=0 ROCKSDB_PLUGINS=zenfs make -j 4 db_bench
sudo DEBUG_LEVEL=0 ROCKSDB_PLUGINS=zenfs make install
cd plugin/zenfs/util
make
popd
```

### Build ZINC

ZINC requires the [6.3 Linux](https://github.com/torvalds/linux/tree/v6.3/block) block layer to be cloned, into which the ZINC file (`zinc.c` and `Makefile`) must be copied to build ZINC. Once the block layer is cloned do the following:

```bash
cp Makefile linux-6.3.8/block/
cp zinc.c linux-6.3.8/block/
cd linux-6.3.8/block/

# Make module
make
# Instal the module
sudo insmod zinc.ko
```

## Using ZINC

After the `zinc.ko` module is installed, it can be set in on any NVMe device as follows:

```bash
# Replace nvme*n* with nvme device name
echo zinc | sudo tee /sys/block/nvme*n*/queue/scheduler
```

## Reproducing CCGRID'24 Results

The [`paperplots notebook`](./plotting-notebooks/paperplots.ipynb) contains all plotting scripts, with the respective data, for all figures used in the paper.

## Directory Structure

This repository is broken down into several distinct directories and subdirectories, which are organized as follows:

- [`interference_model`](./interference_model/) contains the python lib of the presented quantification model, to be imported into data parsing scripts to calculate the $Z^{Inter}$ value.
- ['plotting-notebooks'](./plotting-notebooks/) contains all plotting scripts, as jupyter notebooks, for generating figures.
- [`tools`](./tools/) contains the custom `fio` and `ZenFS` repositories for generating all micro- and macro-level benchmarks of this study.
- [`zinc-benchmarks`](./zinc-benchmarks/) contains all the benchmarking scripts and collected data for the benchmarks (micro- and macro-level) run on ZINC.
- [`zinc-scheduler`](./zinc-scheduler/) contains the source code of ZINC.
- [`zns-command-interference`](./zns-command-interference) contains all interference workloads run throughout the study. Each workload has its own subdirectory, with a benchmarking script to run the workload (run `./bench nvme0n2` on the respective device), all our collected data sets, and each workload has a plotting script to generate standalone figures apart from the paper figures (run `python3 plot.py`).
- [`util`](./util/) contains utility scripts used throughout this study, which are typically called from other benchmarking scripts.

## Cite ZINC

TODO: Reference Format for final paper

## License

TODO
