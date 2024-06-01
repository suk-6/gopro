import os
import math
from datetime import datetime
import os.path as osp
import xml.etree.ElementTree as ET


class Parse:
    def __init__(self, path) -> None:
        self.tmpPath = osp.join("/", "tmp")
        self.uuid = os.urandom(16).hex()
        self.videoPath = path
        print(self.uuid, self.videoPath)

        self.parse()
        self.gpxData = self.getGPXData()
        self.calibration()

        os.remove(osp.join(self.tmpPath, self.uuid + ".kml"))
        os.remove(osp.join(self.tmpPath, self.uuid + ".gpx"))

    def parse(self):
        try:
            os.system(
                f"gopro2gpx -s {self.videoPath} {osp.join(self.tmpPath, self.uuid)} > /dev/null"
            )
        except:
            raise Exception("Is not a GoPro video file")

    def getGPXData(self):
        namespaces = {
            "": "http://www.topografix.com/GPX/1/1",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "wptx1": "http://www.garmin.com/xmlschemas/WaypointExtension/v1",
            "gpxtrx": "http://www.garmin.com/xmlschemas/GpxExtensions/v3",
            "gpxtpx": "http://www.garmin.com/xmlschemas/TrackPointExtension/v2",
            "gpxx": "http://www.garmin.com/xmlschemas/GpxExtensions/v3",
            "trp": "http://www.garmin.com/xmlschemas/TripExtensions/v1",
            "adv": "http://www.garmin.com/xmlschemas/AdventuresExtensions/v1",
            "prs": "http://www.garmin.com/xmlschemas/PressureExtension/v1",
            "tmd": "http://www.garmin.com/xmlschemas/TripMetaDataExtensions/v1",
            "vptm": "http://www.garmin.com/xmlschemas/ViaPointTransportationModeExtensions/v1",
            "ctx": "http://www.garmin.com/xmlschemas/CreationTimeExtension/v1",
            "gpxacc": "http://www.garmin.com/xmlschemas/AccelerationExtension/v1",
            "gpxpx": "http://www.garmin.com/xmlschemas/PowerExtension/v1",
            "vidx1": "http://www.garmin.com/xmlschemas/VideoExtension/v1",
        }

        try:
            gpxPath = osp.join(self.tmpPath, self.uuid + ".gpx")

            data = {
                "startTime": None,
                "points": [],
            }

            tree = ET.parse(gpxPath)
            root = tree.getroot()

            metadata = root.find("metadata", namespaces)
            data["startTime"] = metadata.find("time", namespaces).text
            startTime = datetime.fromisoformat(data["startTime"].replace("Z", "+00:00"))

            trk = root.find("trk", namespaces)
            trkseg = trk.find("trkseg", namespaces)
            for tkrpt in trkseg.iterfind("trkpt", namespaces):
                lat, lng = tkrpt.attrib["lat"], tkrpt.attrib["lon"]
                ele = tkrpt.find("ele", namespaces).text
                time = tkrpt.find("time", namespaces).text

                timeDt = datetime.fromisoformat(time.replace("Z", "+00:00"))
                duration = (timeDt - startTime).total_seconds()

                extensions = tkrpt.find("extensions", namespaces)
                speed = extensions.find(".//gpxtpx:speed", namespaces).text

                data["points"].append(
                    {
                        "lat": lat,
                        "lng": lng,
                        "ele": ele,
                        "time": time,
                        "duration": duration,
                        "speed": speed,
                        "video": "/".join(
                            [
                                p
                                for p in self.videoPath.split(os.sep)[
                                    self.videoPath.split(os.sep).index("road-data") :
                                ]
                            ]
                        ),
                    }
                )

            data["totalDuration"] = data["points"][-1]["duration"]

            return data

        except:
            raise Exception("Failed to parse GPX file")

    def haversine(self, lat1, lng1, lat2, lng2):
        radius = 6371.0

        lat1 = math.radians(lat1)
        lng1 = math.radians(lng1)
        lat2 = math.radians(lat2)
        lng2 = math.radians(lng2)

        dlng = lng2 - lng1
        dlat = lat2 - lat1

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = radius * c

        return distance

    def calculateLength(self):
        points = self.gpxData["points"]
        length = 0

        for point in range(len(points) - 1):
            lat1, lng1 = float(points[point]["lat"]), float(points[point]["lng"])
            lat2, lng2 = float(points[point + 1]["lat"]), float(
                points[point + 1]["lng"]
            )

            length += self.haversine(lat1, lng1, lat2, lng2)

        return length

    def calibration(self):
        points = self.gpxData["points"]
        calibrated = []
        skip = -1

        for point in range(len(points) - 1):
            if skip == point:
                continue

            lat1, lng1 = float(points[point]["lat"]), float(points[point]["lng"])
            lat2, lng2 = float(points[point + 1]["lat"]), float(
                points[point + 1]["lng"]
            )

            distanceDifference = self.haversine(lat1, lng1, lat2, lng2)

            if distanceDifference > 0.0001:  # 1 meter
                skip = point + 1
                print(
                    f"calibrate: {point}, {distanceDifference}, {points[point]['duration']}"
                )

            calibrated.append(points[point])

        self.gpxData["points"] = calibrated
