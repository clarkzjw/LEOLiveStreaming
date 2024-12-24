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

from config import L2A, Dynamic, LoLP, CMAB, DATA_DIR, TITLE, SCENARIO_SET, figsize, FIGURE_DIR, EXCEPTED, ensure_dir, VIDEO_PROFILE


def get_per_round_average_live_latency(dirpath: Path, alg: str) -> float:
    latency = json.load(open(str(dirpath.joinpath("playback_latency.json"))))
    result = list()
    for _, v in latency.items():
        result.append(v)
    return np.average(result)


def average_live_latency_by_target_latency(prefix: str):
    for g in SCENARIO_SET:
        for vp in VIDEO_PROFILE:
            fig = plt.figure(figsize = figsize)

            result = defaultdict(list)

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
                            arrL2A.append(get_per_round_average_live_latency(Path(dirpath), L2A))
                        elif Dynamic in dirpath:
                            arrDynamic.append(get_per_round_average_live_latency(Path(dirpath), Dynamic))
                        elif LoLP in dirpath:
                            arrLoLP.append(get_per_round_average_live_latency(Path(dirpath), LoLP))
                        elif CMAB in dirpath:
                            arrCMAB.append(get_per_round_average_live_latency(Path(dirpath), CMAB))

                result[L2A].append(np.average(arrL2A))
                result[Dynamic].append(np.average(arrDynamic))
                result[LoLP].append(np.average(arrLoLP))
                result[CMAB].append(np.average(arrCMAB))
                result[EXCEPTED].append(targetLatency)

            labels = ['3s', '4s', '5s', '6s']

            bar_width = 0.15
            index = np.arange(len(result[EXCEPTED]))

            ax.bar(index, result[L2A], bar_width, label="L2A-LL", color='tab:blue')
            ax.bar(index + bar_width, result[Dynamic], bar_width, label="Dynamic", color='tab:orange')
            ax.bar(index + 2*bar_width, result[LoLP], bar_width, label="LoL+", color='tab:green')
            ax.bar(index + 3*bar_width, result[CMAB], bar_width, label="CMAB", color='tab:brown')
            ax.bar(index + 4*bar_width, result[EXCEPTED], bar_width, label="Expected", color='tab:red')

            ax.set_xlabel('Target Latency')
            ax.set_ylabel('Average Latency')
            ax.set_xticks(index + 2*bar_width)
            ax.set_xticklabels(labels)

            plt.xticks(np.arange(4), np.arange(3, 7))
            plt.xlabel("Latency Target (seconds)")
            plt.ylabel("Average Live Latency (seconds)")

            plt.legend(loc="lower right")
            plt.tight_layout()
            ensure_dir("{}/{}".format(FIGURE_DIR, vp))
            plt.savefig("{}/{}/average_live_latency_".format(FIGURE_DIR, vp) + TITLE[g] + ".png")
            plt.savefig("{}/{}/average_live_latency_".format(FIGURE_DIR, vp) + TITLE[g] + ".eps")
            plt.clf()
            plt.close()


if __name__ == "__main__":
    average_live_latency_by_target_latency(DATA_DIR)