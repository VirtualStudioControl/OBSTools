# Lists all Scenes and Inputs available in OBS

from libwsctrl.net.obs_websocket5_client import OBSWebsocketClient
from libwsctrl.protocols.obs_ws5.requests import *

import asyncio

from libwsctrl.protocols.obs_ws5.tools.messagetools import innerData
from libwsctrl.structs.callback import Callback

OBS_ADDRESS = "192.168.0.94"
#OBS_ADDRESS = "127.0.0.1"
OBS_PORT = 4455
OBS_PASSWORD = "W3GRyd13y1cXw4aD"


def processSourceList(msg):
    sourceNames = []

    for source in innerData(msg)['inputs']:
        #print(source)
        sourceNames.append(source['inputName'])

    print("Sources:", sourceNames)


def processSceneList(msg):
    sceneNames = []

    for scene in innerData(msg)['scenes']:
        #print(scene)
        sceneNames.append(scene['sceneName'])

    print("Scenes:", sceneNames)


def onAuthenticated(msg):
    callbackSources = Callback(processSourceList)
    wsClient.sendMessageJson(getInputList(), callbackSources)

    callbackScene = Callback(processSceneList)
    wsClient.sendMessageJson(getSceneList(), callback=callbackScene)


async def main():
    global wsClient
    wsClient = OBSWebsocketClient("ws://{}:{}".format(OBS_ADDRESS, OBS_PORT)) # "ws://192.168.114.230:4444" "ws://127.0.0.1:4444"
    await wsClient.connect(password=OBS_PASSWORD, onAuthenticated=Callback(onAuthenticated))
    rcvLoop = wsClient.recieveLoop()
    sendLoop = wsClient.sendLoop()

    await asyncio.gather(rcvLoop, sendLoop, return_exceptions=True)

if __name__ == "__main__":
    asyncio.run(main())
