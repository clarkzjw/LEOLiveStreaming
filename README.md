# LEOLiveStreaming

This repository contains the implementation and artifacts of the paper ***Live Video Streaming over Low-Earth-Orbit Satellite Networks: A Multi-Constellation Evaluation*** submitted to *ACM Transactions on Multimedia Computing, Communications, and Applications*.

Table of Contents
=================

  * [Repository structure](#repository-structure)
  * [Prerequisites](#prerequisites)
  * [Emulation](#emulation)
  * [Real world experiments](#real-world-experiments)
  * [Extensions](#extensions)
  * [License](#license)

## Repository structure

```

```

---

## Prerequisites

### Docker

Any system capable of running recent versions of [Docker](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/) should suffice. The live video streaming emulation results of this paper were produced on Debian 12.8 x86-64 with Docker version 27.3.1 and the [Compose plugin](https://docs.docker.com/compose/install/linux/) version 2.29.7. However, the [Compose standalone](https://docs.docker.com/compose/install/standalone/) should also work.

To install Docker and the Docker Compose plugin on a recent Linux distribution, you can use the following automated installation script.

```bash
curl -fsSL https://get.docker.com | sh
```

### Required prerequisites for development

```bash
sudo apt-get update && sudo apt-get install curl git pipx vim zstd -y
pipx install poetry
```

Add `$HOME/.local/bin` to your `$PATH`, and install the required Python packages.

```bash
poetry install
```

Use `poetry shell` to launch a virtual environment with the installed Python packages.

---

This repository contains the following components.

[Paper figures](#paper-figures)

[Emulation](#emulation)

[Real world experiments](#real-world-experiments)

## Paper Figures

You can recreate figures in the paper with corresponding scripts in the [paper-figures](./paper-figures/) directory.

## Emulation

The topology for our network emulator is shown as follows.

![Network Emulator](./assets/Emulation-Testbed.png)

To conduct video streaming using our purpose-built network emulator, please follow the following steps.

0. Apply file watch limit adjustment on the Linux machine used to run emulations

```bash
echo fs.inotify.max_user_watches= 131070 | sudo tee -a /etc/sysctl.conf && sudo sysctl -p
```

1. Pull Docker images used in emulation.

```bash
sudo docker compose -f docker-compose-emulation.yaml pull
```

or build from scratch.

```bash
sudo docker compose -f docker-compose-emulation.yaml build
```

2. The `Experiment Profiles` are defined in the [experiments](./experiments/) directory, which are a set of JSON files with the following format:

```json
[
  {
        "EMULATION": true,
        "EMULATION_PROFILE": "bent_pipe_victoria_1",
        "VIDEO_PROFILE": "tos",
        "ROUND_DURATION": 600,
        "CMAB_ALPHA": 1.0,
        "TARGET_LATENCY": 3,
        "CONSTANT_VIDEO_BITRATE": -1,
        "TOTAL_ROUNDS": 2,
        "MPD_URL": "http://dashjs-nginx/livesim2/tos/WAVE/vectors/switching_sets/15_30_60/ss1/2023-10-05/stream.mpd",
        "ABR_ALGORITHM": "abrCMAB",
        "CATCH_UP": "liveCatchupModeCMAB"
    },
    ...
]
```

**`EMULATION_PROFILE`**

By default, there are six different `EMULATION_PROFILE`s, as shown in [Figure 7](./paper-figures/figure7/), with the following keys can be selected for `EMULATION_PROFILE`:

```bash
bent_pipe_victoria_1
bent_pipe_victoria_2
bent_pipe_victoria_3
bent_pipe_victoria_4
bent_pipe_victoria_5
oneweb_iowa
```

**`ROUND_DURATION`**

If you are using the default latency traces as shwon above, the maximal `ROUND_DURATION` can be set will be `600`.

**`VIDEO_PROFILE`**

There are two test videos available as built by [Dockerfile-livesim2](./Dockerfile-livesim2), `tos` and `croatia`, each has a corresponding `MPD_URL` as follows:

```
http://dashjs-nginx/livesim2/tos/WAVE/vectors/switching_sets/15_30_60/ss1/2023-10-05/stream.mpd
http://dashjs-nginx/livesim2/croatia/WAVE/vectors/switching_sets/12.5_25_50/ss1/2023-10-05/stream.mpd
```

**`ABR_ALGORITHM`**

The following ABR algorithms are supported by default:

```
abrDynamic
abrL2A
abrLoLP
abrCMAB
```

3. Start video streaming emulation with Docker Compose.

```bash
sudo docker compose -f docker-compose-emulation.yaml up -d
```

4. A convenience container is available to display the video streaming browser output using noVNC. This can be accessed by navigating to `http://<host-ip>:7900/?autoconnect=1&resize=scale&password=secret` in a web browser, where `<host-ip>` represents the IP address of the Linux machine on which the emulation takes place. The video streaming browser output is recorded for visual inspection.

You can disable the video recording by setting the `VIDEO` environment variable to `0` in [`docker-compose-emulation.yaml`](./docker-compose-emulation.yaml).

5. You can check the experiment running process and logs by

```bash
sudo docker logs -f dashjs-runner
```

where the expected execuation time for the entire experiment set will be printed.

```bash
[...]
2024-03-06 09:18:46.937 INFO batch_runner - <module>: Total experiment count: 160, duration: 48000 seconds (13.333333333333334 hours)
[...]
```

6. When video streaming emulation finishes, `dashjs-runner` container will output the following log and exit.

```bash
[...]
2024-03-06 08:54:46.489 INFO batch_runner - <module>: Video Streaming completed.
```

The raw data will be available in the `figures-emulation` folder.

7. After finishing the emulation, you can cleanup the resources by

```bash
sudo docker compose -f docker-compose-emulation.yaml down
```

8. Plot all the figures similar to Figure 8 to Figure 10 by

```bash
cd plot
make
```

## Real world experiments


## Extensions

### Custom video dataset

To replace the default bitrate ladder and use custom video datasets, replace and update the following lines in [Dockerfile-livesim2](./Dockerfile-livesim2) accordingly,

```Dockerfile
# RUN ./dashfetcher -a
                    # test content from https://cta-wave.github.io/Test-Content/
                    #    croatia
                    #    https://dash.akamaized.net/WAVE/vectors/switching_sets/12.5_25_50/ss1/2023-10-05/stream.mpd

                    #    tos
                    #    https://dash.akamaized.net/WAVE/vectors/switching_sets/15_30_60/ss1/2023-10-05/stream.mpd

                    # datasets at AAU.at dataset are not compatible with livesim2
                    # https://ftp.itec.aau.at/datasets/DASHDataset2014/BigBuckBunny/1sec/BigBuckBunny_1s_simple_2014_05_09.mpd
                    # https://ftp.itec.aau.at/datasets/DASHDataset2014/BigBuckBunny/2sec/BigBuckBunny_2s_simple_2014_05_09.mpd

RUN wget https://starlink-dash-live.jinwei.me/tos.zip && unzip tos.zip && rm tos.zip
RUN wget https://starlink-dash-live.jinwei.me/croatia.zip && unzip croatia.zip && rm croatia.zip

RUN cd /livesim2/tos/WAVE/vectors && \
    mv cfhd_sets chdf_sets switching_sets/15_30_60/ss1/2023-10-05 && \
    cd switching_sets/15_30_60/ss1/2023-10-05 && \
    sed -i -e 's/..\/..\/..\/..\///g' stream.mpd && \
    cd /livesim2/croatia/WAVE/vectors && \
    mv cfhd_sets chdf_sets switching_sets/12.5_25_50/ss1/2023-10-05/ && \
    cd switching_sets/12.5_25_50/ss1/2023-10-05/ && \
    sed -i -e 's/..\/..\/..\/..\///g' stream.mpd
```

and rebuild the `livesim2` Docker image and replace the image used by the `livesim2` service in the corresponding `docker-compose.yaml` file.

## License

The code in this repository is licensed under [GPL-3.0](./LICENSE).
