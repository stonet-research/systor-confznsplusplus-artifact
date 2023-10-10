## Setup

Build fio

```bash
git submodule update --init --recursive
cd fio
./configure
make -j
```

## TODO:

 -[ ] we modified the fio json output to use finish instead of write, make sure all scripts still parse the data correctly.