import os
import re
import sys
import time
import socket
import datetime
import schedule
import threading
import subprocess

import motor.motor_asyncio
import numpy as np
import asyncio

from pprint import pprint
from dataclasses import dataclass

from quart import Quart, websocket
from quart import request, jsonify
from quart_cors import cors, route_cors


app = Quart(__name__)
no_cors = cors(app)


POST = ["POST"]
GET  = ["GET"]

eventDb = []

app.config['CORS_HEADERS'] = 'Access-Control-Allow-Origin'

MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://starlink:starlink@{}:27017/".format(MONGO_HOST))

db = client["starlink"]

count = 0
ping_thread = None
last_value = -1
current_experiment_id = None

DEFAULT_GW = os.getenv("GATEWAY", "1.1.1.1")
INTERFACE = os.getenv("INTERFACE")
PING_INTERVAL = os.getenv("LATENCY_TEST_INTERVAL_SECONDS", "1")


class StoppableThread(threading.Thread):
    def __init__(self, hostname):
        super().__init__()
        self.hostname = hostname
        self.stop_flag = False

    def run(self):
        addrs = [ str(i[4][0]) for i in socket.getaddrinfo(self.hostname, 80) ]
        if len(addrs) > 0:
            HOST = addrs[0]
        else:
            HOST = self.hostname

        while not self.stop_flag:
            ping(hostname=HOST)
            time.sleep(float(PING_INTERVAL))

    def stop(self):
        self.stop_flag = True


@dataclass
class PingMetric:
    timestamp: float
    seq_no: int
    rtt: float = 0.0


ping_metric = list[PingMetric]()


def ping(hostname: str) -> None:
    global count
    global last_value
    count += 1

    try:
        if not INTERFACE:
            output = subprocess.check_output(["ping", "-D", "-W", "1", "-c", "1", hostname])
        else:
            output = subprocess.check_output(["ping", "-D", "-I", INTERFACE, "-W", "1", "-c", "1", hostname])
        line = output.decode("utf-8")
        # without -D option
        # match = re.search(r"icmp_seq=(\d+).*time=(\d+\.\d+)", line)
        # with -D option
        # [1726782115.933582] 64 bytes from 1.1.1.1: icmp_seq=1 ttl=59 time=9.10 ms
        match = re.search(r"\[(\d+\.\d+)\].*icmp_seq=(\d+).*time=(\d+(\.\d+)?)", line)
        if match:
            timestamp = float(match.group(1))
            rtt = float(match.group(3))
            pm = PingMetric(timestamp, count, rtt)
            last_value = rtt
            ping_metric.append(pm)

    except subprocess.CalledProcessError as e:
        print(e.output)
        pm = PingMetric(time.time(), count, last_value)
        ping_metric.append(pm)


def get_current_timeslot_start_end(now: float = None):
    if not now:
        now = time.time()
    now = datetime.datetime.fromtimestamp(now)
    if (now.second >= 12 and now.second < 27):
        start = now.replace(second=12, microsecond=0)
        end = start + datetime.timedelta(seconds=15)
    elif (now.second >= 27 and now.second < 42):
        start = now.replace(second=27, microsecond=0)
        end = start + datetime.timedelta(seconds=15)
    elif (now.second >= 42 and now.second < 57):
        start = now.replace(second=42, microsecond=0)
        end = start + datetime.timedelta(seconds=15)
    elif (now.second >= 57 and now.second < 60):
        start = now.replace(second=57, microsecond=0)
        end = start + datetime.timedelta(seconds=15)
    elif (now.second >= 0 and now.second < 12):
        start = (now - datetime.timedelta(minutes=1)).replace(second=57, microsecond=0)
        end = start + datetime.timedelta(seconds=15)
    return start, end


def get_history_latency():
    current_start, current_end = get_current_timeslot_start_end()
    ping_metric.sort(key=lambda x: x.timestamp)
    # get the first timeslot in the current session
    earliest_start, earliest_end = get_current_timeslot_start_end(ping_metric[0].timestamp)
    history = []
    while earliest_start <= current_start:
        # filter every timeslot
        filtered = list(filter(lambda x: x.timestamp >= earliest_start.timestamp() and x.timestamp <= earliest_end.timestamp(), ping_metric))
        mean = 0
        if len(filtered) > 0:
            mean = np.mean([x.rtt for x in filtered])
            std = np.std([x.rtt for x in filtered])
            history.append({
                "start": earliest_start.timestamp(),
                "end": earliest_end.timestamp(),
                "mean": mean,
                "std": std
            })
        earliest_start, earliest_end = get_current_timeslot_start_end(earliest_start.timestamp() + 15)

    history.sort(key=lambda x: x["start"])
    return history


