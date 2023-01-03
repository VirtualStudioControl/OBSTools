import asyncio
import time
from asyncio import Semaphore
from itertools import chain, combinations

from libwsctrl.net.obs_websocket5_client import OBSWebsocketClient
from libwsctrl.protocols.obs_ws5.requests import *
from libwsctrl.protocols.obs_ws5.tools.messagetools import innerData
from libwsctrl.structs.callback import Callback
from structures.SceneInfo import SceneInfo
from structures.SceneTemplate import SceneTemplate

########################################################################################################################
### OBS Credentials
########################################################################################################################

# Local

#OBS_ADDRESS = "192.168.0.94"
#OBS_PORT = 4455
#OBS_PASSWORD = "W3GRyd13y1cXw4aD"

# R3S Production

OBS_ADDRESS = "192.168.114.230"
OBS_PORT = 4455
OBS_PASSWORD = "l2dOXh1CxcSrWWei"

########################################################################################################################
### Templates
########################################################################################################################

SCENE_TEMPLATE_FULL = SceneTemplate(
    name="Template_Full",
    background=["mixerinput"],
    slides=[],
    speakers=["Template_Input_Slides"],
    overlays=["FireshonksLogomitFels"],
    logo=["LogoDark", "LogoLight"]
)

SCENE_TEMPLATE_FULL_NO_OVERLAY = SceneTemplate(
    name="Template_Full",
    background=["mixerinput"],
    slides=[],
    speakers=["Template_Input_Slides"],
    overlays=[],
    logo=["LogoDark", "LogoLight"]
)


SCENE_TEMPLATE_SPEAKER1 = SceneTemplate(
    name="Template_1Speaker",
    background=["Hintergrund", "Boden", "Felsenunten", "Felsenlinks", "Blasen", "FireshonksLogomitFels", "Fireshonk", "mixerinput"],
    slides=[],
    speakers=["Template_Input_Slides"],
    overlays=["Felsenrechts", "overlay_technical_difficulties"],
    logo=["LogoDark", "LogoLight"]
)

SCENE_TEMPLATE_SPEAKER2 = SceneTemplate(
    name="Template_2Speakers",
    background=["Hintergrund", "Boden", "Felsenunten", "Felsenlinks", "Blasen", "FireshonksLogomitFels", "Fireshonk", "mixerinput"],
    slides=[],
    speakers=["Template_Input_Speaker1", "Template_Input_Speaker2"],
    overlays=["Felsenrechts", "overlay_technical_difficulties"],
    logo=["LogoDark", "LogoLight"]
)

SCENE_TEMPLATE_SPEAKER3 = SceneTemplate(
    name="Template_3Speakers",
    background=["Hintergrund", "Boden", "Felsenunten", "Felsenlinks", "Blasen", "FireshonksLogomitFels", "Fireshonk", "mixerinput"],
    slides=[],
    speakers=["Template_Input_Speaker1", "Template_Input_Speaker2", "Template_Input_Speaker3"],
    overlays=["Felsenrechts", "overlay_technical_difficulties"],
    logo=["LogoDark", "LogoLight"]
)

SCENE_TEMPLATE_SPEAKER4 = SceneTemplate(
    name="Template_4Speakers",
    background=["Hintergrund", "Boden", "Felsenunten", "Felsenlinks", "Blasen", "FireshonksLogomitFels", "Fireshonk", "mixerinput"],
    slides=[],
    speakers=["Template_Input_Speaker1", "Template_Input_Speaker2", "Template_Input_Speaker3", "Template_Input_Speaker4"],
    overlays=["Felsenrechts", "overlay_technical_difficulties"],
    logo=["LogoDark", "LogoLight"]
)


