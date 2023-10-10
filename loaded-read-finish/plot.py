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

    queue_depths = np.arange(1, 9)

    read100 = [None] * len(queue_depths)
    read100_iops = [None] * len(queue_depths)
    read99 = [None] * len(queue_depths)
    read99_iops = [None] * len(queue_depths)
    read95 = [None] * len(queue_depths)
    read95_iops = [None] * len(queue_depths)
    read90 = [None] * len(queue_depths)
    read90_iops = [None] * len(queue_depths)
    read75 = [None] * len(queue_depths)
    read75_iops = [None] * len(queue_depths)
    read50 = [None] * len(queue_depths)
    read50_iops = [None] * len(queue_depths)
    read25 = [None] * len(queue_depths)
    read25_iops = [None] * len(queue_depths)

    for key, value in data.items():
        if "bw" in key:
            continue
        x = int(math.log2(int(value["jobs"][1]["job options"]["iodepth"])))
        if 'rflow_100' in key:
            read100[x] = value["jobs"][1]["read"]["lat_ns"]["percentile"]["95.000000"]/1000
            read100_iops[x] = value["jobs"][1]["read"]["iops_mean"]/1000
        elif 'rflow_99' in key:
            read99[x] = value["jobs"][1]["read"]["lat_ns"]["percentile"]["95.000000"]/1000
            read99_iops[x] = value["jobs"][1]["read"]["iops_mean"]/1000
        elif 'rflow_95' in key:
            read95[x] = value["jobs"][1]["read"]["lat_ns"]["percentile"]["95.000000"]/1000
            read95_iops[x] = value["jobs"][1]["read"]["iops_mean"]/1000
        elif 'rflow_90' in key:
            read90[x] = value["jobs"][1]["read"]["lat_ns"]["percentile"]["95.000000"]/1000
            read90_iops[x] = value["jobs"][1]["read"]["iops_mean"]/1000
        elif 'rflow_75' in key:
            read75[x] = value["jobs"][1]["read"]["lat_ns"]["percentile"]["95.000000"]/1000
            read75_iops[x] = value["jobs"][1]["read"]["iops_mean"]/1000
        elif 'rflow_50' in key:
            read50[x] = value["jobs"][1]["read"]["lat_ns"]["percentile"]["95.000000"]/1000
            read50_iops[x] = value["jobs"][1]["read"]["iops_mean"]/1000
        elif 'rflow_25' in key:
            read25[x] = value["jobs"][1]["read"]["lat_ns"]["percentile"]["95.000000"]/1000
            read25_iops[x] = value["jobs"][1]["read"]["iops_mean"]/1000

    fig, ax = plt.subplots()

    ax.plot(read100_iops, read100, markersize = 4, marker = '>', label="   0% finish")
    ax.plot(read99_iops, read99, markersize = 4, marker = 'x',   label="   1% finish")
    ax.plot(read95_iops, read95, markersize = 4, marker = 'o',   label="   5% finish")
    ax.plot(read90_iops, read90, markersize = 4, marker = '<',   label=" 10% finish")
    ax.plot(read75_iops, read75, markersize = 4, marker = '^',   label=" 25% finish")
    ax.plot(read50_iops, read50, markersize = 4, marker = '*',   label=" 50% finish")
    # ax.plot(read25_iops, read25, markersize = 4, marker = 'p',   label=" 75% finish")

    fig.tight_layout()
    ax.grid(which='major', linestyle='dashed', linewidth='1')
    ax.set_axisbelow(True)
    # ax.legend(loc='best', handles=handles)
    ax.legend(loc='upper left')
    ax.set_ylim(bottom=0, top=2250)
    ax.set_xlim(left=0)
    ax.set_ylabel("p95 read Latency (usec)")
    ax.set_xlabel("Total IOPS (x1000)")
    plt.savefig(f"{file_path}/loaded_read_latency.pdf", bbox_inches="tight")
    plt.savefig(f"{file_path}/loaded_read_latency.png", bbox_inches="tight")
    plt.clf()
