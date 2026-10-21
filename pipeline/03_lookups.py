"""Build pipeline/out/zip_county.json (ZCTA -> county FIPS by largest land
overlap) and pipeline/out/fsa_cd.json (FSA -> census division by largest area
overlap, spatial join on the StatCan 2021 boundary files).
Run:  .venv/bin/python -I pipeline/03_lookups.py
"""
import json, csv, collections, time
from shapely.geometry import shape
from shapely.strtree import STRtree
# ZIP (ZCTA) -> county
best = {}
with open("raw/zcta-county/tab20_zcta520_county20_natl.txt", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f, delimiter="|"):
        z = row["GEOID_ZCTA5_20"]; c = row["GEOID_COUNTY_20"]
        if not z or c.startswith("72"): continue
        a = int(row["AREALAND_PART"] or 0)
        if z not in best or a > best[z][1]: best[z] = (c, a)
zip_county = {z: v[0] for z, v in best.items()}
print("ZCTAs:", len(zip_county))
json.dump(zip_county, open("pipeline/out/zip_county.json", "w"), separators=(",", ":"))
# FSA -> census division
t = time.time()
cds = json.load(open("raw/statcan/lcd_000b21s_e_cartographic_wgs84_generalized0.002deg.geojson"))["features"]
fsas = json.load(open("raw/statcan/lfsa000b21s_e_cartographic_wgs84_generalized0.0005deg.geojson"))["features"]
cd_geoms = [shape(c["geometry"]).buffer(0) for c in cds]; cd_ids = [c["properties"]["CDUID"] for c in cds]
tree = STRtree(cd_geoms)
fsa_cd = {}; straddle = 0; share_of_best = []
for f in fsas:
    g = shape(f["geometry"]).buffer(0); fid = f["properties"]["CFSAUID"]
    cand = tree.query(g, predicate="intersects")
    areas = []
    for i in cand:
        a = g.intersection(cd_geoms[i]).area
        if a > 0: areas.append((a, cd_ids[i]))
    if not areas:
        i = tree.nearest(g); fsa_cd[fid] = cd_ids[i]; continue
    areas.sort(reverse=True)
    fsa_cd[fid] = areas[0][1]
    tot = sum(a for a, _ in areas); share_of_best.append(areas[0][0] / tot)
    if len(areas) > 1 and areas[1][0] / tot > 0.05: straddle += 1
print("FSAs:", len(fsa_cd), "| straddle another CD by >5%:", straddle, "| secs:", round(time.time() - t, 1))
print("share of FSA area inside its assigned CD: median %.2f, under 0.6: %d" % (sorted(share_of_best)[len(share_of_best)//2], sum(1 for s in share_of_best if s < 0.6)))
json.dump(fsa_cd, open("pipeline/out/fsa_cd.json", "w"), separators=(",", ":"))
