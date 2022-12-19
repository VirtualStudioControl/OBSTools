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
OBS_PASSWORD = "blahaj"

wsClient: OBSWebsocketClient = None

SCENES = ['MV_SOURCE_1', 'MV_SOURCE_2', 'MV_SOURCE_3', 'MV_SOURCE_HERALD', 'MV_SLIDES',
          'Ffull', 'Fscene', 'F-s1', 'F-S1', 'F-s1-no', 'F-s2', 'F-S2', 'F-H', 'F-s1-s2', 'F-s1-h',
          'F-s2-h', 'F-s1-s2-h', 'S1', 'S2', 'H', 'S1-S2', 'S1-H', 'S2-H', 'S1-S2-H', 'F-s3', 'F-S3', 'F-s1-s3',
          'F-s2-s3', 'F-s3-H', 'F-s1-s2-s3', 'F-s1-s2-s3-H', 'S3', 'S1-S3', 'S2-S3', 'S3-H', 'S1-S2-S3', 'S1-S2-S3-H']


S1_STANDIN = 'Speaker1_standin'
S2_STANDIN = 'Speaker2_standin'
S3_STANDIN = 'Speaker3_standin'

H_STANDIN = 'Herald_standin'
F_STANDIN = 'Slides_standin'


S1_LOCAL = 'Speaker1_Lokal'
S2_LOCAL = 'Speaker2_Lokal'
S3_LOCAL = 'Speaker3_Lokal'

H_LOCAL = 'Herald_Lokal'
F_LOCAL = 'Slides_Local'


S1_REMOTE = 'Speaker1_Remote'
S2_REMOTE = 'Speaker2_Remote'
S3_REMOTE = 'Speaker3_Remote'

H_REMOTE = 'Herald_Remote'
F_REMOTE = 'Slides_Remote'


sync_sources = {
    S1_STANDIN: [S1_LOCAL, S1_REMOTE],
    S2_STANDIN: [S2_LOCAL, S2_REMOTE],
    S3_STANDIN: [S3_LOCAL, S3_REMOTE],
    H_STANDIN: [H_LOCAL, H_REMOTE],
    F_STANDIN: [F_LOCAL, F_REMOTE]
}


def onPropertiesSet(msg, scnname, name):
    if msg['status'] != 'ok':
        print("ERROR: {} at {}::{}".format(msg, scnname, name))
        return


def setProperties(msg, scnname, name, source, properties):
    callback = Callback(onPropertiesSet, scnname=scnname, name=name)
    request = setSceneItemPropertiesFromDict(item={'name': source},
                                             scene_name=scnname,
                                             properties=properties)
    wsClient.sendMessageJson(request, callback=callback)

def processSceneItem(msg, scnname, name):
    if msg['status'] != 'ok':
        print("ERROR Getting Scene item: Scene '{}', Item '{}' with ID '{}'".format(scnname, name, id))
        return
    del msg['status']
    del msg['message-id']

    for source in sync_sources[name]:
        callback = Callback(setProperties, scnname=scnname, name=name, source=source, properties=msg)
        wsClient.sendMessageJson(addSceneItem(sceneName=scnname, sourceName=source, setVisible=True), callback)

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
        if scnname not in SCENES:
            continue
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