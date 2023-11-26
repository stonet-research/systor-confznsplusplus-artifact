#! /usr/bin/python3

import os
import re
import glob
import json
import math
import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np
import colorama
from colorama import Fore, Style
import matplotlib.patches as mpatches

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from interference_model.quantification import get_interference_rms

# TODO: retrieve these values from ZenFS tracing for final calculation
WRITE_INTERFERENCE_GAMMA = 0.5
RESET_INTERFERENCE_DELTA = 0.5

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
                if line.split()[0] == "{":
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

def init_baseline(baseline):
    val = baseline[0]

    i = 0
    for value in baseline:
        baseline[i] = val
        i += 1

def parse_write_baseline(write_baseline_iops, write_baseline_lat):
     for conf_key, conf_value in data.items():

        for key, value in conf_value.items():
            if conf_key == "baseline":
                if "reset_baseline" in key:
                    continue
                elif "bw" in key:
                    continue
                else:
                    head, tail = os.path.split(key)
                    numjobs = int(re.search(r'\d+', tail).group())
                    write_baseline_iops[numjobs - 1] =  value["jobs"][0]["finish"]["iops_mean"]/1000  # this is a bug in fio it being under the "finish" instead of "write"
                    write_baseline_lat[numjobs - 1] = value["jobs"][0]["finish"]["lat_ns"]["percentile"]["95.000000"]/1000
            else:
                continue

def parse_reset_baseline(reset_baseline_iops, reset_baseline_write):
     for conf_key, conf_value in data.items():

        for key, value in conf_value.items():
            if conf_key == "baseline":
                if "reset_baseline" in key:
                    reset_baseline_iops[0] = value["jobs"][1]["ZNS Reset"]["iops_mean"]
                    reset_baseline_lat[0] = value["jobs"][1]["ZNS Reset"]["lat_ns"]["percentile"]["95.000000"]/1000 # TODO: change this to clat after rerunning
                    init_baseline(reset_baseline_iops)
                    init_baseline(reset_baseline_lat)

                    return
                else:
                    continue
            else:
                continue

if __name__ == "__main__":
    file_path = '/'.join(os.path.abspath(__file__).split('/')[:-1])

    data = dict()
    for dir in glob.glob(f'*'):
        dir = dir.split('/')[-1]
        if dir == "data":
            data["baseline"] = dict()
            parse_fio_data(f"{file_path}/{dir}", data["baseline"])
        elif "data" in dir:
            config = re.findall(r'\d+', dir)
            config_string = f"reset_lat_{config[0]}-write_ratio_{config[1]}"
            data[config_string] = dict()
            data[config_string]["reset_limit_val"] = config[0]
            data[config_string]["write_ratio_val"] = config[1]
            parse_fio_data(f"{file_path}/{dir}", data[config_string])

    os.makedirs(f"{file_path}/figures", exist_ok=True)

    queue_depths = np.arange(1, 8)
    lowest_interference = (None, None)

    reset_baseline_iops = [None] * len(queue_depths)
    reset_baseline_lat = [None] * len(queue_depths)
    write_baseline_iops = [None] * len(queue_depths)
    write_baseline_lat = [None] * len(queue_depths)
    config_reset_limit = []
    config_write_ratio = []
    config_interference = []

    parse_write_baseline(write_baseline_iops, write_baseline_lat)
    parse_reset_baseline(reset_baseline_iops, reset_baseline_lat)

    for conf_key, conf_value in data.items():
        write_iops = [None] * len(queue_depths)
        write_lat = [None] * len(queue_depths)
        reset_iops = [None] * len(queue_depths)
        reset_lat = [None] * len(queue_depths)

        for key, value in conf_value.items():
            if conf_key == "baseline":
               continue
            elif "reset_limit_val" in key or "write_ratio_val" in key:
                continue
            else:
                head, tail = os.path.split(key)
                numjobs = int(re.search(r'\d+', tail).group())
                x = numjobs - 1
                write_iops[x] = value["jobs"][2]["finish"]["iops_mean"]/1000
                write_lat[x] = value["jobs"][2]["finish"]["clat_ns"]["percentile"]["95.000000"]/1000
                reset_iops[x] = value["jobs"][1]["ZNS Reset"]["iops_mean"]
                reset_lat[x] = value["jobs"][1]["ZNS Reset"]["clat_ns"]["percentile"]["95.000000"]/1000

        # While debugging skip all that are ongoing and don't have all data
        if not None in write_iops:
            write_interference = get_interference_rms(write_baseline_iops, write_iops, write_baseline_lat, write_lat)
            reset_interference = get_interference_rms(reset_baseline_iops, reset_iops, reset_baseline_lat, reset_lat)

            # print(f"Config {conf_key} WRITE Interference RMS {write_interference}")
            # print(f"Config {conf_key} RESET Interference RMS {reset_interference}")

            interference = WRITE_INTERFERENCE_GAMMA * write_interference + RESET_INTERFERENCE_DELTA * reset_interference
            print(f"Config {conf_key : >40} Interference RMS {interference : >20}")

            config_reset_limit.append(int(conf_value["reset_limit_val"]))
            config_write_ratio.append(int(conf_value["write_ratio_val"]))
            config_interference.append(int(interference))

            inter = lowest_interference[1]
            if inter == None:
                lowest_interference = (conf_key, interference)
            elif interference < inter:
                    lowest_interference = (conf_key, interference)

            fig, ax = plt.subplots()

            ax.plot(write_baseline_iops, write_baseline_lat, markersize = 4, marker = '>', label="   0% reset")
            ax.plot(write_iops, write_lat, markersize = 4, marker = '*', label=" 50% reset")

            fig.tight_layout()
            ax.grid(which='major', linestyle='dashed', linewidth='1')
            ax.set_axisbelow(True)
            # ax.legend(loc='best', handles=handles)
            ax.legend(loc='best')
            ax.set_ylim(bottom=0, top=140)
            ax.set_xlim(left=0)
            ax.set_ylabel("p95 write Latency (usec)")
            ax.set_xlabel("Total IOPS (x1000)")
            plt.savefig(f"{file_path}/figures/loaded_write_latency-{conf_key}.pdf", bbox_inches="tight")
            plt.savefig(f"{file_path}/figures/loaded_write_latency-{conf_key}.png", bbox_inches="tight")
            plt.clf()

    print("\n-------------------------------------------------------------------------------------")
    print(f"{Fore.GREEN}Lowest{Style.RESET_ALL} {lowest_interference[0] : >40} Interference RMS {lowest_interference[1] : >20}")

    # TODO: THIS IS TEMP FOR DEBUG
    config_reset_limit=config_reset_limit[1:]
    config_write_ratio=config_write_ratio[1:]
    config_interference=config_interference[1:]
    x = np.reshape(config_reset_limit, (2, 2))
    y = np.reshape(config_write_ratio, (2, 2))
    z = np.reshape(config_interference, (2, 2))

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    ax.plot_surface(x, y, z)

    ax.set_xlabel('Reset Latency (ms)')
    ax.set_ylabel('Write Ratio')
    ax.set_zlabel('Interference RMS')
    
    plt.savefig(f"{file_path}/figures/configuration-space.png", bbox_inches="tight")
    plt.savefig(f"{file_path}/figures/configuration-space.pdf", bbox_inches="tight")

