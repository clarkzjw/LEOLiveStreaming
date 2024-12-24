from pprint import pprint
from textwrap import wrap
from pymongo import MongoClient
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np
from typing import Tuple, List
from collections import defaultdict
from enum import Enum
import pytz
import os
import json
import pathlib
import re


PST = pytz.timezone("US/Pacific")

FIGURE_DIR = "/figures/"
MONGO_DB_ADDR = "mongo"
MONGO_DB_NAME = "starlink"
EXPERIMENT_ID = os.getenv("EXPERIMENT_ID")
LATENCY_TARGET = os.getenv("TARGET_LATENCY")
EMULATION_MODE = False
EMULATION_TRACE_PROFILE = ""
VIDEO_PROFILE = ""


client = MongoClient("mongodb://starlink:starlink@{}:27017/".format(MONGO_DB_ADDR))
db = client[MONGO_DB_NAME]


BITRATE = "currentBitrate"
LATENCY = "currentLatency"
BUFFER = "currentBuffer"
PLAYBACK_RATE = "currentPlaybackRate"

MEDIA_TYPE_VIDEO = "video"
MEDIA_TYPE_AUDIO = "audio"
MEDIA_TYPE_STREAM = "stream"

METRIC_REP_SWITCH_LIST = "RepSwitchList"

figsize = (21, 7)


def get_result_dir() -> pathlib.PosixPath:
    if EMULATION_MODE:
        path = pathlib.Path(FIGURE_DIR).joinpath("emulation").joinpath(EMULATION_TRACE_PROFILE).joinpath(VIDEO_PROFILE).joinpath("target-{}s".format(LATENCY_TARGET)).joinpath(EXPERIMENT_ID)
    else:
        path = pathlib.Path(FIGURE_DIR).joinpath(VIDEO_PROFILE).joinpath("target-{}s".format(LATENCY_TARGET)).joinpath(EXPERIMENT_ID)
    os.makedirs(path, exist_ok=True)
    return path


def write_metric(data, filename):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


def write_metric_with_timestamp(timestamp, data, filename):
    assert(len(timestamp) == len(data))

    result = {}
    for i in range(len(timestamp)):
        # as long as dash.js stores milliseconds, this is fine
        result[timestamp[i].isoformat()] = data[i]

    with open(filename, "w") as f:
        json.dump(result, f, indent=4)


"""
mediaType: {'audio', 'video', 'stream'}
metric: {'HttpList', 'DVRInfo', 'DroppedFrames',
         'BufferState', 'BufferLevel', 'SchedulingInfo',
         'RequestsQueue', 'ManifestUpdate', 'RepSwitchList'}
"""

def get_event_data(mediaType, metric: str) -> list:
    cursor = db["events-{}".format(EXPERIMENT_ID)].find({})
    events = []
    for c in cursor:
        for m in c.get("type"):
            if isinstance(m, dict):
                events.append(m)

    event_data = []
    for e in events:
        e = e["event"]
        if "metric" in e.keys():
            if e["metric"] == metric and e["mediaType"] == mediaType:
                event_data.append(e["value"])

    return event_data


def get_metric_data(metricKey: str) -> Tuple[list[datetime], list[float]]:
    cursor = db["metric-{}".format(EXPERIMENT_ID)].find({})
    metrics = []
    for c in cursor:
        for m in c.get("type"):
            if isinstance(m, dict):
                if m["experimentID"] == EXPERIMENT_ID:
                    metrics.append(m)

    timestamp = []
    data = []

    for m in metrics:
        epoch = m["time"]
        date_obj = datetime.strptime(epoch, '%Y-%m-%d %H:%M:%S:%f')

        if m[metricKey] != "" and m[metricKey] != None:
            data.append(float(m[metricKey]))
            timestamp.append(date_obj)
        else:
            data.append(0.0)
            timestamp.append(date_obj)

    assert(len(timestamp) == len(data))
    return timestamp, data


def plot_bitrate_switch_temporal():
    timestamp, bitrates = get_metric_data(BITRATE)

    rep_switch_events = get_event_data(MEDIA_TYPE_VIDEO, METRIC_REP_SWITCH_LIST)
    timestamp2 = []
    events = []
    for e in rep_switch_events:
        date_obj = datetime.strptime(e["t"], '%Y-%m-%dT%H:%M:%S.%fZ').astimezone(PST).strftime('%Y-%m-%d %H:%M:%S.%f')
        date_obj = datetime.strptime(date_obj, '%Y-%m-%d %H:%M:%S.%f')
        timestamp2.append(date_obj)
        events.append(1)

    fig = plt.figure(figsize = figsize)
    ax = fig.add_subplot(1, 1, 1)

    ax.plot(timestamp2, events, label="Rep Switch", linestyle='None', marker="x")
    ax.plot(timestamp, bitrates, label="bitrate (Kbps)")
    ax.legend(loc="upper left")

    plt.xlabel("Seconds")
    plt.ylabel("Playback bitrate (Kbps)")
    plt.tight_layout()
    plt.savefig(get_result_dir().joinpath("bitrate_switch.png"))
    plt.close()

    write_metric_with_timestamp(timestamp, bitrates, get_result_dir().joinpath("bitrates.json"))
    write_metric(rep_switch_events, get_result_dir().joinpath("bitrate_switch.json"))


def plot_buffer_temporal():
    timestamp, buffer = get_metric_data(BUFFER)

    fig = plt.figure(figsize = figsize)
    ax = fig.add_subplot(1, 1, 1)

    ax.plot(timestamp, buffer, label="Buffer (second)")
    ax.legend(loc="upper left")
    plt.xlabel("Seconds")
    plt.ylabel("Playback buffer (second)")
    plt.tight_layout()
    plt.savefig(get_result_dir().joinpath("buffer.png"))
    plt.close()

    write_metric_with_timestamp(timestamp, buffer, get_result_dir().joinpath("buffer.json"))


