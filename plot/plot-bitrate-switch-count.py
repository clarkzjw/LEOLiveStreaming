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

from config import L2A, Dynamic, LoLP, CMAB, DATA_DIR, TITLE, SCENARIO_SET, figsize, BITRATE_LIST_LENGTH, FIGURE_DIR, VIDEO_PROFILE, ensure_dir


def get_per_round_bitrate_switch_from_bitrates(dirpath: Path) -> int:
    bitrates = json.load(open(str(dirpath.joinpath("bitrates.json"))))
    lst = list(bitrates.values())
    total = sum(x != y for x, y in zip(lst, lst[1:]))
    return total


def bitrate_switch_by_target_latency(prefix: str):
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
                            arrL2A.append(get_per_round_bitrate_switch_from_bitrates(Path(dirpath)))
                        elif Dynamic in dirpath:
                            arrDynamic.append(get_per_round_bitrate_switch_from_bitrates(Path(dirpath)))
                        elif LoLP in dirpath:
                            arrLoLP.append(get_per_round_bitrate_switch_from_bitrates(Path(dirpath)))
                        elif CMAB in dirpath:
                            arrCMAB.append(get_per_round_bitrate_switch_from_bitrates(Path(dirpath)))

                result[L2A].append(np.average(arrL2A))
                result[Dynamic].append(np.average(arrDynamic))
                result[LoLP].append(np.average(arrLoLP))
                result[CMAB].append(np.average(arrCMAB))

            bar_width = 0.15
            index = np.arange(len(result[Dynamic]))

            ax.bar(index, result[L2A], bar_width, label="L2A-LL", color='tab:blue')
            ax.bar(index + bar_width, result[Dynamic], bar_width, label="Dynamic", color='tab:orange')
            ax.bar(index + 2*bar_width, result[LoLP], bar_width, label="LoL+", color='tab:green')
            ax.bar(index + 3*bar_width, result[CMAB], bar_width, label="CMAB", color='tab:brown')

            # put the value on top of the bar
            for i in range(len(result[Dynamic])):
                textsize = 18
                ax.text(i, result[L2A][i] + 0.5, str(round(result[L2A][i], 2)), ha='center', va='bottom', fontsize=textsize, rotation=45)
                ax.text(i + bar_width, result[Dynamic][i] + 0.5, str(round(result[Dynamic][i], 2)), ha='center', va='bottom', fontsize=textsize, rotation=45)
                ax.text(i + 2*bar_width, result[LoLP][i] + 0.5, str(round(result[LoLP][i], 2)), ha='center', va='bottom', fontsize=textsize, rotation=45)
                ax.text(i + 3*bar_width, result[CMAB][i] + 0.5, str(round(result[CMAB][i], 2)), ha='center', va='bottom', fontsize=textsize, rotation=45)

            plt.xticks(np.arange(4), np.arange(3, 7))
            plt.xlabel("Latency Target (seconds)")
            plt.ylabel("Number of Bitrate Switches")
            plt.ylim(0, max(max(result[x]) for x in result.keys()) * 1.1)
            plt.legend(loc="best")
            plt.tight_layout()
            ensure_dir("{}/{}".format(FIGURE_DIR, vp))
            plt.savefig("{}/{}/bitrate_switch_".format(FIGURE_DIR, vp) + TITLE[g] + ".png")
            plt.savefig("{}/{}/bitrate_switch_".format(FIGURE_DIR, vp) + TITLE[g] + ".eps")
            plt.clf()
            plt.close()


if __name__ == "__main__":
    bitrate_switch_by_target_latency(DATA_DIR)