#! /usr/bin/python3

import os
import re
import glob
import json
from pathlib import Path
import math
import matplotlib.pyplot as plt
import numpy as np
from numpy import sin
import matplotlib.patches as mpatches

from numpy import arange
from pandas import read_csv
from scipy.optimize import curve_fit
from matplotlib import pyplot

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

# define the true objective function for curve fitting
def objective(x, a, b, c, d):
 return a * sin(b - x) + c * x**2 + d

if __name__ == "__main__":
    file_path = '/'.join(os.path.abspath(__file__).split('/')[:-1])

    data = dict()
    parse_fio_data(f"{file_path}/data", data)

    queue_depths = np.arange(1, 8)

    write100 = [None] * len(queue_depths)
    write100_iops = [None] * len(queue_depths)
    write99 = [None] * len(queue_depths)
    write99_iops = [None] * len(queue_depths)
    write95 = [None] * len(queue_depths)
    write95_iops = [None] * len(queue_depths)
    write90 = [None] * len(queue_depths)
    write90_iops = [None] * len(queue_depths)
    write75 = [None] * len(queue_depths)
    write75_iops = [None] * len(queue_depths)
    write50 = [None] * len(queue_depths)
    write50_iops = [None] * len(queue_depths)
    write25 = [None] * len(queue_depths)
    write25_iops = [None] * len(queue_depths)

    for key, value in data.items():
        if "bw" in key:
            continue
        numjobs = int(re.search(r'\d+', key).group())
        if numjobs > 7:
            continue # We skip 14 as it turns out we were bottlenecked by not enough cpu cores, giving inaccurate results
        else:
            x = numjobs - 1
        if 'wflow_100' in key:
            write100[x] = value["jobs"][0]["finish"]["lat_ns"]["percentile"]["95.000000"]/1000
            write100_iops[x] = value["jobs"][0]["finish"]["iops_mean"]/1000
        elif 'wflow_99' in key:
            write99[x] = value["jobs"][0]["finish"]["lat_ns"]["percentile"]["95.000000"]/1000
            write99_iops[x] = value["jobs"][0]["finish"]["iops_mean"]/1000
        elif 'wflow_95' in key:
            write95[x] = value["jobs"][0]["finish"]["lat_ns"]["percentile"]["95.000000"]/1000
            write95_iops[x] = value["jobs"][0]["finish"]["iops_mean"]/1000
        elif 'wflow_90' in key:
            write90[x] = value["jobs"][0]["finish"]["lat_ns"]["percentile"]["95.000000"]/1000
            write90_iops[x] = value["jobs"][0]["finish"]["iops_mean"]/1000
        elif 'wflow_75' in key:
            write75[x] = value["jobs"][0]["finish"]["lat_ns"]["percentile"]["95.000000"]/1000
            write75_iops[x] = value["jobs"][0]["finish"]["iops_mean"]/1000
        elif 'wflow_50' in key:
            write50[x] = value["jobs"][0]["finish"]["lat_ns"]["percentile"]["95.000000"]/1000
            write50_iops[x] = value["jobs"][0]["finish"]["iops_mean"]/1000
        elif 'wflow_25' in key:
            write25[x] = value["jobs"][0]["finish"]["lat_ns"]["percentile"]["95.000000"]/1000
            write25_iops[x] = value["jobs"][0]["finish"]["iops_mean"]/1000

    fig, ax = plt.subplots()

    ax.plot(write100_iops, write100, markersize = 4, marker = '>', label="   0% append")
    ax.plot(write99_iops, write99, markersize = 4, marker = 'x',   label="   1% append")
    ax.plot(write95_iops, write95, markersize = 4, marker = 'o',   label="   5% append")
    ax.plot(write90_iops, write90, markersize = 4, marker = '<',   label=" 10% append")
    ax.plot(write75_iops, write75, markersize = 4, marker = '^',   label=" 25% append")
    ax.plot(write50_iops, write50, markersize = 4, marker = '*',   label=" 50% append")
    # ax.plot(write25_iops, write25, markersize = 4, marker = 'p',   label=" 75% finish")

    fig.tight_layout()
    ax.grid(which='major', linestyle='dashed', linewidth='1')
    ax.set_axisbelow(True)
    # ax.legend(loc='best', handles=handles)
    ax.legend(loc='best')
    ax.set_ylim(bottom=0, top=250)
    ax.set_xlim(left=0)
    ax.set_ylabel("p95 write Latency (usec)")
    ax.set_xlabel("Total IOPS (x1000)")
    plt.savefig(f"{file_path}/loaded_write_latency-append.pdf", bbox_inches="tight")
    plt.savefig(f"{file_path}/loaded_write_latency-append.png", bbox_inches="tight")
    plt.clf()