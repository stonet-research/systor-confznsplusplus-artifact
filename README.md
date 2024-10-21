# Exploring I/O Management Performance in ZNS with ConfZNS++

This repository contains the source code to reproduce the results of the SYSTOR'24 paper "Exploring I/O Management Performance in ZNS with ConfZNS++".
This code includes:

* A performance characterization of ZNS I/O management interference:  [`microbenchmarks`](./benchmarks/passthrough-zns-command-interference/microbenchmarks)
* An interference model to quantify I/O management interference: [quantification.py](interference_model/quantification.py)
* The ConfZNS++ emulator with support for management operations and zone mapping: [confznsplusplus](confznsplusplus) (submodule)
* The fio workload generator modified to support the finish and append management operations, and our own custom softfinish operation: [fio](tools/fio/)
* The ZINC I/O scheduler: [zinc-scheduler](zinc-scheduler) (submodule)

## Setup instructions for the artifact code

1. Ensure you have an OS that supports the codebase.
    All of our experiments utilize the `io_uring NVMe passthrough` functionality, which requires a modern Linux kernel (>6).
    Additionally, our scheduler is built on `Linux 6.3.8`, so we recommend using `Linux 6.3.8` of the Linux kernel for reproducability. If not available, it is valid to run the codebase in an emulator, e.g., QEMU.

2. Clone the repository including its submodules/dependencies

    ```bash
    git clone --recurse-submodules https://github.com/stonet-research/systor-confznsplusplus-artifact.git
    ```

3. Install a local version of fio (needed for all benchmarks!):

    ```bash
    pushd tools/fio
    ./configure
    make -j 
    popd
    # If you want to see the changes made to fio, see `tools/fio.4a0c766.path`. These changes can be applied directly to a fio checked out to commit 4a0c766.
    ```

4. Setup plotting/interference model requirements

    Both our interference model and our plotting scripts use Python. The interference model and `plot.py` scripts have the requirements specified in `requirements.txt`, the notebooks have the requirements specified in `requirements-jupyter.txt`.
    Install the dependencies with:

    ```bash
    pip3 install -r requirements.txt
    pip3 install -r requirements-jupyter.txt # only needed for the plotting notebooks
    ```

5. Setup ZINC

    Note, building ZINC is not necessary for the interference study or for the ConfZNSplusplus results!
    In order to install ZINC follow the install instructions in [zinc-scheduler/README.md](zinc-scheduler/README.md).

6. Setup ConfZNS++

    Note, building ConfZNS++ is not necessary for the interference study or for the ZINC results!

    ```bash
    cd confznsplusplus
    cp ../femu-scripts/femu-copy-scripts.sh .
    ./femu-copy-scripts.sh .
    # only Debian/Ubuntu based distributions supported
    sudo ./pkgdep.sh
    ./femu-compile.sh
    ```

## Reproduce the zns-interference-study experiments (Motivation)

In order to run our micro benchmarks for one namespace, change the directory to `./benchmarks/passthrough-zns-command-interference/microbenchmarks/one-namespace`.
For each type of interference benchmark there is a separate dir, for example "finish on reset interference" is in `finish-on-reset-interference`. Running a benchmark is equal to:

```bash
# Run the benchmark
./bench nvmexny 
# Get the data of the benchmark
cat data/*
# Plot the data of the benchmarks and get the interference value ($Z^{Inter}$) of our model
python3 ./plot.py
```

For experiments with `finish` it is necessary to specify the amount of zones that will be used for finishing zones.
We recommend setting this to ~30% of the zones. We picked the number of zones with the following reasoning:

```
For the evaluated SSDs finish commands are completed at ~1 finish/sec. With a 50% rate limit we can do 1 finish every 2 seconds 
and for benchmarks we try to run for 10 minutes (10*60/2) = 300 and peak write bandwidth is 1.2GB/s = ~1 zone so within 10 
minutes we can fill (10*60) = 600 and we have a total of 904 zones
```

## Reproduce the host-managed solutions experiments

### Softfinish

All benchmarks and data are in [`./benchmarks/passthrough-zns-command-interference/microbenchmarks`](./benchmarks/passthrough-zns-command-interference/microbenchmarks) and have the name `*softfinish*`. `softfinish-bench` runs softfinish in isolation. `softfinish-on-x` are the interference experiments similar to the motivation section.

### ZINC

1. First ensure that the `zinc.ko` module is installed (`sudo insmod zinc.ko`, see [zinc-scheduler/README.md](zinc-scheduler/README.md)).

