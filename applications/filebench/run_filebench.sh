#!/bin/bash

# Move to current dir
scriptdir=$(cd $(dirname "$0") && pwd)

filebenchdir="/mnt/filebench"
filebenchbinary="./filebench/filebench"
resultdir="./results"

if [ $# != 3 ]; then
    echo "Usage: nvme (shortname) zns (shortname) workload"
  exit 1
fi

devnvme="/dev/$1"
devzns="/dev/$2"
workload="$3"

# Unmount if needed
ismounted=$(mount | grep -i "$filebenchdir")
if [[ "$ismounted" == *"f2fs"* ]]; then
  echo "unmounting previous f2fs";
  sudo umount "$filebenchdir";
fi

# mkfs
sudo mkfs.f2fs -f -m -c $devzns $devnvmei || exit
sudo mkdir -p "$filebenchdir" || exit 1
sudo mount -t f2fs $devnvme "$filebenchdir" || exit 1

mkdir -p "$resultdir"

case $workload in
  *"varmail"*)
    sudo "$filebenchbinary" -f "varmail_custom.f" 1> "$resultdir/varmail-$(date +%s).out" 2> "$resultdir/varmail-$(date +%s).err"
    ;;
  *"webserver"*)
   sudo "$filebenchbinary" -f "webserver_custom.f" 1> "$resultdir/webserver-$(date +%s).out" 2> "$resultdir/webserver-$(date +%s).err"
    ;;
  *"fileserver"*)
   sudo "$filebenchbinary" -f "fileserver_custom.f" 1> "$resultdir/fileserver-$(date +%s).out" 2> "$resultdir/fileserver-$(date +%s).err"
    ;;
  *) echo "UNKNOWN WORKLOAD";;
esac

