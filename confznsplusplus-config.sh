#!/bin/sh
qemu=./confznsplusplus/build/x86_64-softmmu/qemu-system-x86_64 # << set to your Qemu installation!

image="./ubuntu-22.04.qcow2" # Set to your image!!!

# config
port_local=7777 # < Set to your desired port
port_image=22   # < Set to the exposed port on the image
memory=64G      # RAM
smp=20          # SMP

$qemu -name qemuzns                                                     \
        --enable-kvm                                                    \
        -m "$memory" -cpu host -smp "$smp"                              \
        -vnc :0                                                         \
        -hda "$image"                                                   \
        -net user,hostfwd=tcp::"$port_local"-:"$port_image",hostfwd=tcp::4420-:4420 \
        -net nic,model=virtio,macaddr=DE:AD:BE:EF:01:42,id=nic1  \
        -device virtio-net-pci,netdev=user0,id=nic1 \
        -netdev bridge,id=user0,br=br0,helper=$qemu/build/qemu-bridge-helper \
        -device vfio-pci,host=0000:89:00.0 \
        -device femu,devsz_mb=$((1024*8*12)),id=nvme0,femu_mode=3,queues=64,zns_zonesize=2147483648,zns_zonecap=$((1107296256)),zns_channels=4,zns_channels_per_zone=4,zns_ways=1,zns_ways_per_zone=1,zns_dies_per_chip=1,zns_planes_per_die=1,zns_page_write_latency=$((700000)),zns_page_read_latency=60000,zns_channel_transfer_latency=25000,zns_block_erasure_latency=3500000,zns_allow_partial_resets=1,zns_vtable_mode=0,zns_block_size_pages=768