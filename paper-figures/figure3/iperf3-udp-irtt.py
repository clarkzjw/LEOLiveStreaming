import os
import re
import sys
import time
import time
import schedule
import threading
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta


INTERVAL = os.getenv("INTERVAL", "10ms")
DURATION = os.getenv("DURATION", "10m")
IRTT_LOCAL_IP = os.getenv("LOCAL_IP", "\[2607:f8f0:xxxx\]")
IPERF_LOCAL_IP = os.getenv("LOCAL_IP", "2607:f8f0:xxxx")
IRTT_HOST_PORT = os.getenv("SERVER", "\[2605:59c8:xxxx\]")
IPERF3_HOST = os.getenv("IPERF3_SERVER", "2605:59c8:xxxx")


# https://gist.github.com/santiagobasulto/698f0ff660968200f873a2f9d1c4113c
TIMEDELTA_REGEX = (r'((?P<days>-?\d+)d)?'
                   r'((?P<hours>-?\d+)h)?'
                   r'((?P<minutes>-?\d+)m)?'
                   r'((?P<minutes>-?\d+)s)?')
TIMEDELTA_PATTERN = re.compile(TIMEDELTA_REGEX, re.IGNORECASE)


def parse_delta(delta):
    """ Parses a human readable timedelta (3d5h19m) into a datetime.timedelta.
    Delta includes:
    * Xd days
    * Xh hours
    * Xm minutes
    Values can be negative following timedelta's rules. Eg: -5h-30m
    """
    match = TIMEDELTA_PATTERN.match(delta)
    if match:
        parts = {k: int(v) for k, v in match.groupdict().items() if v}
        return timedelta(**parts)


DURATION_SECONDS = str(parse_delta(DURATION).seconds)


def test_command(command: str) -> bool:
    from shutil import which
    return which(command) is not None

def run(func):
    job_thread = threading.Thread(target=func)
    job_thread.start()


def check_directory() -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    Path("data/{}".format(today)).mkdir(parents=True, exist_ok=True)
    return today


def timestring() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d-%H-%M-%S")


def failed(e: str) -> None:
    with open("data/failed.txt", "a+") as f:
        f.write("{}\n".format(e))


def irtt_ping() -> None:
    today = check_directory()
    print(datetime.now(), "irtt", threading.current_thread())
    FILENAME = "data/{}/irtt-{}-{}-{}.json".format(today, INTERVAL, DURATION, timestring())
    try:
        output = subprocess.check_output(["irtt", "client", "-6", "-Q", "-i", INTERVAL, "-d", DURATION, "[{}]:2112".format(IPERF3_HOST), "-o", FILENAME])
        if "Error" in output.decode("utf-8"):
            failed(e)
    except Exception as e:
        failed(e)

    print("next run", schedule.next_run())


def iperf3() -> None:
    today = check_directory()
    print(datetime.now(), "iperf3", threading.current_thread())
    FILENAME = "data/{}/iperf3-{}-{}.json".format(today, DURATION, timestring())
    try:
        subprocess.check_output(["iperf3", "-c", IPERF3_HOST, "-R", "-J", "-u", "-b", "300M", "-i", "0.1", "--logfile", FILENAME, "--timestamp", "-t", DURATION_SECONDS])
    except Exception as e:
        failed(e)

    print("next run", schedule.next_run())


schedule.every().hours.at(":10").do(run, irtt_ping)
schedule.every().hours.at(":30").do(run, irtt_ping)
schedule.every().hours.at(":50").do(run, irtt_ping)
schedule.every().hours.at(":10").do(run, iperf3)
schedule.every().hours.at(":30").do(run, iperf3)
schedule.every().hours.at(":50").do(run, iperf3)


if __name__ == "__main__":
    print("interval: ", INTERVAL)
    print("duration: ", DURATION)
    print("iperf3 local ip: ", IPERF_LOCAL_IP)
    print("irtt local ip: ", IRTT_LOCAL_IP)
    print("server: ", IRTT_HOST_PORT)

    print("next run", schedule.next_run())
    while True:
        schedule.run_pending()
        time.sleep(0.5)
