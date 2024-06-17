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

    write100 = [None] * len(queue_depths)
    write100_iops = [None] * len(queue_depths)
    write50_8 = [None] * len(queue_depths)
    write50_8_iops = [None] * len(queue_depths)
    write50_16 = [None] * len(queue_depths)
    write50_16_iops = [None] * len(queue_depths)
    write50_32 = [None] * len(queue_depths)
    write50_32_iops = [None] * len(queue_depths)
    write50_256 = [None] * len(queue_depths)
    write50_256_iops = [None] * len(queue_depths)

    for key, value in data.items():
        if "bw" in key:
            continue
        numjobs = int(re.search(r'\d+', key).group())
        y = 0
        if not numjobs in [1, 2, 3, 4, 5, 6, 7]:
            continue     
        while queue_depths[y] is not numjobs:
            y = y + 1
        x = y
        print(x,y)
        # if numjobs > 7:
        #     continue # We skip 14 as it turns out we were bottlenecked by not enough cpu cores, giving inaccurate results
        # else:
        #     x = numjobs - 1
        if 'wflow_100' in key:
            write100[x] = value["jobs"][0]["write"]["lat_ns"]["percentile"]["95.000000"]/1000
            write100_iops[x] = value["jobs"][0]["write"]["iops_mean"]/1000
        elif '-8' in key:
            write50_8[x] = value["jobs"][0]["write"]["lat_ns"]["percentile"]["95.000000"]/1000
            write50_8_iops[x] = value["jobs"][0]["write"]["iops_mean"]/1000
        elif '-16' in key:
            write50_16[x] = value["jobs"][0]["write"]["lat_ns"]["percentile"]["95.000000"]/1000
            write50_16_iops[x] = value["jobs"][0]["write"]["iops_mean"]/1000
        elif '-32' in key:
            write50_32[x] = value["jobs"][0]["write"]["lat_ns"]["percentile"]["95.000000"]/1000
            write50_32_iops[x] = value["jobs"][0]["write"]["iops_mean"]/1000
        elif '-256' in key:
            write50_256[x] = value["jobs"][0]["write"]["lat_ns"]["percentile"]["95.000000"]/1000
            write50_256_iops[x] = value["jobs"][0]["write"]["iops_mean"]/1000
    # print(f"Interference RMS 0% - 50% {get_interference_rms(write100_iops, write50_iops, write100, write50)}")

    fig, ax = plt.subplots()

    ax.plot(write100_iops, write100, markersize = 4, marker = '>', label="   0% finish")
    ax.plot(write50_256_iops, write50_256, markersize = 4, marker = '*',   label=" 50% finish-256KiB")
    ax.plot(write50_32_iops, write50_32, markersize = 4, marker = '*',   label=" 50% finish-32KiB")
    ax.plot(write50_16_iops, write50_16, markersize = 4, marker = '*',   label=" 50% finish-16KiB")
    ax.plot(write50_8_iops, write50_8, markersize = 4, marker = '*',   label=" 50% finish-8KiB")


    print(write100_iops, write100)
    print(write50_8_iops, write50_8)
    print(write50_16_iops, write50_16)
    print(write50_32_iops, write50_32)
    print(write50_256_iops, write50_256)

    fig.tight_layout()
    ax.grid(which='major', linestyle='dashed', linewidth='1')
    ax.set_axisbelow(True)
    # ax.legend(loc='best', handles=handles)
    ax.legend(loc='best')
    ax.set_ylim(bottom=0, top=6000)
    ax.set_xlim(left=0, right=10)
    ax.set_ylabel("p95 write Latency (usec)")
    ax.set_xlabel("Total IOPS (x1000)")
    plt.savefig(f"{file_path}/loaded_write_latency.pdf", bbox_inches="tight")
    plt.savefig(f"{file_path}/loaded_write_latency.png", bbox_inches="tight")
    plt.clf()
