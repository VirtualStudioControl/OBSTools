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

OUPUT_PATH = "stored_scene_divoc_D2.json"


wsClient: OBSWebsocketClient = None

sourceFilters = []
sceneItems = []


def writeFile(path, content, mode="w"):
    """
    Writes content to a file at the given path

    :param path: Path of the file to write
    :param content: Content to write to the file
    :param mode: File Open mode, 'w' for write, 'a' for append
    :return: None
    """
    dirname = os.path.dirname(path)
    if len(dirname.strip()) > 0 and not os.path.exists(dirname):
        try:
            os.makedirs(dirname)
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    f = open(path, mode, encoding='utf8')
    try:
        f.write(content)
    finally:
        f.close()


def writeJSON(path: str, values: dict):
    content = json.dumps(values, indent=2, sort_keys=True)
    writeFile(path, content)


def storeSceneItems():
    writeJSON(OUPUT_PATH, {"scenes": sceneItems, "sources": sourceFilters})
    print("DONE.")

def processSeceneItem(msg, scnname, name, id, final):
    if msg['status'] != 'ok':
        print("ERROR Getting Scene item: Scene '{}', Item '{}' with ID '{}'".format(scnname, name, id))
        return
    del msg['status']
    del msg['message-id']
    sceneItem = {'scene_name': scnname, 'name': name, 'id': id, 'properties': msg}

    sceneItems.append(sceneItem)

    if final:
        storeSceneItems()


def requestSceneItem(scnname, name, id, final):
    callback = Callback(processSeceneItem, scnname=scnname, name=name, id=id, final=final)
    wsClient.sendMessageJson(getSceneItemProperties({"name": name, "id": id}, scnname), callback=callback)


def processSceneList(msg):
    for j in range(len(msg['scenes'])):
        scene = msg['scenes'][j]
        scnname = scene['name']
        for i in range(len(scene['sources'])):
            src = scene['sources'][i]
            id = src['id']
            name = src['name']
            c = False
            if j == len(msg['scenes']) -1:
                if i == len(scene['sources']) -1:
                    c = True
            requestSceneItem(scnname, name, id, c)


def onGetFilterInfo(msg, sourceName):
    if msg['status'] != 'ok':
        print("ERROR Getting Filter Info: Source '{}''".format(sourceName))
        return

    sourceFilters.append({'sourceName': sourceName, 'filters': msg['filters']})


def processSourceList(msg):
    for source in msg['sources']:
        callback = Callback(onGetFilterInfo, sourceName=source['name'])
        wsClient.sendMessageJson(getSourceFilters(source['name']), callback)


def onAuthenticated(msg):

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
