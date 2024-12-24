import os
import sys
import json
import asyncio
import motor.motor_asyncio
import numpy as np
from matplotlib import pyplot as plt
from pathlib import Path
from pprint import pprint
from dataclasses import dataclass
from collections import defaultdict
from datetime import datetime, timedelta

from config import L2A, Dynamic, LoLP, CMAB, DATA_DIR, TITLE, SCENARIO_SET, figsize, BITRATE_LIST_LENGTH, FIGURE_DIR, VIDEO_PROFILE, ensure_dir


MONGO_HOST = os.getenv("MONGO_HOST", "localhost")


async def get_all_events(experiment_id):
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://starlink:starlink@{}:27017/".format(MONGO_HOST))
    db = client["starlink"]
    return await db["events-{}".format(experiment_id)].find().to_list()


def get_playback_start_time(events):
    for event in events:
        if isinstance(event["type"], list):
            for e in event["type"]:
                ts = e["ts"]
                e = e["event"]
                if e.get("type") == "metricAdded" and e.get("metric") == "HttpList":
                    return datetime.fromtimestamp(float(ts) / 1000)

def get_cmab_init_done_time(events):
    for event in events:
        if isinstance(event["type"], dict):
            e = event["type"]["event"]
            ts = event["type"]["ts"]
            if e.get("type") == "pyodide_init_done":
                return datetime.fromtimestamp(float(ts) / 1000)


def get_cmab_init_explore_finish_time(events):
    for event in events:
        if isinstance(event["type"], dict):
            ts = event["type"]["ts"]
            e = event["type"]["event"]
            if e.get("type") == "cmab_initial_explore_done":
                print("cmab init explore done: ", datetime.fromtimestamp(float(ts) / 1000))
                return datetime.fromtimestamp(float(ts) / 1000)


def get_per_round_stall_duration_from_mongo(experiment_id: str, alg: str):
    metric_type = []
    rebuffering_duration = 0
    buffer_drop_below_stall_threshold = 0

    last_playback_stalled = None
    first_playback_stalled = None
    last_buffer_level = None

    last_event_ts = None

    all_events = asyncio.run(get_all_events(experiment_id))
    playback_start_time = get_playback_start_time(all_events)
    if alg == CMAB:
        cmab_playback_start_time = get_cmab_init_done_time(all_events)

    for event in all_events:
        if isinstance(event["type"], list):
            for e in event["type"]:
                ts = e["ts"]
                if alg == CMAB:
                    if datetime.fromtimestamp(float(ts) / 1000) < cmab_playback_start_time:
                        continue
                e = e["event"]
                last_event_ts = datetime.fromtimestamp(float(ts) / 1000)
                if "mediaType" not in e or e["mediaType"] != "video":
                    continue
                if e["type"] not in metric_type:
                    metric_type.append(e["type"])

                if e["type"] == "bufferStalled":
                    buffer_drop_below_stall_threshold += 1

                if e["type"] == "bufferLevelUpdated":
                    if e["bufferLevel"] == 0:
                        if (last_buffer_level == None) or (last_buffer_level != 0):
                            last_buffer_level = e["bufferLevel"]
                            ts = float(ts) / 1000
                            last_playback_stalled = datetime.fromtimestamp(ts)
                    elif e["bufferLevel"] != 0:
                        if last_playback_stalled is not None:
                            last_buffer_level = e["bufferLevel"]
                            ts = float(ts) / 1000
                            duration = (datetime.fromtimestamp(ts) - last_playback_stalled).total_seconds()
                            rebuffering_duration += duration
                            last_playback_stalled = None

    total_duration = (last_event_ts - playback_start_time).total_seconds()
    print("total duration: ", total_duration, "rebuffering duration: ", rebuffering_duration)
    ratio = rebuffering_duration / total_duration * 100
    return ratio, buffer_drop_below_stall_threshold


def get_per_round_stall_duration(dirpath: Path, alg: str):
    if "emulation" in str(dirpath):
        exp_list = str(dirpath).split("/")[3:]
        experiment_id = "-".join(exp_list)
        experiment_id = "-".join(experiment_id.split("-")[4:])
    else:
        exp_list = str(dirpath).split("/")[2:]
        experiment_id = "-".join(exp_list)
        experiment_id = "-".join(experiment_id.split("-")[3:])
    print(experiment_id)
    return get_per_round_stall_duration_from_mongo(experiment_id, alg)


