#! /usr/bin/python3
import matplotlib.patches as mpatches
import seaborn as sns
from colorama import Fore, Style
import colorama
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib
import math
import json
import glob
import re
import os
import sys
sys.path.append(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))) + '/../../../')
from interference_model.quantification import get_interference_gpt

# TODO: retrieve these values from ZenFS tracing for final calculation
WRITE_INTERFERENCE_GAMMA = 0.5
RESET_INTERFERENCE_DELTA = 0.5

# From our benchmark reset-on-write-interference, the retrieved RMS value
RESET_ON_WRITE_RMS = 0.241
# From our benchmark write-on-reset-interference, the retrieved RMS value
WRITE_ON_RESET_RMS = 0.072


plt.rc('font', size=12)          # controls default text sizes
plt.rc('axes', titlesize=12)     # fontsize of the axes title
plt.rc('axes', labelsize=12)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=12)    # fontsize of the tick labels
plt.rc('ytick', labelsize=12)    # fontsize of the tick labels
plt.rc('legend', fontsize=12)    # legend fontsize

# Switch to Type 1 Fonts.
# matplotlib.rcParams['text.usetex'] = True
plt.rc('font', **{'family': 'serif', 'serif': ['Times']})

matplotlib_color = ['C0', 'C1', 'C2', 'C3', 'C4', 'C5']
m_color_index = 0

matplotlib_colors = [
    'blue', 'green', 'red', 'cyan', 'magenta', 'yellw', 'white'
]

dot_style = [
    '+',
    'X',
    'o',
    'v',
    's',
    'P',
]

# Global parameters
linewidth = 4
markersize = 15

datalabel_size = 36
datalabel_va = 'bottom'
axis_tick_font_size = 46
axis_label_font_size = 52
legend_font_size = 46

heatmap_axis_tick_font_size = 26
heatmap_data_tag_size = 16


def parse_fio_data(fi, data):
    if not os.path.exists(f'{fi}'):
        print(f"No data in {fi}")
        return 0

    if "bw" in fi:
        return
    with open(fi, 'r') as f:
        for index, line in enumerate(f, 1):
            # Removing all fio logs in json file by finding first {
            if line.split()[0] == "{":
                rows = f.readlines()
                with open(os.path.join(os.getcwd(), "temp.json"), 'w+') as temp:
                    temp.write(line)
                    temp.writelines(rows)
                break

    if Path(os.path.join(os.getcwd(), "temp.json")).exists():
        with open(os.path.join(os.getcwd(), "temp.json"), 'r') as temp:
            data[fi] = dict()
            data[fi] = json.load(temp)
            os.remove(os.path.join(os.getcwd(), "temp.json"))

    return 1


def init_baseline(baseline):
    val = baseline[0]

    i = 0
    for value in baseline:
        baseline[i] = val
        i += 1


