import os
import re
from datetime import datetime


def load_ping(filename: str):
    print(filename)
    with open(filename, "r") as f:
        seq_list = []
        rtt_list = []
        timestamp_list = []
        for line in f.readlines():
            match = re.search(r"\[(\d+\.\d+)\].*icmp_seq=(\d+).*time=(\d+(\.\d+)?)", line)
            if match:
                timestamp = int(float(match.group(1)) * 1e9)

                seq = int(match.group(2))
                rtt = float(match.group(3))
                timestamp_list.append(timestamp)
                seq_list.append(seq)
                rtt_list.append(rtt)
    return timestamp_list, rtt_list


if __name__ == "__main__":
    filename = "./ping.txt"
    ts, rtt = load_ping(filename)
    assert len(ts) == len(rtt)

    with open("{}.csv".format(filename), "w") as f:
        for i in range(len(ts)):
            f.write("{},{}\n".format(ts[i], rtt[i]))
