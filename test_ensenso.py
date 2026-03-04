import argparse

from nxlib.context import NxLib, MonoCamera
from nxlib.command import NxLibCommand
from nxlib.constants import *


parser = argparse.ArgumentParser()
parser.add_argument("--serial", type=str,
                    help="the serial of the mono camera to open")
args = parser.parse_args()


def save_image(filename, item):
    with NxLibCommand(CMD_SAVE_IMAGE) as cmd:
        cmd.parameters()[ITM_NODE] = item.path
        cmd.parameters()[ITM_FILENAME] = filename
        cmd.execute()


with NxLib(), MonoCamera(args.serial) as camera:
    camera.capture()
    camera.rectify()
    save_image("raw.png", camera[ITM_IMAGES][ITM_RAW])
    save_image("rectified.png", camera[ITM_IMAGES][ITM_RECTIFIED])