def parse_write_baseline(write_baseline_iops, write_baseline_lat, mqddl_iops, mqddl_lat, mqddl50_iops, mqddl50_lat,
                         mqddl_reset_iops, mqddl_reset_lat, zinc_baseline_iops, zinc_baseline_lat, 
                         zinc50_iops, zinc50_lat, zinc50_reset_iops, zinc50_reset_lat):
    for conf_key, conf_value in data.items():
        # print('c', conf_key)
        for key, value in conf_value.items():
            if conf_key == "baseline":
                if "reset_baseline" in key:
                    continue
                elif "bw" in key:
                    continue
                elif "50-mq_deadline" in key:
                    head, tail = os.path.split(key)
                    numjobs = int(re.search(r'\d+', tail).group())
                    mqddl50_iops[numjobs -
                                 1] = value["jobs"][2]["finish"]["iops_mean"]/1000
                    mqddl50_lat[numjobs -
                                1] = value["jobs"][2]["finish"]["lat_ns"]["percentile"]["95.000000"]/1000
                    mqddl_reset_iops[numjobs -
                                     1] = value["jobs"][1]["ZNS Reset"]["iops_mean"]
                    mqddl_reset_lat[numjobs -
                                    1] = value["jobs"][1]["ZNS Reset"]["lat_ns"]["percentile"]["95.000000"]/1000
                elif "100-mq_deadline" in key:
                    head, tail = os.path.split(key)
                    numjobs = int(re.search(r'\d+', tail).group())
                    mqddl_iops[numjobs -
                               1] = value["jobs"][0]["finish"]["iops_mean"]/1000
                    mqddl_lat[numjobs -
                              1] = value["jobs"][0]["finish"]["lat_ns"]["percentile"]["95.000000"]/1000
                elif "50-zinc" in key:
                    head, tail = os.path.split(key)
                    numjobs = int(re.search(r'\d+', tail).group())
                    zinc50_iops[numjobs -
                                 1] = value["jobs"][2]["finish"]["iops_mean"]/1000
                    zinc50_lat[numjobs -
                                1] = value["jobs"][2]["finish"]["lat_ns"]["percentile"]["95.000000"]/1000 
                    zinc50_reset_iops[numjobs -
                                     1] = value["jobs"][1]["ZNS Reset"]["iops_mean"]
                    zinc50_reset_lat[numjobs -
                                    1] = value["jobs"][1]["ZNS Reset"]["lat_ns"]["percentile"]["95.000000"]/1000
                elif "100-zinc" in key:
                    head, tail = os.path.split(key)
                    numjobs = int(re.search(r'\d+', tail).group())
                    zinc_baseline_iops[numjobs -
                                       1] = value["jobs"][0]["finish"]["iops_mean"]/1000
                    zinc_baseline_lat[numjobs -
                                      1] = value["jobs"][0]["finish"]["lat_ns"]["percentile"]["95.000000"]/1000
                else:
                    head, tail = os.path.split(key)
                    numjobs = int(re.search(r'\d+', tail).group())
                    write_baseline_iops[numjobs -
                                        1] = value["jobs"][0]["finish"]["iops_mean"]/1000
                    write_baseline_lat[numjobs -
                                       1] = value["jobs"][0]["finish"]["lat_ns"]["percentile"]["95.000000"]/1000
            else:
                continue


def parse_reset_baseline(reset_baseline_iops, reset_baseline_lat):
    for conf_key, conf_value in data.items():

        for key, value in conf_value.items():
            if conf_key == "baseline":
                if "reset_baseline" in key:
                    reset_baseline_iops[0] = value["jobs"][1]["ZNS Reset"]["iops_mean"]
                    reset_baseline_lat[0] = value["jobs"][1]["ZNS Reset"]["lat_ns"]["percentile"]["95.000000"]/1000
                    init_baseline(reset_baseline_iops)
                    init_baseline(reset_baseline_lat)
                    print(reset_baseline_iops, reset_baseline_lat)
                    return
                else:
                    continue
            else:
                continue


def get_matrix_col(val):
    """Get the config index for the col which represents the reset latency"""
    match(val):
        case 16:
            return 3
        case 32:
            return 2
        case 64:
            return 1
        case 128:
            return 0


def get_matrix_row(val):
    """Get the config index for the row which represents the write ratio"""
    match(val):
        case 200:
            return 0
        case 2000:
            return 1
        case 20000:
            return 2
        case 200000:
            return 3

