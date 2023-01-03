import errno
import json
import os

from libwsctrl.net.obs_websocket5_client import OBSWebsocketClient
from libwsctrl.protocols.obs_ws5.requests import *

import asyncio

from libwsctrl.structs.callback import Callback

OBS_ADDRESS = "172.24.2.169"
#OBS_ADDRESS = "127.0.0.1"
OBS_PORT = 4444
OBS_PASSWORD = "blahaj"

OUPUT_PATH = "stored_scene.json"


wsClient: OBSWebsocketClient = None

sync_sources = {
    'Slides_Local': ['Slides_Remote', 'Slides_standin'],
    'Speaker1_Lokal': ['Speaker1_Remote', 'Speaker1_standin'],
    'Speaker2_Lokal': ['Speaker2_Remote', 'Speaker2_standin'],
    'Herald_Lokal': ['Herald_Remote', 'Herald_standin'],
    'LogoMonoWhite1000': ['LogoMonoGrey1000']
}


def onPropertiesSet(msg, scnname, name):
    if msg['status'] != 'ok':
        print("ERROR: {} at {}::{}".format(msg, scnname, name))
        return


def processSceneItem(msg, scnname, name):
    if msg['status'] != 'ok':
        print("ERROR Getting Scene item: Scene '{}', Item '{}' with ID '{}'".format(scnname, name, id))
        return
    del msg['status']
    del msg['message-id']

    callback = Callback(onPropertiesSet, scnname=scnname, name=name)

    for source in sync_sources[name]:
        request = setSceneItemPropertiesFromDict(item={'name': source},
                                                 scene_name=scnname,
                                                 properties=msg)
        wsClient.sendMessageJson(request, callback=callback)


def requestSceneItem(scnname, name, ide):
    callback = Callback(processSceneItem, scnname=scnname, name=name)
    wsClient.sendMessageJson(getSceneItemProperties({"name": name, "id": ide}, scnname), callback=callback)


def processSceneList(msg):
    if msg['status'] != 'ok':
        print("ERROR: {}".format(msg))
        return
    for j in range(len(msg['scenes'])):
        scene = msg['scenes'][j]
        scnname = scene['name']
        for i in range(len(scene['sources'])):
            src = scene['sources'][i]
            id = src['id']
            name = src['name']
            if name in sync_sources:
                requestSceneItem(scnname, name, id)


def onAuthenticated(msg):
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