#! /usr/bin/env python3
# import shapely
# from shapely import Point, MultiPoint, Polygon

# hull = shapely.convex_hull(MultiPoint([
#     (0, 0),
#     (0, 1),
#     (1, 1),
#     (1, 0)
# ]))

# hull2 = shapely.convex_hull(MultiPoint([
#     (0, 0)
# ]))

# point = Point(1, 0)

# print(hull)
# print(point)

# distance = point.distance(hull)
# distance2 = point.distance(hull2)

# print(distance)
# print(distance2)


# FIRST TEST: Load the JSON and check it is OK.

from collections import OrderedDict
from enum import Enum
import json
import pandas
from numpy import isnan
from shapely import Point, convex_hull, MultiPoint
import logging
import sys

logging.basicConfig(format = "%(levelname)s: %(message)s", level = "ERROR")


class TestRegionType(Enum):
    @classmethod
    def from_string(cls, s):
        if s == "fixed":
            return cls.FIXED
        if s == "dynamic":
            return cls.DYNAMIC
        raise ValueError("invalid type value")
    FIXED = "fixed"
    DYNAMIC = "dynamic"

class TestRegion(object):
    @classmethod
    def from_dict(cls, label, d):
        logging.debug(f"loading region \"{label}\" from dict")
        return TestRegion(label, type = TestRegionType.from_string(d["type"]), radius = d["radius"], features = d["features"], points = d["points"])
    def __init__(self, label, type, radius, features, points):
        self._label = str(label)
        self._type = type
        self._radius = float(radius)
        self._features = features
        self._points = points
    @property
    def label(self):
        return self._label
    @label.setter
    def label(self, new_label):
        self._label = str(new_label)
    @property
    def type(self):
        return self._type
    @type.setter
    def type(self, new_type):
        if not isinstance(new_type, TestRegionType):
            raise ValueError("region type must be a TestRegionType")
        self._type = new_type
    @property
    def radius(self):
        return self._radius
    @radius.setter
    def radius(self, new_radius):
        self._radius = float(new_radius)
    @property
    def features(self):
        return self._features
    @property
    def points(self):
        return self._points

class TestRegionSet(object):
    @classmethod
    def from_json(cls, path):
        logging.info(f"reading feature parameters from JSON \"{path}\"")
        with open(path, "rt") as json_handle:
            json_data = json.load(json_handle)
        regions = TestRegionSet()
        for k, v in json_data.items():
            regions.regions[k] = TestRegion.from_dict(k, v)
        logging.info(f"read {len(regions.regions)} regions")
        return regions
    def __init__(self):
        self._regions = OrderedDict()
    def create_hulls(self, d):
        d = d.data
        hulls = OrderedDict()
        for region in self._regions.values():
            hull_points = []
            for point_feature in region.points:
                point_x = d[(d["feature"] == point_feature) & (d["coord"] == "x") & (pandas.notnull(d["value"]))]["value"].mean()
                point_y = d[(d["feature"] == point_feature) & (d["coord"] == "y") & (pandas.notnull(d["value"]))]["value"].mean()
                hull_points.append(Point(point_x, point_y))
            hull = convex_hull(MultiPoint(hull_points))
            hulls[region.label] = hull
        return hulls
    @property
    def regions(self):
        return self._regions

class TrackingData(object):
    @classmethod
    def from_csv(cls, path):
        logging.info(f"reading tracking data from CSV \"{path}\"")
        df = pandas.read_csv(path)
        return TrackingData(df)
    def __init__(self, df):
        self._data = df
        self._individuals = list(pandas.unique(self._data["individual"]))
    @property
    def frames(self):
        return list(pandas.unique(self._data["frame"]))
    @property
    def individuals(self):
        return self._individuals
    def select_point(self, frame, individual, feature):
        frame_i = self._data["frame"] == frame
        individual_i = self._data["individual"] == individual
        feature_i = self._data["feature"] == feature
        point_x = self._data[frame_i & individual_i & feature_i & (self._data["coord"] == "x")]["value"].mean()
        point_y = self._data[frame_i & individual_i & feature_i & (self._data["coord"] == "y")]["value"].mean()
        if isnan(point_x) or isnan(point_y):
            return None
        else:
            return Point(point_x, point_y)
    @property
    def data(self):
        return self._data

# Load featureset from JSON:
features = TestRegionSet.from_json("../tests/test_hull_2.json")

# Load tracking data from CSV into a Pandas dataframe:
d = TrackingData.from_csv("../tests/tracking-analysis-reformatted.csv")

# Test Hulls:
test_hulls = features.create_hulls(d)

# Make sure we always keep the features in order:
feature_labels = list(test_hulls.keys())
header = ["frame"]
header.extend(feature_labels)
print(",".join(header))

for frame_i in d.frames:
    feature_counts = dict()
    for hull_id in feature_labels:
        feature_counts[hull_id] = 0
    # logging.debug(f"testing frame {frame_i}")
    for region in features.regions.values():
        # logging.debug(f"testing frame {frame_i} region {region.label}")
        feature_hull = test_hulls[region.label]
        for individual_i in d.individuals:
            # logging.debug(f"testing frame {frame_i} region {region.label} individual {individual_i}")
            min_distance = float("inf")
            for test_feature_i in region.features:
                logging.debug(f"testing frame {frame_i} region {region.label} individual {individual_i} feature {test_feature_i}")
                # Get the point we care about:
                test_point = d.select_point(frame_i, individual_i, test_feature_i)
                if test_point is not None:
                    test_distance = test_point.distance(feature_hull)
                    logging.debug(f"testing against point {test_point} (distance = {test_distance})")
                    min_distance = min(min_distance, test_distance)
            logging.debug(f"frame {frame_i} region {region.label} individual {individual_i} minimum diatance across all test features is {min_distance}")
            if min_distance <= region.radius:
                logging.debug(f"frame {frame_i} region {region.label} individual {individual_i} logged")
                feature_counts[hull_id] += 1
    output = list()
    output.append(str(frame_i))
    for i in feature_labels:
        output.append(str(feature_counts[i]))
    print(",".join(output))

                


# # Try to iterate through each line and see what happens:
# frame = 0
# frame_d = d[d["frame"] == frame]

# # Choose which region to test:
# for region in features.regions.values():
#     for individual in individuals:
#         for test_feature in region.features:
#             test_feature_x = frame_d[(frame_d["individual"] == individual) & (frame_d["feature"] == test_feature) & (frame_d["coord"] == "x")]["value"].mean()
#             test_feature_y = frame_d[(frame_d["individual"] == individual) & (frame_d["feature"] == test_feature) & (frame_d["coord"] == "y")]["value"].mean()
#             if (not isnan(test_feature_x)) & (not isnan(test_feature_y)):
#                 test_point = Point(test_feature_x, test_feature_y)
#                 distance = test_point.distance(test_hulls["hopper"])
#                 intersect = distance <= region.radius
#                 print(f"{frame},{region.label},{individual},{test_feature},{distance},{intersect}")
#             else:
#                 print(f"{frame},{region.label},{individual},{test_feature},-,False")
