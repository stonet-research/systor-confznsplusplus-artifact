#! /usr/bin/python3

import os
import re
import glob
import json
from pathlib import Path
import math
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as mpatches

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/../../../../')

from interference_model.quantification import get_interference_rms,get_emd

plt.rc('font', size=12)          # controls default text sizes
plt.rc('axes', titlesize=12)     # fontsize of the axes title
plt.rc('axes', labelsize=12)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=12)    # fontsize of the tick labels
plt.rc('ytick', labelsize=12)    # fontsize of the tick labels
plt.rc('legend', fontsize=12)    # legend fontsize

def parse_fio_data(data_path, data):
    if not os.path.exists(f'{data_path}') or \
            os.listdir(f'{data_path}') == []:
        print(f"No data in {data_path}")
        return 0

    for file in glob.glob(f'{data_path}/*'):
        if "bw" in file:
            continue
        with open(file, 'r') as f:
            for index, line in enumerate(f, 1):
                # Removing all fio logs in json file by finding first {
                if line.split() == []:
                    pass
                elif line.split()[0] == "{":
                    rows = f.readlines()
                    with open(os.path.join(os.getcwd(), "temp.json"), 'w+') as temp:
                        temp.write(line)
                        temp.writelines(rows)
                    break

        if Path(os.path.join(os.getcwd(), "temp.json")).exists(): 
            with open(os.path.join(os.getcwd(), "temp.json"), 'r') as temp:
                data[file] = dict()
                data[file] = json.load(temp)
                os.remove(os.path.join(os.getcwd(), "temp.json"))

    return 1

if __name__ == "__main__":
    file_path = '/'.join(os.path.abspath(__file__).split('/')[:-1])

    data = dict()
    parse_fio_data(f"{file_path}/data", data)

    queue_depths = [1,2,4,8,16,32,64]

    read100 = [None] * len(queue_depths)
    read100_iops = [None] * len(queue_depths)

    read50_256 = [None] * len(queue_depths)
    read50_256_iops = [None] * len(queue_depths)
    read50_32 = [None] * len(queue_depths)
    read50_32_iops = [None] * len(queue_depths)
    read50_16 = [None] * len(queue_depths)
    read50_16_iops = [None] * len(queue_depths)
    read50_8 = [None] * len(queue_depths)
    read50_8_iops = [None] * len(queue_depths)

    for key, value in data.items():
        if "bw" in key:
            continue
        x = (int(value["jobs"][1]["job options"]["iodepth"]))
        print('depth', x)
        if not x in [1,2,4,8,16,32,64]:
                continue
        y = 0
        while queue_depths[y] is not x:
            y = y + 1
        print(x,y)
        x = y
        if 'rflow_100' in key:
            read100[x] = value["jobs"][1]["read"]["lat_ns"]["percentile"]["95.000000"]/1000
            read100_iops[x] = value["jobs"][1]["read"]["iops_mean"]/1000
        elif '-256' in key:
            read50_256[x] = value["jobs"][1]["read"]["lat_ns"]["percentile"]["95.000000"]/1000
            read50_256_iops[x] = value["jobs"][1]["read"]["iops_mean"]/1000
        elif '-32' in key:
            read50_32[x] = value["jobs"][1]["read"]["lat_ns"]["percentile"]["95.000000"]/1000
            read50_32_iops[x] = value["jobs"][1]["read"]["iops_mean"]/1000
        elif '-16' in key:
            read50_16[x] = value["jobs"][1]["read"]["lat_ns"]["percentile"]["95.000000"]/1000
            read50_16_iops[x] = value["jobs"][1]["read"]["iops_mean"]/1000
        elif '-8' in key:
            read50_8[x] = value["jobs"][1]["read"]["lat_ns"]["percentile"]["95.000000"]/1000
            read50_8_iops[x] = value["jobs"][1]["read"]["iops_mean"]/1000

    # print(f"Interference RMS 0% - 50% {get_interference_rms(read100_iops, read50_iops, read100, read50)}")

    fig, ax = plt.subplots()

    ax.plot(read100_iops, read100, markersize = 4, marker = '>', label="   0% finish")
    ax.plot(read50_256_iops, read50_256, markersize = 4, marker = '*',   label=" 50% finish-256KiB")
    ax.plot(read50_32_iops, read50_32, markersize = 4, marker = '*',   label=" 50% finish-32KiB")
    ax.plot(read50_16_iops, read50_16, markersize = 4, marker = '*',   label=" 50% finish-16KiB")
    ax.plot(read50_8_iops, read50_8, markersize = 4, marker = '*',   label=" 50% finish-8KiB")

    print(read100_iops, read100)
    print(read50_256_iops, read50_256)
    print(read50_32_iops, read50_32)
    print(read50_16_iops, read50_16)
    print(read50_8_iops, read50_8)

    fig.tight_layout()
    ax.grid(which='major', linestyle='dashed', linewidth='1')
    ax.set_axisbelow(True)
    # ax.legend(loc='best', handles=handles)
    ax.legend(loc='upper right')
    ax.set_ylim(bottom=0, top=6000)
    ax.set_xlim(left=0, right=60)
    ax.set_ylabel("p95 read Latency (usec)")
    ax.set_xlabel("Total IOPS (x1000)")
    plt.savefig(f"{file_path}/loaded_read_latency.pdf", bbox_inches="tight")
    plt.savefig(f"{file_path}/loaded_read_latency.png", bbox_inches="tight")
    plt.clf()
