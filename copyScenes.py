import errno
import json
import os
from copy import copy, deepcopy

from libwsctrl.net.obs_websocket4_client import OBSWebsocketClient
from libwsctrl.protocols.obs_ws4.obs_websocket_protocol import *

import asyncio

from libwsctrl.structs.callback import Callback

OBS_ADDRESS = "192.168.114.230"
#OBS_ADDRESS = "127.0.0.1"
OBS_PORT = 4444
OBS_PASSWORD = "12345678"


SCENE_LIST = ['Fscene', 'F-s1', 'F-s2', 'F-h', 'F-S1', 'F-S2', 'F-s1-s2', 'F-S1-H', 'S1-H', 'S2-H', 'H', 'S1-S2', 'S1-S2-H', 'S1', 'S2']
SOURCE_LIST = ['Bauchbinde Hashtags','SterneKlein_4096', 'FelsenH4096', 'FelsenM4096', 'FelsenV4096', 'Hailand4096', 'Planet4096']

SRC_SCENE = 'F-S1-S2-H'

sceneItemProperties = {}


def onSceneItemPropertiesSent(msg):
    print(msg)


def setItemProperties(msg, scene, source):
    if msg['status'] != 'ok':
        print("ERROR adding Scene item: Scene '{}', Item '{}'".format(scene, source))
        return
    print("Setting Item Properties: Scene '{}', Item '{}'".format(scene, source))

    callback = Callback(onSceneItemPropertiesSent)
    wsClient.sendMessageJson(setSceneItemPropertiesFromDict(item={'name': source},
                                             scene_name= scene,
                                             properties=sceneItemProperties[source]), callback=callback)

def addSceneItemsToScenes():
    for scene in SCENE_LIST:
        for source in SOURCE_LIST:
            #callback = Callback(setItemProperties, scene=scene, source=source)
            #wsClient.sendMessageJson(addSceneItem(scene, source, True), callback)
            msg = {'status': 'ok'}
            setItemProperties(msg, scene=scene, source=source)
        sleep(1)

def addSceneItemConfiguration(msg, srcname, sources):
    if msg['status'] != 'ok':
        print("ERROR Getting Scene item: Item '{}'".format(srcname))
        return
    del msg['status']
    del msg['message-id']

    sceneItemProperties[srcname] = msg

    print("Got Source:", srcname)

    if sources == len(sceneItemProperties):
        addSceneItemsToScenes()


def onAuthenticated(msg):

    for i in range(len(SOURCE_LIST)):
        callback = Callback(addSceneItemConfiguration, srcname=SOURCE_LIST[i], sources = len(SOURCE_LIST))
        wsClient.sendMessageJson(getSceneItemProperties({"name": SOURCE_LIST[i]}, SRC_SCENE), callback=callback)


async def main():
    global wsClient
    wsClient = OBSWebsocketClient("ws://{}:{}".format(OBS_ADDRESS, OBS_PORT)) #"ws://192.168.114.230:4444" "ws://127.0.0.1:4444"
    await wsClient.connect(password=OBS_PASSWORD, onAuthenticated=Callback(onAuthenticated))
    rcvLoop = wsClient.recieveLoop()
    sendLoop = wsClient.sendLoop()

    await asyncio.gather(rcvLoop, sendLoop, return_exceptions=True)

if __name__ == "__main__":
    asyncio.run(main())