SCENE_TEMPLATE_SLIDES = SceneTemplate(
    name="Template_Slides_4Speakers",
    background=["Hintergrund", "Boden", "Felsenunten", "Felsenlinks", "Blasen", "FireshonksLogomitFels", "Fireshonk", "mixerinput"],
    slides=["Standin_Slides", "BMD_Input_5", "Slides_REMOTE"],
    speakers=["Template_Input_Speaker1", "Template_Input_Speaker2", "Template_Input_Speaker3", "Template_Input_Speaker4"],
    overlays=["Felsenrechts", "overlay_technical_difficulties"],
    logo=["LogoDark", "LogoLight"]
)

TEMPLATE_FULL = "TemplateFull"
TEMPLATE_FULL_NO_OVERLAY = "TemplateFullNoOverlay"
TEMPLATE_SPEAKER = "TemplateSingle"
TEMPLATE_SPEAKER_SLIDES = "TemplateSingleSlides"

TEMPLATE_SCENES = {
    TEMPLATE_FULL: [SCENE_TEMPLATE_FULL],
    TEMPLATE_FULL_NO_OVERLAY: [SCENE_TEMPLATE_FULL_NO_OVERLAY],
    TEMPLATE_SPEAKER: [SCENE_TEMPLATE_SPEAKER1, SCENE_TEMPLATE_SPEAKER2, SCENE_TEMPLATE_SPEAKER3, SCENE_TEMPLATE_SPEAKER4],
    TEMPLATE_SPEAKER_SLIDES: [SCENE_TEMPLATE_SLIDES],
}

ALL_TEMPLATES = [*TEMPLATE_SCENES[TEMPLATE_FULL],
                 *TEMPLATE_SCENES[TEMPLATE_FULL_NO_OVERLAY],
                 *TEMPLATE_SCENES[TEMPLATE_SPEAKER],
                 *TEMPLATE_SCENES[TEMPLATE_SPEAKER_SLIDES]]

########################################################################################################################
### Configuretion
########################################################################################################################

SPEAKER_COUNT = 3
PREREC_COUNT = 2
REMOTE_COUNT = 1

SPEAKER_BASE = "S"
HERALD_BASE = "H"
SLIDES_BASE = "F"
PREREC_BASE = "PreRec"
REMOTE_BASE = "Remote"

INFOBEAMER = "Infobeamer"
TECHNICAL_DIFFICULTIES = "TechnicalDifficulties"

INTRO = "Intro"
OUTRO = "Outro"
QNA = "QandA"

SEPERATOR = "-"

########################################################################################################################
### Sources
########################################################################################################################

SPEAKER_SOURCES = {
    "{}{}".format(SPEAKER_BASE, 1): ["Standin_Speaker1", "BMD_Input_1", "Speaker1_REMOTE"],
    "{}{}".format(SPEAKER_BASE, 2): ["Standin_Speaker2", "BMD_Input_2", "Speaker2_REMOTE"],
    "{}{}".format(SPEAKER_BASE, 3): ["Standin_Speaker3", "BMD_Input_3", "Speaker3_REMOTE"],
    HERALD_BASE: ["Standin_Herald", "BMD_Input_4", "Herald_REMOTE"],
    SLIDES_BASE: ["Standin_Slides", "BMD_Input_5", "Slides_REMOTE"],
    "{}{}".format(PREREC_BASE, 1): ["PreREC1"],
    "{}{}".format(PREREC_BASE, 2): ["PreREC2"],
    "{}{}".format(REMOTE_BASE, 1): ["RTMP1"],
    INFOBEAMER: ["BMD_Input_6"],
    TECHNICAL_DIFFICULTIES: ["TechnicalDifficultiesWeb"],
    INTRO: ["IntroWeb"],
    OUTRO: ["MISSING_SOURCE"],
    QNA: ["MISSING_SOURCE"]
}

########################################################################################################################
### Internal
########################################################################################################################
CLEAR_ONLY = False
MESSAGES_RECEIVED = 0

#region Scene Generation
def powerset(iterable):
    s = list(iterable)
    touples = chain.from_iterable(combinations(s, r) for r in range(len(s)+1))
    result = []
    for t in touples:
        result.append(t)
    return result


