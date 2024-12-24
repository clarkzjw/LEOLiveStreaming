import os
import sys
import json
import numpy as np
from matplotlib import pyplot as plt
from pathlib import Path
from pprint import pprint
from dataclasses import dataclass
from collections import defaultdict
from datetime import datetime

from config import L2A, Dynamic, LoLP, CMAB, DATA_DIR, TITLE, SCENARIO_SET, figsize, FIGURE_DIR, VIDEO_PROFILE, ensure_dir


def get_per_round_average_bitrate(experiment_id: str, alg:str):
    print(experiment_id)

    bitrate = json.load(open(str(Path(experiment_id).joinpath("bitrate_by_second.json"))))
    return np.average(bitrate)


def get_per_round_std_bitrate(experiment_id: str, alg:str) -> float:
    print(experiment_id)
    bitrate = json.load(open(str(Path(experiment_id).joinpath("bitrate_by_second.json"))))
    return np.std(list(bitrate))


def average_bitrate_by_target_latency(prefix: str):
    for g in SCENARIO_SET:
        for vp in VIDEO_PROFILE:
            fig = plt.figure(figsize = figsize)

            result_avg = defaultdict(list)

            ax = fig.add_subplot(1, 1, 1)
            for targetLatency in range(3, 7, 1):
                arrL2A = []
                arrDynamic = []
                arrLoLP = []
                arrCMAB = []

                for dirpath, dirnames, files in os.walk(prefix):
                    if len(files) != 0:
                        if "target-{}s".format(str(targetLatency)) not in dirpath:
                            continue
                        if vp not in dirpath:
                            continue
                        if "variable" not in dirpath:
                            continue
                        print(dirpath)
                        if L2A in dirpath:
                            arrL2A.append(get_per_round_average_bitrate(Path(dirpath), L2A))
                        elif Dynamic in dirpath:
                            arrDynamic.append(get_per_round_average_bitrate(Path(dirpath), Dynamic))
                        elif LoLP in dirpath:
                            arrLoLP.append(get_per_round_average_bitrate(Path(dirpath), LoLP))
                        elif CMAB in dirpath:
                            arrCMAB.append(get_per_round_average_bitrate(Path(dirpath), CMAB))

                result_avg[L2A].append(np.average(arrL2A))
                result_avg[Dynamic].append(np.average(arrDynamic))
                result_avg[LoLP].append(np.average(arrLoLP))
                result_avg[CMAB].append(np.average(arrCMAB))

            bar_width = 0.15
            index = np.arange(len(result_avg[Dynamic]))

            ax.bar(index, result_avg[L2A], bar_width, label="L2A-LL", color='tab:blue')
            ax.bar(index + bar_width, result_avg[Dynamic], bar_width, label="Dynamic", color='tab:orange')
            ax.bar(index + 2*bar_width, result_avg[LoLP], bar_width, label="LoL+", color='tab:green')
            ax.bar(index + 3*bar_width, result_avg[CMAB], bar_width, label="CMAB", color='tab:brown')

            plt.xticks(np.arange(4), np.arange(3, 7))
            plt.xlabel("Latency Target (seconds)")
            plt.ylabel("Average Bitrate (Kbps)")
            plt.ylim(0, 6500)
            plt.legend(loc="lower right")
            plt.tight_layout()
            ensure_dir("{}/{}".format(FIGURE_DIR, vp))
            plt.savefig("{}/{}/average_bitrate_".format(FIGURE_DIR, vp) + TITLE[g] + ".png")
            plt.savefig("{}/{}/average_bitrate_".format(FIGURE_DIR, vp) + TITLE[g] + ".eps")
            plt.clf()
            plt.close()


def std_bitrate_by_target_latency(prefix: str):
    for g in SCENARIO_SET:
        for vp in VIDEO_PROFILE:
            fig = plt.figure(figsize = figsize)

            result_std = defaultdict(list)

            ax = fig.add_subplot(1, 1, 1)
            for targetLatency in range(3, 7, 1):
                arrL2A = []
                arrDynamic = []
                arrLoLP = []
                arrCMAB = []

                for dirpath, dirnames, files in os.walk(prefix):
                    if len(files) != 0:
                        if "target-{}s".format(str(targetLatency)) not in dirpath:
                            continue
                        if vp not in dirpath:
                            continue
                        if "variable" not in dirpath:
                            continue
                        print(dirpath)
                        if L2A in dirpath:
                            arrL2A.append(get_per_round_std_bitrate(Path(dirpath), L2A))
                        elif Dynamic in dirpath:
                            arrDynamic.append(get_per_round_std_bitrate(Path(dirpath), Dynamic))
                        elif LoLP in dirpath:
                            arrLoLP.append(get_per_round_std_bitrate(Path(dirpath), LoLP))
                        elif CMAB in dirpath:
                            arrCMAB.append(get_per_round_std_bitrate(Path(dirpath), CMAB))

                result_std[L2A].append(arrL2A[0])
                result_std[Dynamic].append(arrDynamic[0])
                result_std[LoLP].append(arrLoLP[0])
                result_std[CMAB].append(arrCMAB[0])

            bar_width = 0.15
            index = np.arange(len(result_std[Dynamic]))

            ax.bar(index, result_std[L2A], bar_width, label="L2A-LL", color='tab:blue')
            ax.bar(index + bar_width, result_std[Dynamic], bar_width, label="Dynamic", color='tab:orange')
            ax.bar(index + 2*bar_width, result_std[LoLP], bar_width, label="LoL+", color='tab:green')
            ax.bar(index + 3*bar_width, result_std[CMAB], bar_width, label="CMAB", color='tab:brown')

            plt.xticks(np.arange(4), np.arange(3, 7))
            plt.xlabel("Latency Target (seconds)")
            plt.ylabel("Bitrate Standard Deviation (Kbps)")
            plt.legend(loc="upper right")
            plt.ylim(0, 6000)
            plt.tight_layout()
            ensure_dir("{}/{}".format(FIGURE_DIR, vp))
            plt.savefig("{}/{}/std_bitrate_".format(FIGURE_DIR, vp) + TITLE[g] + ".png")
            plt.savefig("{}/{}/std_bitrate_".format(FIGURE_DIR, vp) + TITLE[g] + ".eps")
            plt.clf()
            plt.close()


if __name__ == "__main__":
    average_bitrate_by_target_latency(DATA_DIR)
    std_bitrate_by_target_latency(DATA_DIR)
