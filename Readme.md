## Setup

Build fio

```bash
git submodule update --init --recursive
cd fio
./configure
make -j
```

## TODO:

 - [ ] we modified the fio json output to use finish instead of write, make sure all scripts still parse the data correctly.
 - [ ] zinc install instructions + submodule for it, maybe rename this repo to ZINCbench or so.
 - [ ] write on reset does not have the fio bug where "write" is replaced with "finish" hence plotting won't work on new data

 ## TODO for ZINC Configuration benchmark
 - [ ] Rerun the reset baseline for 50% reset limit without io_uring_cmd, we want io_uring with none, as this is needed to compare with the schedulers (and so we get the clat in fio)
 - [ ] TODO: UNCOMMENT THE SKIPPED RUNS ONCE ALL DONE in zinc-configuration bench, ALL MARKED WITH TODO (do global TODO search as well)
 - [ ] Update the gamma and delta in zinc config parsing from ZenFS
 - [ ] Update parsing to use clat_ns once the reset 50% baseline is rerun with io_uring