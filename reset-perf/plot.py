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

    queue_depths = np.arange(1, 8)

    peak = 0
    bw = [None] * (len(queue_depths))
    bw_plot = [None] * (len(queue_depths) + 1)
    bw_err = [None] * (len(queue_depths) + 1)
    bw_plot_err = [0] * 505

    for key, value in data.items():
        if "bw" in key:
            peak = value["jobs"][1]["ZNS Reset"]["bw_mean"]
        else:
            numjobs = int(re.search(r'\d+', key).group())
            x = numjobs - 1

            bw[x] = value["jobs"][1]["ZNS Reset"]["bw_mean"]
            bw_err[x] = value["jobs"][1]["ZNS Reset"]["bw_dev"]

    bw_plot[0] = 1 # peak relative bw
    bw_err[0] = 0

    i = 1;
    for value in bw:
        if value == None:
            continue
        bw_plot[i] = value / peak
        i += 1

    i = 1
    for value in bw_err:
        if value == None:
            continue
        bw_plot_err[i * 72] = value / peak
        i += 1


    x = np.arange(0, len(queue_depths) + 1)
    X_Y_Spline = make_interp_spline(x, bw_plot)

    X_ = np.linspace(x.min(), x.max(), 505)
    Y_ = X_Y_Spline(X_)

    fig, ax = plt.subplots()


    # plt.errorbar(X_, Y_, yerr=bw_plot_err, markersize = 4, marker = 'o', markevery=72) # 505 points = 504/8 (x-axis points) = 72 + Remainder 1 so the last marker shows
    plt.plot(X_, Y_, markersize = 4, marker = 'o', markevery=72) # 505 points = 504/8 (x-axis points) = 72 + Remainder 1 so the last marker shows

    fig.tight_layout()
    ax.grid(which='major', linestyle='dashed', linewidth='1')
    ax.set_axisbelow(True)
    # ax.legend(loc='best', handles=handles)
    # ax.legend(loc='best')
    ax.set_ylim(bottom=0)
    # ax.set_xlim(left=0)
    ax.set_ylabel("relative reset bandwidth")
    ax.set_xlabel("concurrent write jobs")
    plt.savefig(f"{file_path}/reset-performance.pdf", bbox_inches="tight")
    plt.savefig(f"{file_path}/reset-performance.png", bbox_inches="tight")
    plt.clf()
