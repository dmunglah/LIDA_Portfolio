#!/usr/bin/env python3
"""
extract_nose_batch.py

Batch-processes DeepLabCut CSV outputs in a directory, classifies mouse Nose
(or MidForehead fallback) relative to apparatus regions, filters by likelihood,
computes distances, and aggregates per file summary statistics.

Key features:
1. Confidence filtering via likelihood threshold (LIKELIHOOD_THRESH).
2. Batch processing of all '*.csv' files in the working directory, excluding outputs.
3. OOP design with PolygonRegion, CircleRegion, and BatchExtractor.
4. Per-frame CSV/JSON outputs and a distances CSV.
5. Aggregated summary_stats.csv with counts and percentages for each zone.

Usage:
    pip install shapely
    python3 extract_nose_batch.py

Outputs (for each input 'XYZ.csv'):
    output_XYZ_classified.csv
    output_XYZ_classified.json
    distances_XYZ.csv

And a global:
    summary_stats.csv
"""

import os
import glob
import csv
import json
import re
from shapely.geometry import Point, Polygon

# ——— CONFIGURATION ———
LIKELIHOOD_THRESH = 0.9     # Only accept feature points with likelihood ≥ this
FALLBACK          = ["Nose", "MidForehead"]
VERTEX_RADII      = {i: 5 for i in range(4)}  # px buffer around each hopper corner

SUMMARY_OUT = "summary_stats.csv"

def safe_float(val):
    """Convert to float or return None."""
    try:
        return float(val)
    except:
        return None

def extract_frame_number(imgfile):
    """Parse 'img083.png' → 83."""
    m = re.search(r"(\d+)", imgfile)
    return int(m.group(1)) if m else -1

class PolygonRegion:
    """4-corner convex polygon + per-vertex buffers."""
    def __init__(self, corner_cols, vertex_radii=None):
        self.corners = corner_cols
        self.radii   = vertex_radii or {}

    def polygon(self, row):
        pts = []
        for xi, yi in self.corners:
            x = safe_float(row[xi]); y = safe_float(row[yi])
            if x is None or y is None:
                return None
            pts.append((x, y))
        poly = Polygon(pts)
        return poly if poly.is_valid else None

    def contains(self, row, pt):
        poly = self.polygon(row)
        return poly is not None and pt.within(poly)

    def dist_to_hull(self, row, pt):
        poly = self.polygon(row)
        return pt.distance(poly) if poly else None

    def vertex_distances(self, row, pt):
        d = {}
        for i,(xi,yi) in enumerate(self.corners):
            x=safe_float(row[xi]); y=safe_float(row[yi])
            d[i] = pt.distance(Point(x,y)) if (x is not None and y is not None) else None
        return d

    def within_vertex_buffers(self, row, pt):
        flags = {}
        for i,(xi,yi) in enumerate(self.corners):
            x=safe_float(row[xi]); y=safe_float(row[yi])
            if x is None or y is None:
                flags[i] = False
            else:
                dist = pt.distance(Point(x,y))
                flags[i] = dist <= self.radii.get(i,0)
        return flags

class CircleRegion:
    """Circular region around a single bodypart + fixed radius."""
    def __init__(self, x_col, y_col, radius):
        self.x_col = x_col; self.y_col = y_col; self.radius = radius

    def contains(self, row, pt):
        x = safe_float(row[self.x_col]); y = safe_float(row[self.y_col])
        return x is not None and y is not None and pt.distance(Point(x,y))<=self.radius

    def dist_to_center(self, row, pt):
        x = safe_float(row[self.x_col]); y = safe_float(row[self.y_col])
        return pt.distance(Point(x,y)) if (x is not None and y is not None) else None

