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

    queue_depths = [1, 2, 3, 4, 5, 6, 7]

    soft0 = [None] * len(queue_depths)
    soft0_iops = [None] * len(queue_depths)
    soft8 = [None] * len(queue_depths)
    soft8_iops = [None] * len(queue_depths)    
    soft16 = [None] * len(queue_depths)
    soft16_iops = [None] * len(queue_depths)       
    soft32 = [None] * len(queue_depths)
    soft32_iops = [None] * len(queue_depths)        
    soft64 = [None] * len(queue_depths)
    soft64_iops = [None] * len(queue_depths)
    soft128 = [None] * len(queue_depths)
    soft128_iops = [None] * len(queue_depths)
    soft256 = [None] * len(queue_depths)
    soft256_iops = [None] * len(queue_depths)
    soft512 = [None] * len(queue_depths)
    soft512_iops = [None] * len(queue_depths)


    for key, value in data.items():
        if "bw" in key:
            continue
        numjobs = int(re.search(r'\d+', key).group())
        y = 0
        if not numjobs in [1, 2,3, 4,5,6, 7]:
            continue     
        while queue_depths[y] is not numjobs:
            y = y + 1
        x = y
        print(x,y)
        # if numjobs > 7:
        #     continue # We skip 14 as it turns out we were bottlenecked by not enough cpu cores, giving inaccurate results
        # else:
        #     x = numjobs - 1
        print(key)
        if 'soft_0' in key:
            soft0[x] = value["jobs"][1]["finish"]["lat_ns"]["percentile"]["95.000000"]/1000
            soft0_iops[x] = value["jobs"][1]["finish"]["iops_mean"]
        elif 'soft_8' in key:
            soft8[x] = value["jobs"][1]["write"]["lat_ns"]["percentile"]["95.000000"]/1000
            soft8_iops[x] = value["jobs"][1]["write"]["iops_mean"]
        elif 'soft_16' in key:
            soft16[x] = value["jobs"][1]["write"]["lat_ns"]["percentile"]["95.000000"]/1000
            soft16_iops[x] = value["jobs"][1]["write"]["iops_mean"]     
        elif 'soft_32' in key:
            soft32[x] = value["jobs"][1]["write"]["lat_ns"]["percentile"]["95.000000"]/1000
            soft32_iops[x] = value["jobs"][1]["write"]["iops_mean"]     
        elif 'soft_64' in key:
            soft64[x] = value["jobs"][1]["write"]["lat_ns"]["percentile"]["95.000000"]/1000
            soft64_iops[x] = value["jobs"][1]["write"]["iops_mean"]
        elif 'soft_128' in key:
            soft128[x] = value["jobs"][1]["write"]["lat_ns"]["percentile"]["95.000000"]/1000
            soft128_iops[x] = value["jobs"][1]["write"]["iops_mean"]
        elif 'soft_256' in key:
            soft256[x] = value["jobs"][1]["write"]["lat_ns"]["percentile"]["95.000000"]/1000
            soft256_iops[x] = value["jobs"][1]["write"]["iops_mean"]
        elif 'soft_512' in key:
            soft512[x] = value["jobs"][1]["write"]["lat_ns"]["percentile"]["95.000000"]/1000
            soft512_iops[x] = value["jobs"][1]["write"]["iops_mean"]

    # print(f"Interference RMS 0% - 50% {get_interference_rms(write100_iops, write50_iops, write100, write50)}")

    GREEN = "#117733"
    TEAL  = "#44AA99"
    CYAN = "#88CCEE"
    OLIVE = "#999933"
    SAND = "#DDCC77"
    ROSE   = "#CC6677"
    BLUE = "#88CCEE"
    MAGENTA = "#AA4499"
    GREY = GRAY = "#DDDDDD"

    colors    = ["#000000", CYAN, MAGENTA, OLIVE, ROSE, GREEN]

    fig, ax = plt.subplots()

    print(soft0_iops, soft0)
    print(soft16_iops, soft16)
    print(soft32_iops, soft32)
    print(soft512_iops, soft512)

    ax.plot(soft0_iops, soft0, markersize = 4, marker='x', linestyle='--',linewidth=2, label="Device", color='black')
    ax.plot(soft16_iops, soft16, markersize = 4, marker = '>', linewidth=2,label="Soft-8KiB", color=OLIVE)
    ax.plot(soft32_iops, soft32, markersize = 4, marker = 'o', linewidth=2,label="Soft-16KiB", color=BLUE)
    # ax.plot(soft64_iops, soft64, markersize = 4, marker = 'x',   label="   Soft-64")
    # ax.plot(soft128_iops, soft128, markersize = 4, marker = 'o',   label="   Soft-128")
    # ax.plot(soft256_iops, soft256, markersize = 4, marker = '<',   label="  Soft-256")
    ax.plot(soft512_iops, soft512, markersize = 4, marker = '<', linewidth=2, label="Soft-256KiB",color=ROSE)

    fig.tight_layout()
    ax.grid(which='major', linestyle='dashed', linewidth='1')
    ax.set_axisbelow(True)
    # ax.legend(loc='best', handles=handles)
    ax.legend(loc='upper left')
    ax.set_ylim(bottom=0)
    ax.set_xlim(left=1.8,right=2.1)

    # ax.xaxis.set_ticks(np.arange(0, 175+25, 25))
    # ax.yaxis.set_ticks(np.arange(0, 350+50, 50))

    ax.set_ylabel("P95 latency (µs)")
    ax.set_xlabel("Throughput (KIOPS)")
    plt.savefig(f"{file_path}/loaded_write_latency2.pdf", bbox_inches="tight")
    plt.savefig(f"{file_path}/loaded_write_latency2.png", bbox_inches="tight")
    plt.clf()
