import os
import matplotlib.pyplot as plt
from dataclasses import dataclass


EMULATION = "emulation"
STARLINK = "starlink"
ONEWEB = "oneweb_iowa"


SCENARIO_SET = [EMULATION]
# SCENARIO_SET = [ONEWEB]
VIDEO_PROFILE = ["tos"]

TITLE = {
    EMULATION: "Emulation",
    STARLINK: "Starlink",
    ONEWEB: "OneWeb"
}

LINEWIDTH=10
markersize=28
figsize=(14, 12)
fontsize=36

plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42
plt.rcParams.update({'font.size': fontsize})
plt.rcParams.update({'axes.labelsize': fontsize})

DATA_DIR = "../figures/emulation"

L2A = "abrL2A"
Dynamic = "abrDynamic"
LoLP = "abrLoLP"
CMAB = "abrCMAB"
EXCEPTED = "excepted"

FIGURE_DIR = "figures"
BITRATE_LIST_LENGTH = 8
linestyle = "solid"


@dataclass
class AlgorithmStat:
    L2A: list[float]
    Dynamic: list[float]
    LoLP: list[float]


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)
