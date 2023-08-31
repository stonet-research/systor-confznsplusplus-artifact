#! /usr/bin/python3

import os
import re
import glob
import json
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
        with open(file, 'r') as f:
            for index, line in enumerate(f, 1):
                # Removing all fio logs in json file by finding first {
                if len(line.split()) == 0:
                    continue
                if line.split()[0] == "{":
                    rows = f.readlines()
                    with open(os.path.join(os.getcwd(), "temp.json"), 'w+') as temp:
                        temp.write(line)
                        temp.writelines(rows)
                    break

        with open(os.path.join(os.getcwd(), "temp.json"), 'r') as temp:
            data[file] = dict()
            data[file] = json.load(temp)
            os.remove(os.path.join(os.getcwd(), "temp.json"))

    return 1

if __name__ == "__main__":
    file_path = '/'.join(os.path.abspath(__file__).split('/')[:-1])

    data = dict()
    parse_fio_data(f"{file_path}/data", data)

    queue_depths = [1, 2, 4, 8, 16, 32, 64, 128]

    reset100 = [None] * len(queue_depths)
    reset100_iops = [None] * len(queue_depths)
    reset99 = [None] * len(queue_depths)
    reset99_iops = [None] * len(queue_depths)
    reset95 = [None] * len(queue_depths)
    reset95_iops = [None] * len(queue_depths)
    reset90 = [None] * len(queue_depths)
    reset90_iops = [None] * len(queue_depths)
    reset75 = [None] * len(queue_depths)
    reset75_iops = [None] * len(queue_depths)
    reset50 = [None] * len(queue_depths)
    reset50_iops = [None] * len(queue_depths)

    for key, value in data.items():
        if "bw" in key:
            continue
        numjobs = int(re.search(r'\d+', key).group())
        if 'tflow_100' in key:
            reset100[int(math.log2(int(numjobs)))] = value["jobs"][1]["ZNS Reset"]["lat_ns"]["percentile"]["95.000000"]/1000/1000
            reset100_iops[int(math.log2(int(numjobs)))] = value["jobs"][1]["ZNS Reset"]["iops_mean"]
        elif 'tflow_99' in key:
            reset99[int(math.log2(int(numjobs)))] = value["jobs"][1]["ZNS Reset"]["lat_ns"]["percentile"]["95.000000"]/1000/1000
            reset99_iops[int(math.log2(int(numjobs)))] = value["jobs"][1]["ZNS Reset"]["iops_mean"]
        elif 'tflow_95' in key:
            reset95[int(math.log2(int(numjobs)))] = value["jobs"][1]["ZNS Reset"]["lat_ns"]["percentile"]["95.000000"]/1000/1000
            reset95_iops[int(math.log2(int(numjobs)))] = value["jobs"][1]["ZNS Reset"]["iops_mean"]
        elif 'tflow_90' in key:
            reset90[int(math.log2(int(numjobs)))] = value["jobs"][1]["ZNS Reset"]["lat_ns"]["percentile"]["95.000000"]/1000/1000
            reset90_iops[int(math.log2(int(numjobs)))] = value["jobs"][1]["ZNS Reset"]["iops_mean"]
        elif 'tflow_75' in key:
            reset75[int(math.log2(int(numjobs)))] = value["jobs"][1]["ZNS Reset"]["lat_ns"]["percentile"]["95.000000"]/1000/1000
            reset75_iops[int(math.log2(int(numjobs)))] = value["jobs"][1]["ZNS Reset"]["iops_mean"]
        elif 'tflow_50' in key:
            reset50[int(math.log2(int(numjobs)))] = value["jobs"][1]["ZNS Reset"]["lat_ns"]["percentile"]["95.000000"]/1000/1000
            reset50_iops[int(math.log2(int(numjobs)))] = value["jobs"][1]["ZNS Reset"]["iops_mean"]

    fig, ax = plt.subplots()

    ax.plot(reset100_iops, reset100, markersize=6, marker='x', label="100% reset")
    ax.plot(reset99_iops, reset99, markersize=6, marker='o', label="  99% reset")
    ax.plot(reset95_iops, reset95, markersize=6, marker='*', label="  95% reset")
    ax.plot(reset90_iops, reset90, markersize=6, marker='<', label="  90% reset")
    ax.plot(reset75_iops, reset75, markersize=6, marker='+', label="  75% reset")
    ax.plot(reset50_iops, reset50, markersize=6, marker='^', label="  50% reset")

    fig.tight_layout()
    ax.grid(which='major', linestyle='dashed', linewidth='1')
    ax.set_axisbelow(True)
    # ax.legend(loc='best', handles=handles)
    ax.legend(loc='best')
    ax.set_ylim(bottom=0)
    # ax.set_xlim(left=0)
    ax.set_ylabel("p95 Reset Latency (msec)")
    ax.set_xlabel("Total IOPS")
    plt.savefig(f"{file_path}/loaded_reset_latency.pdf", bbox_inches="tight")
    plt.savefig(f"{file_path}/loaded_reset_latency.png", bbox_inches="tight")
    plt.clf()


    reset_iops = [reset50_iops[0], reset75_iops[0], reset90_iops[0], reset95_iops[0], reset99_iops[0], reset100_iops[0]]
    reset_lat = [reset50[0], reset75[0], reset90[0], reset95[0], reset99[0], reset100[0]]
    x = ["50", "75", "90", "95", "99", "100"]

    fig, ax = plt.subplots()

    ax.bar(np.arange(1,7), reset_iops)

    fig.tight_layout()
    ax.grid(which='major', linestyle='dashed', linewidth='1')
    ax.set_axisbelow(True)
    # ax.legend(loc='best', handles=handles)
    # ax.legend(loc='best')
    ax.set_ylim(bottom=0)
    ax.set_xticks(np.arange(1,7), x)
    # ax.set_xlim(left=0)
    ax.set_ylabel("Total IOPS")
    ax.set_xlabel("Reset Rate (%)")
    plt.savefig(f"{file_path}/reset_iops.pdf", bbox_inches="tight")
    plt.savefig(f"{file_path}/reset_iops.png", bbox_inches="tight")
    plt.clf()

    fig, ax = plt.subplots()

    ax.bar(np.arange(1,7), reset_lat)

    fig.tight_layout()
    ax.grid(which='major', linestyle='dashed', linewidth='1')
    ax.set_axisbelow(True)
    # ax.legend(loc='best', handles=handles)
    # ax.legend(loc='best')
    ax.set_ylim(bottom=0)
    ax.set_xticks(np.arange(1,7), x)
    # ax.set_xlim(left=0)
    ax.set_ylabel("p95 reset latency (msec)")
    ax.set_xlabel("Reset Rate (%)")
    plt.savefig(f"{file_path}/reset_lat.pdf", bbox_inches="tight")
    plt.savefig(f"{file_path}/reset_lat.png", bbox_inches="tight")
    plt.clf()
