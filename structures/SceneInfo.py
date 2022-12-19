from typing import List


class SceneInfo:

    def __init__(self, name: str, sources: List[str], template: str = "Default"):
        self.name = name
        self.sources = sources
        self.template = template