if __name__ == "__main__":
    file_path = '/'.join(os.path.abspath(__file__).split('/')[:-1])

    data = dict()
    data["baseline"] = dict()
    for fi in glob.glob(f'data/*'):
        fi = fi.split('/')[-1]
        parse_fio_data(f"{file_path}/data/{fi}", data["baseline"])

    os.makedirs(f"{file_path}/figures", exist_ok=True)

    queue_depths = np.arange(1, 8)
    lowest_interference = (None, None)

    reset_baseline_iops = [None] * len(queue_depths)
    reset_baseline_lat = [None] * len(queue_depths)
    # NOTE: This is the old setup, now instead use mqddl_iops
    write_baseline_iops = [None] * len(queue_depths)
    # NOTE: This is the old setup, now instead use mqddl_lat
    write_baseline_lat = [None] * len(queue_depths)
    config_reset_limit = []
    config_write_ratio = []
    config_interference = np.zeros(shape=(4, 4))
    config_interference_write = np.zeros(shape=(4, 4))
    config_interference_reset = np.zeros(shape=(4, 4))
    mqddl_iops = [None] * len(queue_depths)
    mqddl50_iops = [None] * len(queue_depths)
    mqddl_lat = [None] * len(queue_depths)
    mqddl50_lat = [None] * len(queue_depths)
    zinc_baseline_iops = [None] * len(queue_depths)
    zinc_baseline_lat = [None] * len(queue_depths)
    zinc50_iops = [None] * len(queue_depths)
    zinc50_lat = [None] * len(queue_depths)   
    zinc50_reset_iops = [None] * len(queue_depths)
    zinc50_reset_lat = [None] * len(queue_depths)   
    mqddl_reset_iops = [None] * len(queue_depths)
    mqddl_reset_lat = [None] * len(queue_depths)

    parse_write_baseline(write_baseline_iops, write_baseline_lat, mqddl_iops, mqddl_lat, mqddl50_iops, mqddl50_lat,
                         mqddl_reset_iops, mqddl_reset_lat, zinc_baseline_iops, zinc_baseline_lat,
                         zinc50_iops,zinc50_lat,zinc50_reset_iops,zinc50_reset_lat)
    parse_reset_baseline(reset_baseline_iops, reset_baseline_lat)

    mqddl_write_interference = get_interference_gpt(
        mqddl_iops, mqddl50_iops, mqddl_lat, mqddl50_lat)
    mqddl_reset_interference = get_interference_gpt(
        reset_baseline_iops, mqddl_reset_iops, reset_baseline_lat, mqddl_reset_lat)
    zinc_write_interference = get_interference_gpt(
        zinc_baseline_iops, zinc50_iops, zinc_baseline_lat, zinc50_lat)
    write_interference = get_interference_gpt(
        mqddl_iops, zinc50_iops, mqddl_lat, zinc50_lat)
    reset_interference = get_interference_gpt(
        reset_baseline_iops, zinc50_reset_iops, reset_baseline_lat, zinc50_reset_lat)

    print("-------------------------------------------------------------------------------------")
    print(
        f"mq-deadline WRITE Interference RMS {mqddl_write_interference: >20.15f}")
    print(
        f"mq-deadline RESET Interference RMS {mqddl_reset_interference: >20.15f}")
    print(
        f"ZINC WRITE Interference RMS {zinc_write_interference: >20.15f}")
    print(
        f"ZINC versus mq-deadline WRITE Interference RMS {write_interference: >20.15f}")
    print(
        f"ZINC RESET Interference RMS {reset_interference: >20.15f}")
    print("-------------------------------------------------------------------------------------")



    fig, ax = plt.subplots()

    ax.plot(mqddl_iops, mqddl_lat, markersize=4,
            marker='>', label="   0% reset - mqddl")
    ax.plot(mqddl50_iops, mqddl50_lat, markersize=4,
            marker='>', label="  50% reset - mqddl")
    ax.plot(zinc_baseline_iops, zinc_baseline_lat,
            markersize=4, marker='>', label="   0% reset - zinc")
    ax.plot(zinc50_iops, zinc50_lat, markersize=4,
            marker='*', label=" 50% reset - zinc")

    fig.tight_layout()
    ax.grid(which='major', linestyle='dashed', linewidth='1')
    ax.set_axisbelow(True)
    # ax.legend(loc='best', handles=handles)
    ax.legend(loc='best')
    ax.set_ylim(bottom=0, top=140)
    ax.set_xlim(left=0)
    ax.set_ylabel("p95 write Latency (usec)")
    ax.set_xlabel("Total IOPS (x1000)")
    plt.savefig(
        f"{file_path}/figures/loaded_write_latency-optimal.pdf", bbox_inches="tight")
    plt.savefig(
        f"{file_path}/figures/loaded_write_latency-optimal.png", bbox_inches="tight")
    plt.clf()
    plt.close()


