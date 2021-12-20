import errno
import json
import os

from libwsctrl.net.obs_websocket4_client import OBSWebsocketClient
from libwsctrl.protocols.obs_ws4.obs_websocket_protocol import *

import asyncio

from libwsctrl.structs.callback import Callback

OBS_ADDRESS = "192.168.114.230"
#OBS_ADDRESS = "127.0.0.1"
OBS_PORT = 4444
OBS_PASSWORD = "12345678"

def processSourceList(msg):
    sourceNames = []

    for source in msg['sources']:
        sourceNames.append(source['name'])

    print("Sources:", sourceNames)


def processSceneList(msg):
    sceneNames = []

    for scene in msg['scenes']:
        sceneNames.append(scene['name'])

    print("Scenes:", sceneNames)


def onAuthenticated(msg):
    pass
    callbackSources = Callback(processSourceList)
    wsClient.sendMessageJson(getSourcesList(), callbackSources)

    callbackScene = Callback(processSceneList)
    wsClient.sendMessageJson(getSceneList(), callback=callbackScene)


async def main():
    global wsClient
    wsClient = OBSWebsocketClient("ws://{}:{}".format(OBS_ADDRESS, OBS_PORT)) #"ws://192.168.114.230:4444" "ws://127.0.0.1:4444"
    await wsClient.connect(password=OBS_PASSWORD, onAuthenticated=Callback(onAuthenticated))
    rcvLoop = wsClient.recieveLoop()
    sendLoop = wsClient.sendLoop()

    await asyncio.gather(rcvLoop, sendLoop, return_exceptions=True)

if __name__ == "__main__":
    asyncio.run(main())
