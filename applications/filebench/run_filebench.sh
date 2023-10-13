#!/bin/bash

# Move to current dir
scriptdir=$(cd $(dirname "$0") && pwd)

filebenchdir="/mnt/filebench"
filebenchbinary="setarch `arch` --addr-no-randomize $scriptdir/filebench/filebench"
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
echo mq-deadline | sudo tee "/sys/block/$2/queue/scheduler"
sudo mkfs.f2fs -f -m -c $devzns $devnvmei || exit
sudo mkdir -p "$filebenchdir" || exit 1
sudo mount -t f2fs $devnvme "$filebenchdir" || exit 1

mkdir -p "$resultdir"

case $workload in
  *"varmail"*)
    sudo $filebenchbinary -f "varmail_custom.f" 1> "$resultdir/varmail-$(date +%s).out" 2> "$resultdir/varmail-$(date +%s).err";
    sudo cat /sys/kernel/debug/f2fs/status >  "$resultdir/varmail-f2fs-info-$(date +%s).out";
    for i in $(sudo find /sys/fs/f2fs/$1 -type f); do echo $i=$(sudo cat $i); done | sudo tee -a "$resultdir/varmail-f2fs-info-$(date +%s).out";
    for i in $(sudo find /sys/fs/f2fs/$1/stat -type f); do echo $i=$(sudo cat $i); done | sudo tee -a "$resultdir/varmail-f2fs-info-$(date +%s).out";
    ;;
  *"webserver"*)
    sudo $filebenchbinary -f "webserver_custom.f" 1> "$resultdir/webserver-$(date +%s).out" 2> "$resultdir/webserver-$(date +%s).err";
    sudo cat /sys/kernel/debug/f2fs/status >  "$resultdir/webserver-f2fs-info-$(date +%s).out";
    for i in $(sudo find /sys/fs/f2fs/$1 -type f); do echo $i=$(sudo cat $i); done | sudo tee -a "$resultdir/webserver-f2fs-info-$(date +%s).out";
    for i in $(sudo find /sys/fs/f2fs/$1/stat -type f); do echo $i=$(sudo cat $i); done | sudo tee -a "$resultdir/webserver-f2fs-info-$(date +%s).out";
    ;;
  *"fileserver"*)
    sudo $filebenchbinary -f "fileserver_custom.f" 1> "$resultdir/fileserver-$(date +%s).out" 2> "$resultdir/fileserver-$(date +%s).err";
    sudo cat /sys/kernel/debug/f2fs/status >  "$resultdir/fileserver-f2fs-info-$(date +%s).out";
    for i in $(sudo find /sys/fs/f2fs/$1 -type f); do echo $i=$(sudo cat $i); done | sudo tee -a "$resultdir/fileserver-f2fs-info-$(date +%s).out";
    for i in $(sudo find /sys/fs/f2fs/$1/stat -type f); do echo $i=$(sudo cat $i); done | sudo tee -a "$resultdir/fileserver-f2fs-info-$(date +%s).out";
    ;;
  *) echo "UNKNOWN WORKLOAD";;
esac

