import errno
import json
import os
from copy import copy, deepcopy

from libwsctrl.net.obs_websocket5_client import OBSWebsocketClient
from libwsctrl.protocols.obs_ws5.requests import *

import logging

import asyncio

from libwsctrl.protocols.obs_ws5.tools.messagetools import checkError, innerData
from libwsctrl.structs.callback import Callback

OBS_ADDRESS = "192.168.0.94"
OBS_PORT = 4455
OBS_PASSWORD = "W3GRyd13y1cXw4aD"

S1_STANDIN = 'Speaker1_standin'
S2_STANDIN = 'Speaker2_standin'
S3_STANDIN = 'Speaker3_standin'

H_STANDIN = 'Herald_standin'
F_STANDIN = 'Slides_standin'

BG_IMG = ['Logo_opaque', 'Logo_transparent', 'speaker-backdrop']

SCENE_LIST = ['FF', 'VM 2', 'VM 1', 'PDF', 'CLEAR']#['F-s3', 'F-S3', 'F-S1-S3', 'F-S2-S3', 'F-S3-H', 'F-S1-S2-S3', 'F-S1-S2-S3-H', 'S3', 'S1-S3', 'S2-S3', 'S3-H', 'S1-S2-S3', 'S1-S2-S3-H'] # , 'F-s1-s2', 'F-s1-h', 'F-s2-h', 'F-s1-s2-h'

SOURCE_LIST = ['Logo']

SRC_SCENE = 'Unity'


logger = logging.getLogger()

def onSceneItemDuplicated(msg, srcname):
    if checkError(msg, logger):
        print("Duplicated Item " + srcname)

def onSceneItemIDObtained(msg, srcname):
    data = innerData(msg)
    for targedSCN in SCENE_LIST:
        callback = Callback(onSceneItemDuplicated, srcname=srcname)
        wsClient.sendMessageJson(duplicateSceneItem(SRC_SCENE, data['sceneItemId'], targedSCN), callback=callback)

def onAuthenticated(msg):

    for i in range(len(SOURCE_LIST)):
        callback = Callback(onSceneItemIDObtained, srcname=SOURCE_LIST[i])
        wsClient.sendMessageJson(getSceneItemId(SRC_SCENE, SOURCE_LIST[i]), callback=callback)


async def main():
    global wsClient
    wsClient = OBSWebsocketClient("ws://{}:{}".format(OBS_ADDRESS, OBS_PORT)) #"ws://192.168.114.230:4444" "ws://127.0.0.1:4444"
    await wsClient.connect(password=OBS_PASSWORD, onAuthenticated=Callback(onAuthenticated))
    rcvLoop = wsClient.recieveLoop()
    sendLoop = wsClient.sendLoop()

    await asyncio.gather(rcvLoop, sendLoop, return_exceptions=True)

if __name__ == "__main__":
    asyncio.run(main())
