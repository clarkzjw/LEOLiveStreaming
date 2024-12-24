import struct
import subprocess
import argparse
import time
from pathlib import Path
from threading import Thread
import datetime
import pandas as pd
import os
from datetime import timedelta


dev = os.getenv("IFCE", "eth1")
handover_latency = 500


def exec_tc_latency(rtt, loss_rate=0):
    update_cmd_rtt = f'tc qdisc change dev {dev} parent 1:1 handle 10: netem delay {rtt}ms loss {loss_rate}'
    try:
        subprocess.run(update_cmd_rtt, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(e)


def exec_tc_bw(mbps):
    update_cmd_bw = f'tc qdisc change dev {dev} root handle 1: tbf rate {mbps}mbit burst 15k latency 50ms'
    try:
        subprocess.run(update_cmd_bw, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(e)


def init():
    try:
        subprocess.check_output(["tc", "qdisc", "add", "dev", dev, "root", "handle", "1:", "tbf", "rate", "100mbit", "burst", "16kbit", "latency", "40ms" ])
        subprocess.check_output(["tc", "qdisc", "add", "dev", dev, "parent", "1:1", "handle", "10:", "netem", "delay", "40ms"])
    except subprocess.CalledProcessError as e:
        print(e)


def tc_del():
    try:
        subprocess.check_output(["tc", "qdisc", "del", "dev", dev, "root"])
    except subprocess.CalledProcessError as e:
        print(e)


def update_tc_latency(filename):
    with open(filename, "r") as f:
        data = f.readlines()

    start_time = datetime.datetime.fromtimestamp(float(data[0].split(",")[0]) / 1e9)
    now = pd.to_datetime(datetime.datetime.now(), format="%Y-%m-%dT%H:%M:%S.%f%z")

    start_time = start_time.replace(tzinfo=None).replace(day=now.day, month=now.month, year=now.year, hour=now.hour, minute=now.minute)
    diff = start_time - now
    if diff.total_seconds() < 0:
        # start_time = start_time.replace(minute=start_time.minute + 1)
        start_time = start_time + timedelta(minutes=1)
    diff = start_time - now

    print("starting in: {}".format(diff.total_seconds()))
    time.sleep(diff.total_seconds())

    for index in range(len(data)):
        # 1699783800453306834,44.418749,28.530506,15.888176
        # timestamp, rtt, _, _ = data[index].split(",")
        timestamp, rtt = data[index].split(",")
        rtt = float(rtt)
        if rtt > 0:
            exec_tc_latency(round(rtt))
        else:
            exec_tc_latency(handover_latency, 1)
        if index + 1 < len(data):
            # next_timestamp, _, _, _ = data[index + 1].split(",")
            next_timestamp, _, = data[index + 1].split(",")
            sleep_time = float(next_timestamp)/1e9 - float(timestamp)/1e9
            time.sleep(round(sleep_time, 3))


# def update_tc_bw(filename):
#     with open(filename, "r") as f:
#         data = f.readlines()

#     start_time = datetime.datetime.fromtimestamp(float(data[0].split(",")[0]) / 1e9)
#     now = pd.to_datetime(datetime.datetime.now(), format="%Y-%m-%dT%H:%M:%S.%f%z")

#     start_time = start_time.replace(tzinfo=None).replace(day=now.day, month=now.month, year=now.year, hour=now.hour, minute=now.minute)
#     diff = start_time - now
#     if diff.total_seconds() < 0:
#         start_time = start_time.replace(minute=start_time.minute + 1)
#     diff = start_time - now

#     print("starting in: {}".format(diff.total_seconds()))
#     time.sleep(diff.total_seconds())

#     for index in range(len(data)):
#         # 1699783800000000000,18.211382010948572,4.552845502737143
#         timestamp, _, recv = data[index].split(",")
#         bw = float(recv)
#         if bw > 0:
#             exec_tc_latency(round(bw))
#         if index + 1 < len(data):
#             next_timestamp, _, _ = data[index + 1].split(",")
#             sleep_time = float(next_timestamp)/1e9 - float(timestamp)/1e9
#             time.sleep(round(sleep_time, 3))


if __name__ == "__main__":
    scenario = os.getenv("SCENARIO", "bent_pipe")

    LATENCY_FILE = scenario+"_latency.csv"
    THROUGHPUT_FILE = scenario+"_throughput.csv"

    init()

    th1 = Thread(target=update_tc_latency, args=(LATENCY_FILE, ))
    # th2 = Thread(target=update_tc_bw, args=(THROUGHPUT_FILE, ))

    th1.start()
    # th2.start()
    th1.join()
    # th2.join()
