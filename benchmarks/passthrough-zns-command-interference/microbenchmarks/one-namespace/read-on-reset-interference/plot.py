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
from scipy.interpolate import make_interp_spline

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/../../../')

from interference_model.quantification import get_interference_rms

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

    peak = 0
    iops = [None] * (len(queue_depths))
    iops_plot = [None] * (len(queue_depths) + 1)
    iops_err = [None] * (len(queue_depths) + 1)
    iops_plot_err = [0] * 577

    for key, value in data.items():
        if "bw" in key:
            peak = value["jobs"][1]["ZNS Reset"]["iops"]
        else:
            x = int(math.log2(int(value["jobs"][2]["job options"]["iodepth"])))

            iops[x] = value["jobs"][1]["ZNS Reset"]["iops"]
            iops_err[x] = value["jobs"][1]["ZNS Reset"]["iops"]

    iops_plot[0] = 1 # peak relative iops
    iops_err[0] = 0

    iops_max = [iops[0]] * (len(queue_depths))

    print(f"Interference RMS 0% - 50% {get_interference_rms(iops_max, iops, iops, iops, 1, 0)}")

    i = 1;
    for value in iops:
        if value == None:
            continue
        iops_plot[i] = value / peak
        i += 1

    i = 1
    for value in iops_err:
        if value == None:
            continue
        iops_plot_err[i * 72] = value / peak
        i += 1

    x = np.arange(0, len(queue_depths) + 1)
    X_Y_Spline = make_interp_spline(x, iops_plot)

    X_ = np.linspace(x.min(), x.max(), 577)
    Y_ = X_Y_Spline(X_)

    fig, ax = plt.subplots()

    # plt.errorbar(X_, Y_, yerr=iops_plot_err, markersize = 4, marker = 'o', markevery=72)
    plt.plot(X_, Y_, markersize = 4, marker = 'o', markevery=72)

    fig.tight_layout()
    ax.grid(which='major', linestyle='dashed', linewidth='1')
    ax.set_axisbelow(True)
    # ax.legend(loc='best', handles=handles)
    # ax.legend(loc='best')
    ax.set_ylim(bottom=0, top=1.15)
    # ax.set_xlim(left=0)
    ax.set_xticklabels([0,0,1,2,4,8,16,32,64,128])
    ax.set_ylabel("relative reset IOPS")
    ax.set_xlabel("read I/O depth")
    plt.savefig(f"{file_path}/reset-performance.pdf", bbox_inches="tight")
    plt.savefig(f"{file_path}/reset-performance.png", bbox_inches="tight")
    plt.clf()