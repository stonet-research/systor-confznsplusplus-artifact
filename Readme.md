## Setup

Build fio

```bash
pushd tools/fio
./configure
make -j
popd

pushd tools/rocksdb
DEBUG_LEVEL=0 ROCKSDB_PLUGINS=zenfs make -j 4 db_bench
sudo DEBUG_LEVEL=0 ROCKSDB_PLUGINS=zenfs make install
cd plugin/zenfs/util
make
popd
```

## TODO

- [ ] we modified the fio json output to use finish instead of write, make sure all scripts still parse the data correctly.
- [ ] zinc install instructions + submodule for it, maybe rename this repo to ZINCbench or so.
- [ ] write on reset does not have the fio bug where "write" is replaced with "finish" hence plotting won't work on new data

## TODO for ZINC Configuration benchmark

- [ ] Rerun the reset baseline for 50% reset limit without io_uring_cmd, we want io_uring with none, as this is needed to compare with the schedulers (and so we get the clat in fio)
- [ ] TODO: UNCOMMENT THE SKIPPED RUNS ONCE ALL DONE in zinc-configuration bench, ALL MARKED WITH TODO (do global TODO search as well)
- [ ] Update the gamma and delta in zinc config parsing from ZenFS
- [ ] Update parsing to use clat_ns once the reset 50% baseline is rerun with io_uring

## ZINC TODO

- [ ] Add zinc to this repo, will require to restructure this repo to have cleaner folders like the paper
- [ ] cleanup the zinc code, there's still copyrights from mq-deadline, we can remove these and state it uses mq-deadline code as base
