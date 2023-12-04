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

if __name__ == "__main__":
    file_path = '/'.join(os.path.abspath(__file__).split('/')[:-1])

    files = [f"{file_path}/data/zenfs_data_fill.log", f"{file_path}/data/zenfs_data_overwrite.log", f"{file_path}/data/zenfs_data_gc.log", f"{file_path}/data/zenfs_data.log"]

    for data_path in files:
        with open(data_path, 'r') as f:
            data = []
            lat_data = []
            for index, line in enumerate(f, 1):
                if "thread 0" in line:
                    ops = line.split()[7]
                    op_dat = ops.split(",")
                    data.append(float(op_dat[1][:-1])/1000)
                    lat = line.split()[10]
                    lat_dat = lat.split(",")
                    lat_data.append((float(lat_dat[1][:-1])))
                else:
                    continue

        if "fill" in data_path:
            op = "fill"
        elif "overwrite" in data_path:
            op = "overwrite"
        elif "gc" in data_path:
            op = "gc"
        else:
            op = "concur_fill"

        fig, ax = plt.subplots()

        ax.plot(lat_data, data, markersize = 4, marker = '>')

        fig.tight_layout()
        ax.grid(which='major', linestyle='dashed', linewidth='1')
        ax.set_axisbelow(True)
        # ax.legend(loc='best', handles=handles)
        # ax.legend(loc='best')
        ax.set_ylim(bottom=0, top=(max(data) * 1.1))
        ax.set_ylabel("Total IOPS (x1000)")
        ax.set_xlabel("Time (seconds)")
        plt.savefig(f"{file_path}/zenfs_throughput-{op}.pdf", bbox_inches="tight")
        plt.savefig(f"{file_path}/zenfs_throughput-{op}.png", bbox_inches="tight")
        plt.clf()