class BatchExtractor:
    """
    Finds all input CSVs, and for each:
      - parses headers
      - builds feature index + regions
      - loops over frames with likelihood filtering
      - writes per-file outputs
      - collects summary stats
    """
    def __init__(self, threshold=LIKELIHOOD_THRESH):
        self.threshold = threshold
        self.summary = []

    def find_inputs(self):
        """All .csv in cwd, excluding our outputs."""
        all_csv = glob.glob("*.csv")
        return [f for f in all_csv if not f.startswith(("output_","distances_","summary_"))]

    def build_index(self, bp_row, coord_row):
        idx = {}
        for i, (bp,c) in enumerate(zip(bp_row, coord_row)):
            if bp and c in ("x","y","likelihood"):
                idx.setdefault(bp, {})[c] = i
        return idx

    def process_file(self, path):
        base = os.path.splitext(os.path.basename(path))[0]
        out_csv = f"output_{base}_classified.csv"
        out_json= f"output_{base}_classified.json"
        out_dist= f"distances_{base}.csv"

        with open(path,newline="") as f:
            r = csv.reader(f)
            next(r); next(r)
            bp_row = next(r); coord_row = next(r)
            idx = self.build_index(bp_row, coord_row)

            # setup regions
            cfg = json.load(open(JSON_IN))["targets"]
            # hopper
            hp_pts = cfg["hopper"]["points"]
            corners = [(idx[p]["x"], idx[p]["y"]) for p in hp_pts]
            hopper = PolygonRegion(corners, VERTEX_RADII)
            # bottle
            bt = cfg["bottle"]; p=bt["points"][0]
            bottle = CircleRegion(idx[p]["x"], idx[p]["y"], bt["radius"])

            cls_rows=[]; dist_rows=[]
            counts = {"hopper":0,"bottle":0,"other":0}

            for row in r:
                video=row[1]; frame=extract_frame_number(row[2])
                # pick feature with likelihood
                pt=None
                for feat in FALLBACK:
                    if feat in idx:
                        lik = safe_float(row[idx[feat]["likelihood"]]) or 0
                        if lik<self.threshold: continue
                        x=safe_float(row[idx[feat]["x"]]); y=safe_float(row[idx[feat]["y"]])
                        if x is not None and y is not None:
                            pt=Point(x,y); break

                # classify
                cr={"file":video,"frame":frame,"hopper":0,"bottle":0,"other":0}
                zone="other"
                if pt:
                    if hopper.contains(row,pt):
                        cr["hopper"]=1; zone="hopper"
                    elif bottle.contains(row,pt):
                        cr["bottle"]=1; zone="bottle"
                counts[zone]+=1
                cls_rows.append(cr)

                # distances
                dr={"file":video,"frame":frame}
                if pt:
                    dr["dist_to_hull"] = hopper.dist_to_hull(row,pt)
                    vd = hopper.vertex_distances(row,pt)
                    vb = hopper.within_vertex_buffers(row,pt)
                    for i in vd: dr[f"dist_v{i}"]=vd[i]
                    for i in vb: dr[f"within_v{i}"]=vb[i]
                    dr["dist_to_bottle"] = bottle.dist_to_center(row,pt)
                else:
                    dr["dist_to_hull"]=None
                    for i in range(4):
                        dr[f"dist_v{i}"]=None; dr[f"within_v{i}"]=False
                    dr["dist_to_bottle"]=None
                dist_rows.append(dr)

        # write outputs
        with open(out_csv,"w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=["file","frame","hopper","bottle","other"])
            w.writeheader(); w.writerows(cls_rows)
        with open(out_json,"w") as f:
            js=[{"file":r["file"],"frame":r["frame"],
                 "apparatus":("hopper" if r["hopper"] else
                             "bottle" if r["bottle"] else "other")}
                for r in cls_rows]
            json.dump(js,f,indent=2)
        with open(out_dist,"w",newline="") as f:
            keys=list(dist_rows[0].keys())
            w=csv.DictWriter(f,fieldnames=keys)
            w.writeheader(); w.writerows(dist_rows)

        # summary
        total = sum(counts.values())
        self.summary.append({
            "file": base,
            "total_frames": total,
            **{k: counts[k] for k in counts},
            **{f"{k}_pct": counts[k]/total*100 for k in counts}
        })

    def write_summary(self):
        keys=["file","total_frames",
              "hopper","bottle","other",
              "hopper_pct","bottle_pct","other_pct"]
        with open(SUMMARY_OUT,"w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=keys)
            w.writeheader(); w.writerows(self.summary)
        print(f"✅ Wrote {SUMMARY_OUT}")

    def run(self):
        inputs = self.find_inputs()
        for p in inputs:
            print("Processing", p)
            self.process_file(p)
        self.write_summary()

if __name__=="__main__":
    extractor = BatchExtractor()
    extractor.run()
