import os
import os.path as osp
import json

from parse import Parse


class App:
    def __init__(self, path) -> None:
        self.path = path
        self.videos = self.getVideos()

        self.saveJson()

    def getVideos(self):
        videos = []
        for root, _, files in os.walk(self.path):
            for file in files:
                if file.lower().endswith(".mp4"):
                    videos.append(osp.join(root, file))
        return videos

    def saveJson(self):
        result = {
            "duration": 0,
            "length": 0,
            "points": [],
        }

        for video in self.videos:
            parse = Parse(video)
            result["points"].extend(parse.gpxData["points"])
            result["length"] += parse.calculateLength()
            result["duration"] += parse.gpxData["totalDuration"]

        with open("goprodata.json", "w") as f:
            json.dump(result, f)


if __name__ == "__main__":
    path = osp.join("/", "Volumes", "T7", "road-data", "240601")
    app = App(path)
