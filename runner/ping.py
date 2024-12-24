import os
import logging
import subprocess
import threading


logger = logging.getLogger(__name__)


def icmp_ping(exp_id: str, duration: int) -> None:
    GATEWAY = os.getenv("GATEWAY")
    name = "ICMP_PING"
    logger.info("{}, {}".format(name, threading.current_thread()))

    FILENAME = "ping-{}.txt".format(exp_id)

    cmd = ["ping", "-D", "-i", "0.01", GATEWAY]
    try:
        with open(FILENAME, "w") as outfile:
            subprocess.run(cmd, stdout=outfile, timeout=duration)
    except subprocess.TimeoutExpired:
        pass
