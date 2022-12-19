from typing import List


class SceneTemplate:

    def __init__(self, name: str, background: List[str], slides: List[str], speakers: List[str], overlays: List[str], logo: List[str]):
        self.name: str = name
        self.background: List[str] = background
        self.slides: List[str] = slides
        self.speakers: List[str] = speakers
        self.overlays: List[str] = overlays
        self.logo: List[str] = logo

        self.items = {}

    def addSceneItem(self, sceneItem):
        self.items[sceneItem["sourceName"]] = sceneItem