2. Run the benchmarks in [`benchmarks/scheduler-benchmarks/microbenchmarks`](./benchmarks/scheduler-benchmarks/microbenchmarks/). It contains the following benchmarks:
    * `zinc-configuration`: The scripts needed to get the optimal configuration for ZINC. Run `./bench` to see what arguments to use to run the benchmarks. The data is in `data/`, where `baseline-data` holds the data without interference, and `data-reset_time_*_write_ratio_*` holds data for various ZINC configurations. Run `plot.py` to get the plots.
    * `zinc-cpu-usage`: used to measure the CPU usage compared to mq-deadline. Run `./bench`.
    * `optimal-reset-on-write`: reproduce the interference plot from the motivation for ZINC and mq-deadline. Run with `./bench`.

## Reproduce the ConfZNS++ results

We exposed the configurations we used with ConfZNS++ in [confznplusplus-config.sh](confznplusplus-config.sh).
Please modify this script as needed for your local install (e.g., change the VM path).
All benchmarks and data that used ConfZNS++ are in [`./benchmarks/passthrough-zns-command-interference/microbenchmarks`](./benchmarks/passthrough-zns-command-interference/microbenchmarks) and have the name `conznsplusplus-*-final-configuration`.

## Reproduce the Plots

The [`paperplots notebook`](./plotting-notebooks/paperplots.ipynb) contains all plotting scripts, with the respective data, for all figures used in the paper.

## Directory Structure

This repository is broken down into several distinct directories and subdirectories, which are organized as follows:

* [`interference_model`](./interference_model/) contains the python lib of the presented quantification model, to be imported into data parsing scripts to calculate the $Z^{Inter}$ value.
* [`plotting-notebooks`](./plotting-notebooks/) contains all plotting scripts, as jupyter notebooks, for generating figures.
* [`confznsplusplus`](./confznsplusplus): contains the source code of ConZNSplusplus
* [`tools`](./tools/) contains the custom `fio` repositories for generating all benchmarks of this study.
* [`benchmarks/scheduler-benchmarks`](./benchmarks/scheduler-benchmarks/) contains all the benchmarking scripts and collected data for the benchmarks using a scheduler. It contains benchmarks with ZINC and/or mq-deadline.
* [`zinc-scheduler`](./zinc-scheduler/) contains the source code of ZINC.
* [`benchmarks/passthrough-zns-command-interference`](./benchmarks/passthrough-zns-command-interference) contains all interference workloads run throughout the study. Each workload has its own subdirectory, with a benchmarking script to run the workload (run `./bench nvme0n2` on the respective device), all our collected data sets, and each workload has a plotting script to generate standalone figures apart from the paper figures (run `python3 plot.py`).
* [`util`](./util/) contains utility scripts used throughout this study, which are typically called from other benchmarking scripts.

## Cite
Krijn Doekemeijer, Dennis Maisenbacher, Zebin Ren, Nick Tehrany, Matias Bjørling, and Animesh Trivedi. 2024. Exploring I/O Management Performance in ZNS with ConfZNS++. In Proceedings of the 17th ACM International Systems and Storage Conference (SYSTOR '24). Association for Computing Machinery, New York, NY, USA, 162–177. https://doi.org/10.1145/3688351.3689160

```
@inproceedings{2024-systor-confzsnplusplus,
author = {Doekemeijer, Krijn and Maisenbacher, Dennis and Ren, Zebin and Tehrany, Nick and Bj\o{}rling, Matias and Trivedi, Animesh},
title = {Exploring I/O Management Performance in ZNS with ConfZNS++},
year = {2024},
isbn = {9798400711817},
publisher = {Association for Computing Machinery},
address = {New York, NY, USA},
url = {https://doi.org/10.1145/3688351.3689160},
doi = {10.1145/3688351.3689160},
abstract = {Flash-based storage is known to suffer from performance unpredictability due to interference between host-issued I/O and device-side I/O management. SSDs with data placement capabilities, such as Zoned Namespaces (ZNS) and Flexible Data Placement (FDP), expose selective device-side I/O management operations to the host to provide predictable performance. In this paper, we demonstrate that these host-issued I/O management operations lead to performance interference with host-issued I/O. Indeed, we find that the I/O management operations introduced by ZNS and FDP create I/O interference, leading to significant performance losses. Despite the performance implications, we observe that ZNS research frequently uses emulators (over 20 recently published papers), but no emulator currently has function-realistic models for I/O management. To address this gap, we identify ten ZNS I/O management designs, explain how they interfere with I/O, and introduce ConfZNS++, a function-realistic emulator with native I/O management support, providing future research with the capability to explore these designs. Additionally, we introduce two actionable host-managed solutions to reduce ZNS management interference: ZINC, an I/O scheduler prioritizing I/O over I/O management, and the softfinish operation, a host-managed implementation of the finish operation. In our experiments, ZINC reduces reset interference by 56.9\%, and softfinish reduces finish interference by 50.7\%.},
booktitle = {Proceedings of the 17th ACM International Systems and Storage Conference},
pages = {162–177},
numpages = {16},
keywords = {Emulation, Interference, NVMe Flash Storage, ZNS},
location = {Virtual, Israel},
series = {SYSTOR '24}
}
```
