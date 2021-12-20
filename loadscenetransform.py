import asyncio
import json

from libwsctrl.net.obs_websocket4_client import OBSWebsocketClient
from libwsctrl.protocols.obs_ws4.obs_websocket_protocol import *
from libwsctrl.structs.callback import Callback

OBS_ADDRESS = "192.168.114.230"
#OBS_ADDRESS = "127.0.0.1"
OBS_PORT = 4444
OBS_PASSWORD = "12345678"

INPUT_PATH = "scene.json"


wsClient: OBSWebsocketClient = None


def readFile(path):
    """
    Read the complete file

    :param path: Path to read from
    :return: the data of the file
    """
    f = open(path, "r", encoding='utf8')
    result = ""
    try:
        result = f.read()
    finally:
        f.close()

    return result


def readJSON(path: str) -> dict:
    content = readFile(path)
    return json.loads(content)


def onSceneItemPropertiesSent(msg):
    print(msg)


def onAuthenticated(msg):
    callback = Callback(onSceneItemPropertiesSent)
    values = readJSON(INPUT_PATH)

    for itm in values['scenes']:
        request = setSceneItemPropertiesFromDict(item={'id':itm['id'], 'name':itm['name']},
                                                                scene_name=itm['scene_name'],
                                                                properties=itm['properties'])
        print(request)
        wsClient.sendMessageJson(request, callback=callback)

    for source in values['sources']:
        sname = source['sourceName']
        filters = source['filters']
        for filter in filters:
            wsClient.sendMessageJson(setSourceFilterSettings(sname, filter['name'], filter['settings']), callback=callback)
            wsClient.sendMessageJson(setSourceFilterVisibility(sname, filter['name'], filter['enabled']),
                                     callback=callback)


async def main():
    global wsClient
    wsClient = OBSWebsocketClient("ws://{}:{}".format(OBS_ADDRESS, OBS_PORT)) #"ws://192.168.114.230:4444" "ws://127.0.0.1:4444"
    await wsClient.connect(password=OBS_PASSWORD, onAuthenticated=Callback(onAuthenticated))
    rcvLoop = wsClient.recieveLoop()
    sendLoop = wsClient.sendLoop()

    await asyncio.gather(rcvLoop, sendLoop, return_exceptions=True)

if __name__ == "__main__":
    asyncio.run(main())
