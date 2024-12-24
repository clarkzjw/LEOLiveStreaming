import os
import json
import datetime
import itertools
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from pprint import pprint
from pathlib import Path
from datetime import timedelta
from matplotlib.lines import Line2D


fontsize = 25
figsize=(20, 10)
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42
plt.rc('font', size=fontsize)
plt.rc('axes', labelsize=fontsize)


def duplicate_object_pairs_hook(pairs):
    def _key(pair):
        (k, v) = pair
        return k
    def gpairs():
        for (k, group) in itertools.groupby(pairs, _key):
            ll = [v for (_, v) in group]
            (v, *extra) = ll
            yield (k, ll if extra else v)
    return dict(gpairs())


def plot(dir: str, date_prefix: str):
    iperf3_filename = Path(dir).joinpath("iperf3-20m-{}.json".format(date_prefix))
    irtt_filename = Path(dir).joinpath("irtt-10ms-20m-{}.json".format(date_prefix))

    try:
        with open(irtt_filename, "r") as f:
            data = json.loads(f.read())
            rtt = []
            receive = []
            send = []
            irtt_timestamps = []

            for round in data["round_trips"]:
                irtt_timestamps.append(datetime.datetime.fromtimestamp(float(round["timestamps"]["client"]["send"]["wall"])/1e9))
                if round["lost"] == "true":
                    rtt.append(-1)
                    receive.append(-100)
                    send.append(-100)
                elif round["lost"] == "true_up":
                    rtt.append(-100)
                    send.append(-1)
                    receive.append(-100)
                elif round["lost"] == "true_down":
                    rtt.append(-100)
                    receive.append(-1)
                    send.append(-100)
                else:
                    rtt.append(float(round["delay"]["rtt"])/1000000)
                    receive.append(float(round["delay"]["receive"])/1000000)
                    send.append(float(round["delay"]["send"])/1000000)

    except json.decoder.JSONDecodeError:
        print("JSONDecodeError: ", irtt_filename)
        return
    except OSError:
        print("FileNotFoundError: ", iperf3_filename)
        return

    try:
        with open(iperf3_filename, "r") as f:
            data = json.loads(f.read(), object_pairs_hook=duplicate_object_pairs_hook)
            recv_mbps = []
            iperf3_timestamps = []
            start_ts = float(data["start"]["timestamp"]["timesecs"])

            for round in data["intervals"]:
                sum = round["sum"]
                iperf3_timestamps.append(datetime.datetime.fromtimestamp(start_ts + sum["end"]))
                recv_mbps.append(float(sum["bits_per_second"])/1000000)
                # if --bidir is used
                # for s in sum:
                #     if s["sender"] == False:
                #         recv_mbps.append(float(s["bits_per_second"])/1000000)
                #     elif s["sender"] == True:
                #         send_mbps.append(float(s["bits_per_second"])/1000000)

    except json.decoder.JSONDecodeError:
        print("JSONDecodeError: ", iperf3_filename)
        return
    except OSError:
        print("FileNotFoundError: ", iperf3_filename)
        return

    start = 0.023
    end = 0.13

    rtt = rtt[int(len(rtt)*start):int(len(rtt)*end)]
    send = send[int(len(send)*start):int(len(send)*end)]
    receive = receive[int(len(receive)*start):int(len(receive)*end)]
    recv_mbps = recv_mbps[int(len(recv_mbps)*start):int(len(recv_mbps)*end)]
    irtt_timestamps = irtt_timestamps[int(len(irtt_timestamps)*start):int(len(irtt_timestamps)*end)]
    iperf3_timestamps = iperf3_timestamps[int(len(iperf3_timestamps)*start):int(len(iperf3_timestamps)*end)]

    fig, (ax1, ax4) = plt.subplots(2, 1, figsize=figsize, sharex=True)

    ax1.tick_params(axis='x', labelsize=14, length=10, width=4)
    ax4.tick_params(axis='x', labelsize=14, length=10, width=4)

    seconds = [12, 27, 42, 57]

    handovers = []
    for ax, timestamps in zip([ax1, ax4], [iperf3_timestamps, irtt_timestamps]):
        for timestamp in timestamps:
            for s in seconds:
                line_time = timestamp.replace(second=s, microsecond=0)
                handovers.append(line_time)

    for t in sorted(list(set(handovers))):
        if t < max(irtt_timestamps) and t < max(iperf3_timestamps) and t > min(irtt_timestamps) and t > min(iperf3_timestamps):
            ax1.axvline(t, color='r', linestyle='--')
            ax4.axvline(t, color='r', linestyle='--')

    ax1.plot(irtt_timestamps, rtt, '.')
    ax1.set_xlim(min(min(irtt_timestamps), min(iperf3_timestamps)), max(max(irtt_timestamps), max(iperf3_timestamps)))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    ax1.set_ylim(0, max(rtt))
    ax1.set_ylabel("Latency (ms)")
    ax1.set_title("RTT")

    ax4.tick_params(axis='x', which='major', labelsize=fontsize)
    ax4.plot(iperf3_timestamps, recv_mbps)
    ax4.set_xlim(min(min(irtt_timestamps), min(iperf3_timestamps)), max(max(irtt_timestamps), max(iperf3_timestamps)))
    ax4.set_ylim(-1, max(recv_mbps)*1.1)
    ax4.set_xlabel("Time")
    ax4.set_ylabel("Throughput (Mbps)")
    ax4.set_title("Downlink Throughput (UDP)")

    handover_line = Line2D([0], [0], color='r', linestyle='--', label='Handover Timestamp')
    ax1.legend(handles=[handover_line])

    plt.tight_layout()
    plt.savefig(Path(dir).joinpath("{}.png".format(date_prefix)))
    plt.close()


if __name__ == "__main__":
    path = Path("./data")
    for dirpath, dirnames, files in os.walk(path):
        if len(files) != 0:
            for f in files:
                if f.endswith(".json") and f.startswith("iperf3"):
                        date_prefix = "-".join(f.split(".")[0].split("-")[2:8])
                        plot(dirpath, date_prefix)
