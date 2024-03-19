#!/bin/bash

DEBUG_FIO=1 ./append-on-finish-interference/bench nvme1n2 300
DEBUG_FIO=1 ./append-on-read-interference/bench nvme1n2 300
DEBUG_FIO=1 ./append-on-reset-interference/bench nvme1n2 300
DEBUG_FIO=1 ./append-on-write-interference/bench nvme1n2 300
DEBUG_FIO=1 ./finish-on-append-interference/bench nvme1n2 300
DEBUG_FIO=1 ./finish-on-read-interference/bench nvme1n2 300
DEBUG_FIO=1 ./finish-on-write-interference/bench nvme1n2 300
DEBUG_FIO=1 ./read-on-append-interference/bench nvme1n2 300
DEBUG_FIO=1 ./read-on-finish-interference/bench nvme1n2 300
DEBUG_FIO=1 ./read-on-reset-interference/bench nvme1n2
DEBUG_FIO=1 ./reset-on-append-interference/bench nvme1n2
DEBUG_FIO=1 ./reset-on-read-interference/bench nvme1n2
DEBUG_FIO=1 ./reset-on-write-interference/bench nvme1n2
DEBUG_FIO=1 ./write-on-append-interference/bench nvme1n2
DEBUG_FIO=1 ./write-on-finish-interference/bench nvme1n2 300
DEBUG_FIO=1 ./write-on-reset-interference/bench nvme1n2
DEBUG_FIO=1 ./write-on-reset-interference-with-concurrent-resets/bench nvme1n2 
