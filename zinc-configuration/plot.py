#! /usr/bin/python3

import os
import re
import glob
import json
import math
import matplotlib
import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np
import colorama
from colorama import Fore, Style
import seaborn as sns
import matplotlib.patches as mpatches

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from interference_model.quantification import get_interference_rms

# TODO: retrieve these values from ZenFS tracing for final calculation
WRITE_INTERFERENCE_GAMMA = 0.5
RESET_INTERFERENCE_DELTA = 0.5

RESET_ON_WRITE_RMS = 0.241 # From our benchmark reset-on-write-interference, the retrieved RMS value
WRITE_ON_RESET_RMS = 0.072 # From our benchmark write-on-reset-interference, the retrieved RMS value


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
                    write_baseline_iops[numjobs - 1] =  value["jobs"][0]["finish"]["iops_mean"]/1000
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
        
def generate_heatmap(config_interference, job, max):
    reset_latency = [16, 32, 64, 128]
    write_ratio    = [200, 2000, 20000, 200000]

    cmap = sns.color_palette('rocket_r', as_cmap=True).copy()
    cmap.set_under('#88CCEE')
    
    ax = sns.heatmap(config_interference, 
                    linewidth=0.1, 
                    xticklabels=True, 
                    cmap=cmap, 
                    yticklabels=True, 
                    clip_on=False, 
                    # cbar_kws={'shrink': 0.8, 'extend': 'min', 'extendrect': True, 'format': '%d Blocks (512B)'}, 
                    square=True, 
                    cbar=True, 
                    vmin=0,
                    vmax=max,
                    linecolor='black',  annot_kws={"size": 20})

    ax.set_xticks([x+0.5 for x in np.arange(len(write_ratio))])
    ax.set_xticklabels(labels=write_ratio,
                fontsize=heatmap_axis_tick_font_size)
    ax.xaxis.set_label_position('top') 
    ax.xaxis.tick_top()

    ax.set_yticks([x+0.5 for x in np.arange(len(reset_latency))])
    ax.set_yticklabels(labels=reset_latency[::-1],
                    fontsize=heatmap_axis_tick_font_size)

    plt.setp(ax.get_xticklabels(),
                rotation=45,
                ha="left",
                rotation_mode="anchor")
    
    plt.setp(ax.get_yticklabels(),
                rotation=45,
                ha="right",
                rotation_mode="anchor")
    
    ax.set_ylabel("Reset Latency")
    ax.set_xlabel("Write Ratio")
    
    for i in range(len(config_interference)):
        for j in range(len(config_interference[0])):
            text = round(config_interference[i][j], 3)
            if config_interference[i][j] >= 0.9:
                color = 'w'
            elif config_interference[i][j] == 0:
                color = 'black'
            else:
                color = 'black'
            text = ax.text(j+0.5,
                            i+0.5,
                            text,
                            ha="center",
                            va="center",
                            color=color,
                            fontsize=heatmap_data_tag_size)

    cbar = ax.collections[0].colorbar
    # here set the labelsize by 20
    cbar.ax.tick_params(labelsize=20)

    plt.savefig(f"{file_path}/figures/configuration-interference-{job}.pdf", bbox_inches="tight")
    plt.savefig(f"{file_path}/figures/configuration-interference-{job}.png", bbox_inches="tight")
    plt.clf()
    plt.close()

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
    config_interference = np.zeros(shape=(4, 4))
    config_interference_write = np.zeros(shape=(4, 4))
    config_interference_reset = np.zeros(shape=(4, 4))

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

            print("-------------------------------------------------------------------------------------")
            print(f"Config {conf_key: >40} WRITE Interference RMS {write_interference: >20.15f}")
            print(f"Config {conf_key: >40} RESET Interference RMS {reset_interference: >20.15f}")

            interference = WRITE_INTERFERENCE_GAMMA * write_interference + RESET_INTERFERENCE_DELTA * reset_interference
            print(f"Config {conf_key : >40} Interference RMS {interference : >26.15f}")
            print("-------------------------------------------------------------------------------------")

            # config_reset_limit.append(int(conf_value["reset_limit_val"]))
            # config_write_ratio.append(int(conf_value["write_ratio_val"]))
            config_interference[get_matrix_col(int(conf_value["reset_limit_val"]))][get_matrix_row(int(conf_value["write_ratio_val"]))] = interference
            
            config_interference_write[get_matrix_col(int(conf_value["reset_limit_val"]))][get_matrix_row(int(conf_value["write_ratio_val"]))] = write_interference
            config_interference_reset[get_matrix_col(int(conf_value["reset_limit_val"]))][get_matrix_row(int(conf_value["write_ratio_val"]))] = reset_interference
            
            # This one is to calculate relative gains respective to the benchmarked reset-on-write-interference RMS
            # rms_repesctive_change = float(RESET_ON_WRITE_RMS) / write_interference
            # config_interference_write[get_matrix_col(int(conf_value["reset_limit_val"]))][get_matrix_row(int(conf_value["write_ratio_val"]))] = rms_repesctive_change
           
            # This one is to calculate relative gains respective to the benchmarked write-on-reset-interference RMS
            # rms_repesctive_change = float(WRITE_ON_RESET_RMS) / reset_interference
            # config_interference_reset[get_matrix_col(int(conf_value["reset_limit_val"]))][get_matrix_row(int(conf_value["write_ratio_val"]))] = rms_repesctive_change


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
            plt.close()

    print("\n=====================================================================================")
    print(f"{Fore.GREEN}Lowest{Style.RESET_ALL} {lowest_interference[0] : >40} Interference RMS {lowest_interference[1]:>26.15f}")


    generate_heatmap(config_interference_write, "write", 2)
    generate_heatmap(config_interference_reset, "reset", 25)
    generate_heatmap(config_interference, "combined", 15)