import os
import re
import json
import numpy as np
import matplotlib.pyplot as plt

from pathlib import Path
from matplotlib import dates as mdates
from datetime import timedelta, datetime
from dataclasses import dataclass


LINEWIDTH=10
markersize=20
figsize=(16, 8)
fontsize=28

plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42
plt.rcParams.update({'font.size': fontsize})
plt.rcParams.update({'axes.labelsize': fontsize})


traces = [
    "./data/bent_pipe_victoria_1_latency.csv",
    "./data/bent_pipe_victoria_2_latency.csv",
    "./data/bent_pipe_victoria_3_latency.csv",
    "./data/bent_pipe_victoria_4_latency.csv",
    "./data/bent_pipe_victoria_5_latency.csv",
    "./data/oneweb_iowa_latency.csv"
]

if __name__ == "__main__":
    for t in traces:
        with open(t, "r") as f:
            lines = f.readlines()
            ts = []
            rtt = []
            first = None
            count = 0
            for l in lines:
                # 1734546419040668928,17.8
                now = datetime.fromtimestamp(int(l.split(",")[0])/1e9)
                if first is None:
                    first = now
                if now - first > timedelta(minutes=10):
                    break
                if count % 5 == 0:
                    ts.append((now-first).total_seconds())
                    rtt.append(float(l.split(",")[1]))
                count += 1

            fig = plt.figure(figsize=figsize)
            ax = fig.add_subplot(111)
            ax.plot(ts, rtt, linestyle="None", marker=".")
            ax.set_ylabel("RTT (ms)")
            ax.set_xlabel("Time (s)")
            p99 = np.percentile(np.array(rtt), 99.99)
            if "oneweb" in t:
                ax.set_ylim(0, 400)
            else:
                ax.set_ylim(0, p99)
            plt.tight_layout()
            plt.savefig("{}.png".format(t))
            plt.close()
