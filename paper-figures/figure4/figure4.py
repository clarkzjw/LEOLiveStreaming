import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import gridspec


LINEWIDTH = 4
figsize = (32, 9)
fontsize=22

plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42
plt.rcParams.update({'font.size': fontsize})
plt.rcParams.update({'axes.labelsize': fontsize})


def load_ping(filename: str):
    print(filename)
    first = None
    with open(filename, "r") as f:
        count = 0
        seq_list = []
        rtt_list = []
        timestamp_list = []
        for line in f.readlines():
            match = re.search(r"\[(\d+\.\d+)\].*icmp_seq=(\d+).*time=(\d+(\.\d+)?)", line)
            if match:
                count += 1
                timestamp = datetime.fromtimestamp(float(match.group(1)))
                if first == None:
                    first = timestamp
                if timestamp > first + timedelta(hours=4):
                    break
                try:
                    timestamp = datetime.strptime(str(timestamp)[11:], "%H:%M:%S.%f")
                except ValueError:
                    timestamp = datetime.strptime(str(timestamp)[11:], "%H:%M:%S")
                seq = int(match.group(2))
                rtt = float(match.group(3))
                timestamp_list.append(timestamp)
                seq_list.append(seq)
                rtt_list.append(rtt)
    print(len(timestamp_list))
    return timestamp_list, rtt_list


if __name__ == "__main__":
    scenario = ["Alaska", "Iowa"]
    latency = {}

    fig = plt.figure(figsize=figsize)
    gs0 = gridspec.GridSpec(1, 2, figure=fig, width_ratios=[2, 5])

    axECDF = fig.add_subplot(gs0[0])
    gs01 = gs0[1].subgridspec(2, 1)

    axARA = fig.add_subplot(gs01[1, :])
    axAlaska = fig.add_subplot(gs01[0, :])

    latency = {}
    for s in scenario:
        for dirpath, dirnames, files in os.walk(s):
            if len(files) != 0:
                for f in files:
                    if f.startswith("ping-") and f.endswith(".txt"):
                        ts, rtt = load_ping(Path(dirpath).joinpath(f))
                        assert(len(ts) == len(rtt))

                        rtt = np.array(rtt)
                        latency[s] = rtt
                        p99 = np.percentile(rtt, 99)
                        axECDF.ecdf(rtt, linewidth=LINEWIDTH, label=s)

                        start = datetime.strptime("16:33:00", "%H:%M:%S")
                        end = datetime.strptime("16:38:00", "%H:%M:%S")

                        timestamps = np.array(ts)

                        ts = np.array(ts)[(timestamps >= start) & (timestamps <= end)]
                        rtt = np.array(rtt)[(timestamps >= start) & (timestamps <= end)]

                        p99 = np.percentile(rtt, 99.99)

                        if "Alaska" in dirpath:
                            print("Alaska")
                            axAlaska.plot(ts, rtt, linestyle="None", marker=".", markersize=2, label="Alaska", color="blue")
                            axAlaska.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                            axAlaska.set_ylabel('RTT (ms)')
                            axAlaska.set_ylim(0, 250)
                            axAlaska.legend(loc="upper right")
                        elif "Iowa" in dirpath:
                            print("Iowa")
                            axARA.plot(ts, rtt, linestyle="None", marker=".", markersize=2, label="Iowa", color="red")
                            axARA.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                            axARA.set_xlabel("Time")
                            axARA.set_ylabel('RTT (ms)')
                            axARA.set_ylim(0, 250)
                            axARA.legend(loc="upper right")

    axECDF.set_xlabel('RTT (ms)')
    axECDF.set_ylabel('CDF')
    axECDF.set_xlim(0, max([np.percentile(latency[s], 99) for s in scenario]))
    axECDF.get_lines()[0].set_color("blue")
    axECDF.get_lines()[1].set_color("red")
    axECDF.legend(loc="best")
    plt.tight_layout()
    plt.savefig("figure4.png")
    plt.close()
