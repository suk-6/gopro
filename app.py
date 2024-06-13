import os
import os.path as osp
import json
from tqdm import tqdm

from parse import Parse


class App:
    def __init__(self, path) -> None:
        self.path = path
        self.videos = self.getVideos()
        self.boundaries = self.getBoundaries()

        self.saveJson()

    def getVideos(self):
        videos = []
        for root, _, files in os.walk(self.path):
            for file in files:
                if file.lower().endswith(".mp4"):
                    videos.append(osp.join(root, file))
        return videos

    def getBoundaries(self):
        boundaries = []
        for file in os.listdir(osp.join(".", "boundary")):
            if file.lower().endswith(".json"):
                with open(osp.join(".", "boundary", file)) as f:
                    boundaries.append(json.load(f))

        return boundaries

    def saveJson(self):
        result = {
            "duration": 0,
            "length": 0,
            "points": [],
        }

        for video in tqdm(self.videos, desc="Parsing videos", unit="video"):
            parse = Parse(video)
            result["points"].extend(parse.gpxData["points"])
            result["length"] += parse.calculateLength()
            result["duration"] += parse.gpxData["totalDuration"]

        for boundary in self.boundaries:
            result["points"].extend(boundary["coordinates"])

        with open("goprodata.json", "w") as f:
            json.dump(result, f)


if __name__ == "__main__":
    path = osp.join("/", "Volumes", "T7", "road-data")
    app = App(path)