def plot_playback_rate_temporal():
    timestamp, playback_rate = get_metric_data(PLAYBACK_RATE)

    fig = plt.figure(figsize = figsize)
    ax = fig.add_subplot(1, 1, 1)

    ax.plot(timestamp, playback_rate, label="Playback rate")
    ax.legend(loc="upper left")
    plt.xlabel("Seconds")
    plt.ylabel("Playback rate")
    plt.tight_layout()
    plt.savefig(get_result_dir().joinpath("playback_rate.png"))
    plt.close()

    write_metric_with_timestamp(timestamp, playback_rate, get_result_dir().joinpath("playback_rate.json"))


def plot_buffer_latency():
    timestamp, buffer = get_metric_data(BUFFER)
    timestamp, latency = get_metric_data(LATENCY)

    fig = plt.figure(figsize = figsize)
    ax = fig.add_subplot(1, 1, 1)

    ax.plot(timestamp, buffer, label="Buffer (second)")
    ax.plot(timestamp, latency, label="Latency to Live (second)")

    ax.legend(loc="upper left")
    plt.xlabel("Seconds")
    plt.tight_layout()
    plt.savefig(get_result_dir().joinpath("buffer-latency.png"))
    plt.close()

    write_metric_with_timestamp(timestamp, latency, get_result_dir().joinpath("playback_latency.json"))


def plot_bitrate_by_second():
    timestamp, bitrate = get_metric_data(BITRATE)
    result = defaultdict(list[float])
    for i in range(len(timestamp)):
        t = timestamp[i]
        b = bitrate[i]
        result[t.isoformat()].append(b)

    averaged_bitrate_by_second = []
    for k in result:
        averaged_bitrate_by_second.append(np.average(result[k]))

    fig = plt.figure(figsize = figsize)
    ax = fig.add_subplot(1, 1, 1)

    ax.plot(averaged_bitrate_by_second)
    plt.tight_layout()
    plt.savefig(get_result_dir().joinpath("bitrate_by_second.png"))
    plt.close()

    write_metric(averaged_bitrate_by_second, get_result_dir().joinpath("bitrate_by_second.json"))


def plot_qoe(qoe):
    plt.plot(qoe, label="QoE", linestyle='None', marker="x")
    plt.legend(loc="upper left")
    plt.ylabel("QoE")
    plt.savefig(get_result_dir().joinpath("qoe.png"))
    plt.close()


def time_series_plot(filename: str, timestamp: list[int], rtt_list: list[float]) -> None:
    assert(len(timestamp) == len(rtt_list))

    fig = plt.figure(figsize =(21, 7))
    ax = fig.add_subplot(111)

    ax.plot(timestamp, rtt_list, '.')
    plt.title(filename+"_latency")
    plt.tight_layout()

    filename = get_result_dir().joinpath(str(filename) + "-ping.png")
    plt.savefig(filename)
    plt.close()


def plot_ping():
    filename = "ping-{}.txt".format(EXPERIMENT_ID)

    with open(filename, "r") as f:
        count = 0
        seq_list = []
        rtt_list = []
        timestamp_list = []
        for line in f.readlines():
            match = re.search(r"\[(\d+\.\d+)\].*icmp_seq=(\d+).*time=(\d+(\.\d+)?)", line)
            if match:
                count += 1
                timestamp = float(match.group(1))
                seq = int(match.group(2))
                rtt = float(match.group(3))
                timestamp_list.append(timestamp)
                seq_list.append(seq)
                rtt_list.append(rtt)

        assert(len(timestamp_list) == len(rtt_list))
        time_series_plot(filename, timestamp_list, rtt_list)
        os.system("cp {} {}".format(filename, get_result_dir().joinpath(filename)))


def write_qoe():
    cursor = db["qoe-{}".format(EXPERIMENT_ID)].find({})
    qoe = []
    arms = []
    live_latency = []
    for c in cursor:
        for m in c.get("type"):
            if m == "reward_qoe":
                qoe.append(c["type"]["reward_qoe"])
            elif m == "arm":
                arms.append(c["type"]["arm"])
            elif m == "currentLiveLatency":
                live_latency.append(c["type"]["currentLiveLatency"])

    plot_qoe(qoe)
    write_metric(qoe, get_result_dir().joinpath("qoe.json"))
    write_metric(arms, get_result_dir().joinpath("arms.json"))
    write_metric(live_latency, get_result_dir().joinpath("currentLiveLatency.json"))


def generate_plots(EXP_ID: str, ROUND_DURATION, TARGET_LATENCY, CONSTANT_VIDEO_BITRATE: int, EMULATION: bool, EMULATION_PROFILE: str, VIDEO: str):
    global EXPERIMENT_ID
    global LATENCY_TARGET
    global EMULATION_MODE
    global EMULATION_TRACE_PROFILE
    global VIDEO_PROFILE
    EXPERIMENT_ID = EXP_ID
    LATENCY_TARGET = TARGET_LATENCY
    EMULATION_MODE = EMULATION
    EMULATION_TRACE_PROFILE = EMULATION_PROFILE
    VIDEO_PROFILE = VIDEO

    plot_buffer_temporal()
    plot_bitrate_by_second()
    plot_bitrate_switch_temporal()
    plot_playback_rate_temporal()
    plot_buffer_latency()
    plot_ping()
    write_qoe()