def generateName(scene: tuple):
    result = ""
    for i in range(len(scene)):
        if i > 0:
            result += SEPERATOR
        result += scene[i]
    return result


def generateScenes() -> List[SceneInfo]:
    names = []

    names.append(SceneInfo("{}{}full".format(SLIDES_BASE, SEPERATOR), [SLIDES_BASE], TEMPLATE_FULL))
    for i in range(SPEAKER_COUNT):
        names.append(SceneInfo("{}{}{}full".format(SPEAKER_BASE, i + 1, SEPERATOR), ["{}{}".format(SPEAKER_BASE, i + 1)], TEMPLATE_FULL))
    names.append(SceneInfo("{}{}full".format(HERALD_BASE, SEPERATOR), [HERALD_BASE], TEMPLATE_FULL))

    speakers = []
    for i in range(SPEAKER_COUNT):
        speakers.append("{}{}".format(SPEAKER_BASE, i+1))
    speakers.append(HERALD_BASE)

    scenes = powerset(speakers)

    names.append(SceneInfo(SLIDES_BASE, [SLIDES_BASE], TEMPLATE_SPEAKER))

    for scene in scenes:
        if (len(scene) == 0):
            continue
        name = generateName(scene)
        names.append(SceneInfo("{}{}{}".format(SLIDES_BASE, SEPERATOR, name), [*scene], TEMPLATE_SPEAKER_SLIDES))
        names.append(SceneInfo(name, [*scene], TEMPLATE_SPEAKER))

    for prerec in range(PREREC_COUNT):
        names.append(SceneInfo("{}{}".format(PREREC_BASE, prerec+1), ["{}{}".format(PREREC_BASE, prerec+1)], TEMPLATE_FULL_NO_OVERLAY))

    for remote in range(REMOTE_COUNT):
        names.append(SceneInfo("{}{}".format(REMOTE_BASE, remote + 1), ["{}{}".format(REMOTE_BASE, remote + 1)], TEMPLATE_FULL_NO_OVERLAY))

    names.append(SceneInfo(INFOBEAMER, [INFOBEAMER], TEMPLATE_FULL_NO_OVERLAY))
    names.append(SceneInfo(TECHNICAL_DIFFICULTIES, [TECHNICAL_DIFFICULTIES], TEMPLATE_FULL_NO_OVERLAY))

    names.append(SceneInfo(INTRO, [INTRO], TEMPLATE_FULL_NO_OVERLAY))
    names.append(SceneInfo(OUTRO, [OUTRO], TEMPLATE_FULL_NO_OVERLAY))
    names.append(SceneInfo(QNA, [QNA], TEMPLATE_FULL_NO_OVERLAY))

    return names

#endregion

#region OBS Setup


def pickTemplate(sceneInfo: SceneInfo) -> SceneTemplate:
    candidate = TEMPLATE_SCENES[sceneInfo.template]
    if isinstance(candidate, SceneTemplate):
        return candidate

    # More than one Template available for type, pick the most likely to fit
    try:
        return candidate[len(sceneInfo.sources)-1]
    except:
        return candidate[-1]


def onItemDuplicated(msg, item, semaphore: Semaphore):
    semaphore.release() # Item is duplicated, so nothing else to do

def onTransformSet(msg):
    print(msg)

def sanitizeTransform (transform):
    if ('boundsWidth' in transform):
        del transform['boundsWidth']
        del transform['boundsHeight']
    return transform

def onItemCreated(msg, sceneInfo: SceneInfo, template: SceneTemplate, slotNumber, source, semaphore: Semaphore):
    sceneItemID = innerData(msg)['sceneItemId']

    callback = Callback(onTransformSet)
    wsClient.sendMessageJson(setSceneItemTransform(sceneInfo.name, sceneItemID, sanitizeTransform(template.items[template.speakers[slotNumber]]['sceneItemTransform'])), callback=callback)
    semaphore.release()


