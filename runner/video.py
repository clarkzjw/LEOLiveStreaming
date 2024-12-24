import os
import time
import logging
from config import VIDEO_CONTAINER_IMAGE, CHROME_CONTAINER_IP, DOCKER_NETWORK_NAME

import docker


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

logger = logging.getLogger("util")


def pull_ffmpeg_image() -> None:
    client = docker.from_env()
    client.images.pull(VIDEO_CONTAINER_IMAGE)


def create_ffmpeg_container(exp_id: str) -> docker.models.containers.Container:
    client = docker.from_env()
    workdir = os.getenv("WORKDIR")

    container = client.containers.run(VIDEO_CONTAINER_IMAGE,
                                        detach=True,
                                        environment=[
                                            "DISPLAY_CONTAINER_NAME={}".format(CHROME_CONTAINER_IP),
                                            "FILE_NAME={}.mp4".format(exp_id),
                                            ],
                                        network=DOCKER_NETWORK_NAME,
                                        volumes=["{}/videos:/videos".format(workdir)])
    return container


def restart_nginx() -> None:
    logger.info("restarting nginx")
    client = docker.from_env()
    nginx = client.containers.get("dashjs-nginx")
    nginx.restart()
    while True:
        try:
            nginx = client.containers.get("dashjs-nginx")
            if nginx.status == "running":
                break
        except:
            logger.info("waiting for nginx to restart")
            time.sleep(1)
            continue


def create_nginx_with_trace(EMULATION_PROFILE: str) -> docker.models.containers.Container:
    logger.info("creating nginx with trace profile {}".format(EMULATION_PROFILE))
    client = docker.from_env()

    # nginx:
    # image: clarkzjw/dashjs-nginx-emulation:tomm24
    # build:
    #   context: .
    #   dockerfile: Dockerfile-nginx-emulation
    # container_name: dashjs-nginx
    # privileged: true
    # environment:
    #   SCENARIO: "bent_pipe"
    #   # SCENARIO: "isl"
    #   # SCENARIO: "bent_pipe_synthetic"
    #   # SCENARIO: "isl_synthetic"
    # ports:
    #   - 80
    # restart: always
    # networks:
    #   dashjs:
    #     ipv4_address: 192.167.0.107

    NGINX_CONTAINER_NAME = "dashjs-nginx"
    NGINX_NETWORK_IP = "192.167.0.107"

    nginx_container = client.containers.run(image="clarkzjw/dashjs-nginx-emulation:tomm24",
                          detach=True,
                          environment=[
                              "SCENARIO={}".format(EMULATION_PROFILE),
                          ],
                          restart_policy={"Name": "always"},
                        #   network=DOCKER_NETWORK_NAME,
                        #   networking_config=client.api.create_networking_config({
                        #       DOCKER_NETWORK_NAME: client.api.create_endpoint_config(
                        #           ipv4_address=NGINX_NETWORK_IP
                        #           )}),
                          name=NGINX_CONTAINER_NAME,
                          privileged=True)

    network = client.networks.get(DOCKER_NETWORK_NAME)
    network.connect(NGINX_CONTAINER_NAME, ipv4_address=NGINX_NETWORK_IP)

    while True:
        try:
            nginx = client.containers.get(NGINX_CONTAINER_NAME)
            if nginx.status == "running":
                break
        except:
            logger.info("waiting for nginx to start")
            time.sleep(1)
            continue

    return nginx_container