def stall_duration_by_target_latency(prefix: str):
    for g in SCENARIO_SET:
        for vp in VIDEO_PROFILE:
            fig = plt.figure(figsize = figsize)

            result = defaultdict(list)
            result_buffer_health = defaultdict(list)

            ax = fig.add_subplot(1, 1, 1)
            for targetLatency in range(3, 7, 1):
                arrL2A = []
                arrDynamic = []
                arrLoLP = []
                arrCMAB = []

                bufferHealthL2A = []
                bufferHealthDynamic = []
                bufferHealthLoLP = []
                bufferHealthCMAB = []

                for dirpath, dirnames, files in os.walk(prefix):
                    if len(files) != 0:
                        if "target-{}s".format(str(targetLatency)) not in dirpath:
                            continue
                        if "variable" not in dirpath:
                            continue
                        if vp not in dirpath:
                            continue
                        print(dirpath)
                        if L2A in dirpath:
                            ratio, buffer_drop_below_stall_threshold = get_per_round_stall_duration(Path(dirpath), L2A)
                            arrL2A.append(ratio)
                            bufferHealthL2A.append(buffer_drop_below_stall_threshold)
                        elif Dynamic in dirpath:
                            ratio, buffer_drop_below_stall_threshold = get_per_round_stall_duration(Path(dirpath), Dynamic)
                            arrDynamic.append(ratio)
                            bufferHealthDynamic.append(buffer_drop_below_stall_threshold)
                        elif LoLP in dirpath:
                            ratio, buffer_drop_below_stall_threshold = get_per_round_stall_duration(Path(dirpath), LoLP)
                            arrLoLP.append(ratio)
                            bufferHealthLoLP.append(buffer_drop_below_stall_threshold)
                        elif CMAB in dirpath:
                            ratio, buffer_drop_below_stall_threshold = get_per_round_stall_duration(Path(dirpath), CMAB)
                            arrCMAB.append(ratio)
                            bufferHealthCMAB.append(buffer_drop_below_stall_threshold)

                result[L2A].append(np.average(arrL2A))
                result[Dynamic].append(np.average(arrDynamic))
                result[LoLP].append(np.average(arrLoLP))
                result[CMAB].append(np.average(arrCMAB))

                result_buffer_health[L2A].append(np.average(bufferHealthL2A))
                result_buffer_health[Dynamic].append(np.average(bufferHealthDynamic))
                result_buffer_health[LoLP].append(np.average(bufferHealthLoLP))
                result_buffer_health[CMAB].append(np.average(bufferHealthCMAB))

            ############################
            bar_width = 0.15
            index = np.arange(len(result[Dynamic]))

            ax.bar(index, result[L2A], bar_width, label="L2A-LL", color='tab:blue')
            ax.bar(index + bar_width, result[Dynamic], bar_width, label="Dynamic", color='tab:orange')
            ax.bar(index + 2*bar_width, result[LoLP], bar_width, label="LoL+", color='tab:green')
            ax.bar(index + 3*bar_width, result[CMAB], bar_width, label="CMAB", color='tab:brown')

            plt.xticks(np.arange(4), np.arange(3, 7))
            plt.xlabel("Latency Target (seconds)")

            plt.ylabel("Rebuffering Time Ratio (%)")
            plt.ylim(0, 0.2)

            plt.legend(loc="upper right")
            plt.tight_layout()
            ensure_dir("{}/{}".format(FIGURE_DIR, vp))
            plt.savefig("{}/{}/average_rebuffering_time_percentage_".format(FIGURE_DIR, vp) + TITLE[g] + ".png")
            plt.savefig("{}/{}/average_rebuffering_time_percentage_".format(FIGURE_DIR, vp) + TITLE[g] + ".eps")
            plt.clf()
            plt.close()
            ############################

            fig = plt.figure(figsize = figsize)
            ax = fig.add_subplot(1, 1, 1)
            ax.bar(index, result_buffer_health[L2A], bar_width, label="L2A-LL", color='tab:blue')
            ax.bar(index + bar_width, result_buffer_health[Dynamic], bar_width, label="Dynamic", color='tab:orange')
            ax.bar(index + 2*bar_width, result_buffer_health[LoLP], bar_width, label="LoL+", color='tab:green')
            ax.bar(index + 3*bar_width, result_buffer_health[CMAB], bar_width, label="CMAB", color='tab:brown')

            plt.xticks(np.arange(4), np.arange(3, 7))
            plt.xlabel("Latency Target (seconds)")
            plt.ylabel("Buffer Below Threshold")

            plt.legend(loc="best")
            plt.tight_layout()
            ensure_dir("{}/{}".format(FIGURE_DIR, vp))
            plt.savefig("{}/{}/average_buffer_health_".format(FIGURE_DIR, vp) + TITLE[g] + ".png")
            plt.savefig("{}/{}/average_buffer_health_".format(FIGURE_DIR, vp) + TITLE[g] + ".eps")
            plt.clf()
            plt.close()


if __name__ == "__main__":
    stall_duration_by_target_latency(DATA_DIR)