async def taskCreateScene(sceneInfo: SceneInfo):
    sem = Semaphore()
    template = pickTemplate(sceneInfo)

    for itm in template.background:
        await sem.acquire()
        callback = Callback(onItemDuplicated, item=itm, semaphore=sem)
        wsClient.sendMessageJson(duplicateSceneItem(template.name, template.items[itm]['sceneItemId'], sceneInfo.name),
                                 callback=callback)

    for itm in template.slides:
        await sem.acquire()
        callback = Callback(onItemDuplicated, item=itm, semaphore=sem)
        wsClient.sendMessageJson(duplicateSceneItem(template.name, template.items[itm]['sceneItemId'], sceneInfo.name),
                                 callback=callback)

    for i in range(len(sceneInfo.sources)):
        for j in range(len(SPEAKER_SOURCES[sceneInfo.sources[i]])):
            await sem.acquire()
            callback = Callback(onItemCreated, sceneInfo=sceneInfo, template=template, slotNumber=i, source=SPEAKER_SOURCES[sceneInfo.sources[i]][j], semaphore=sem)
            wsClient.sendMessageJson(createSceneItem(sceneInfo.name, SPEAKER_SOURCES[sceneInfo.sources[i]][j], True),
                                 callback=callback)

    for itm in template.overlays:
        await sem.acquire()
        callback = Callback(onItemDuplicated, item=itm, semaphore=sem)
        wsClient.sendMessageJson(duplicateSceneItem(template.name, template.items[itm]['sceneItemId'], sceneInfo.name),
                                 callback=callback)

    for itm in template.logo:
        await sem.acquire()
        callback = Callback(onItemDuplicated, item=itm, semaphore=sem)
        wsClient.sendMessageJson(duplicateSceneItem(template.name, template.items[itm]['sceneItemId'], sceneInfo.name),
                                 callback=callback)


def onSceneCreated(msg, sceneInfo: SceneInfo, semaphore: Semaphore):
    asyncio.create_task(taskCreateScene(sceneInfo))
    semaphore.release()


def onTemplateItemsListed(msg, template: SceneTemplate, semaphore: Semaphore):
    for sceneItem in innerData(msg)['sceneItems']:
        template.addSceneItem(sceneItem)

    semaphore.release()

def onSceneRemoved(msg, semaphore):
    semaphore.release()

async def sceneTask():
    scenes = generateScenes()

    sem = Semaphore()
    for scene in scenes:
        await sem.acquire()
        callback = Callback(onSceneRemoved, semaphore=sem)
        wsClient.sendMessageJson(removeScene(scene.name), callback=callback)

    await sem.acquire()
    sem.release()

    if not CLEAR_ONLY:

        for template in ALL_TEMPLATES:
            await sem.acquire()
            callback = Callback(onTemplateItemsListed, template=template, semaphore=sem)
            wsClient.sendMessageJson(getSceneItemList(template.name), callback=callback)
        await sem.acquire()
        sem.release()


        for scene in scenes:
            await sem.acquire()
            print("Generating " + scene.name)
            callback = Callback(onSceneCreated, sceneInfo=scene, semaphore=sem)
            wsClient.sendMessageJson(createScene(scene.name), callback=callback)


def onAuthenticated(msg):
    print(msg)
    asyncio.create_task(sceneTask())


async def main():
    global wsClient
    wsClient = OBSWebsocketClient("ws://{}:{}".format(OBS_ADDRESS, OBS_PORT)) #"ws://192.168.114.230:4444" "ws://127.0.0.1:4444"
    await wsClient.connect(password=OBS_PASSWORD, onAuthenticated=Callback(onAuthenticated))
    rcvLoop = wsClient.recieveLoop()
    sendLoop = wsClient.sendLoop()

    await asyncio.gather(rcvLoop, sendLoop, return_exceptions=True)
    exit()

#endregion

if __name__ == "__main__":
    asyncio.run(main())