def get_history_throughput():
    results = eventDb
    throughput_history = []

    for r in results:
        for obj in r["type"]:
            if type(obj) is not list:
                continue
            obj = obj["event"]
            if type(obj) is not dict:
                continue
            if obj["type"] == "throughputMeasurementStored":
                if obj["mediaType"] == "video":
                    throughput_history.append({
                        "timestamp": datetime.datetime.strptime(obj["httpRequest"]["tresponse"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=datetime.timezone.utc).timestamp(),
                        "tresponse": obj["httpRequest"]["tresponse"],
                        "throughput": float(obj["throughput"])/1000.0
                    })

    throughput_history.sort(key=lambda x: x["timestamp"])

    if len(throughput_history) == 0:
        return []

    current_start, current_end = get_current_timeslot_start_end()
    earliest_start, earliest_end = get_current_timeslot_start_end(throughput_history[0]["timestamp"])
    history = []
    while earliest_start <= current_start:
        current_timeslot = list(filter(lambda x: x["timestamp"] >= earliest_start.timestamp() and x["timestamp"] <= earliest_end.timestamp(), throughput_history))

        if len(current_timeslot) > 0:
            history.append({
                "start": earliest_start.timestamp(),
                "end": earliest_end.timestamp(),
                "mean": np.mean([x["throughput"] for x in current_timeslot]),
                "std": np.std([x["throughput"] for x in current_timeslot])
            })
        earliest_start, earliest_end = get_current_timeslot_start_end(earliest_start.timestamp() + 15)

    history.sort(key=lambda x: x["start"])
    return history


def schedule_thread():
    while True:
        schedule.run_pending()
        time.sleep(0.1)


@app.route("/event/initDone", methods=POST)
@route_cors()
async def playback_initDone():
    global current_experiment_id

    collection = "initDone-{}".format(current_experiment_id)
    await db[collection].insert_one({"timestamp": time.time()})
    current_experiment_id = current_experiment_id

    return jsonify("Succeed")


@app.route("/event/initDone/<experimentID>", methods=GET)
@route_cors()
async def check_playback_initDone(experimentID):
    collection = "initDone-{}".format(experimentID)
    result = db[collection].find_one()
    if not result:
        return jsonify(0), 404
    return jsonify(1), 200


@app.route("/ping", methods=GET)
@route_cors()
async def get_ping_latest():
    if len(ping_metric) > 0:
        return jsonify(ping_metric[-1].rtt)
    else:
        return jsonify(0)


@app.route("/pingstats", methods=GET)
@route_cors()
async def get_ping_stats():
    return jsonify(get_history_latency())


@app.route("/throughputstats", methods=GET)
@route_cors()
async def get_throughput_stats():
    return jsonify(get_history_throughput())


### Main API endpoints for each experiment
async def insert_one_data(collection_name, data):
    await db[collection_name].insert_one(data)


@app.route("/metric/<experimentID>", methods=POST)
@route_cors()
async def playback_metric(experimentID):
    metric = await request.get_json()
    asyncio.create_task(insert_one_data("metric-{}".format(experimentID), metric))

    return jsonify("Succeed"), 200


@app.route("/qoe/<experimentID>", methods=POST)
@route_cors()
async def qoe(experimentID):
    qoe = await request.get_json()
    asyncio.create_task(insert_one_data("qoe-{}".format(experimentID), qoe))

    return jsonify("Succeed"), 200


@app.route("/event/<experimentID>", methods=POST)
@route_cors()
async def playback_event(experimentID):
    global eventDb

    event = await request.get_json()
    eventDb.append(event)

    asyncio.create_task(insert_one_data("events-{}".format(experimentID), event))

    return jsonify("Succeed"), 200


@app.route("/stop/<experimentID>", methods=POST)
@route_cors()
async def stop_experiment(experimentID):
    global current_experiment_id

    print("Stop experiment {}".format(experimentID))
    current_experiment_id = None
    ping_metric.clear()
    eventDb.clear()

    return jsonify("Succeed"), 200


if __name__ == "__main__":
    if not INTERFACE:
        print("Environment variable INTERFACE is empty, default interface will be used for latency tests")

    print("Latency tests interval: {}s".format(PING_INTERVAL))

    p = threading.Thread(target=schedule_thread)
    p.start()

    ping_thread = StoppableThread(DEFAULT_GW)
    ping_thread.start()

    app.run(host="0.0.0.0", port=8000)
