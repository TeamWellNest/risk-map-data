"""Project the US county and Canadian census division boundaries into one
Albers equal-area view and write SVG path strings.
Output: pipeline/out/geom.json  {vb, us:{fips:path}, ca:{cduid:path}, us_states:path, ca_prov:path, hi_box}
Run:  .venv/bin/python -I pipeline/04_geometry.py
"""
import json, io, zipfile, math, time, shapefile
from shapely.geometry import shape, mapping, MultiPolygon, Polygon
from shapely.ops import unary_union
t0 = time.time()
# ---------- load ----------
z = zipfile.ZipFile("raw/census/cb_2021_us_county_20m.zip"); b = "cb_2021_us_county_20m"
r = shapefile.Reader(shp=io.BytesIO(z.read(b + ".shp")), dbf=io.BytesIO(z.read(b + ".dbf")), shx=io.BytesIO(z.read(b + ".shx")))
feats = []
def drop_far_west(geom):
    """Aleutian parts east of the antimeridian (positive longitude) are dropped."""
    polys = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)
    keep = [p for p in polys if p.bounds[0] < 0]
    return MultiPolygon(keep) if len(keep) > 1 else keep[0]
for sr in r.iterShapeRecords():
    d = sr.record.as_dict()
    if d["GEOID"].startswith("72"): continue
    g = shape(sr.shape.__geo_interface__).buffer(0)
    if d["STATEFP"] == "02": g = drop_far_west(g)
    feats.append({"type": "Feature", "properties": {"id": d["GEOID"], "c": "us", "st": d["STATEFP"]}, "geometry": mapping(g)})
cds = json.load(open("raw/statcan/lcd_000b21s_e_cartographic_wgs84_generalized0.002deg.geojson"))["features"]
for c in cds:
    p = c["properties"]
    feats.append({"type": "Feature", "properties": {"id": p["CDUID"], "c": "ca", "st": p["PRUID"]}, "geometry": c["geometry"]})
print("features:", len(feats), "| load secs", round(time.time() - t0, 1))
# ---------- simplification happens AFTER projection, per shape (shapely, topology-safe per polygon) ----------
simp = feats
# ---------- projection: Albers equal-area conic, spherical ----------
PHI1, PHI2, PHI0, LAM0 = map(math.radians, (30, 60, 45, -100))
n = (math.sin(PHI1) + math.sin(PHI2)) / 2
C = math.cos(PHI1) ** 2 + 2 * n * math.sin(PHI1)
rho0 = math.sqrt(C - 2 * n * math.sin(PHI0)) / n
def proj(lon, lat, lam0=LAM0, n=n, C=C, rho0=rho0):
    lam, phi = math.radians(lon), math.radians(lat)
    rho = math.sqrt(max(C - 2 * n * math.sin(phi), 0)) / n
    th = n * (lam - lam0)
    return rho * math.sin(th), rho0 - rho * math.cos(th)
# Hawaii gets its own small Albers (inset)
HP1, HP2, HP0, HL0 = map(math.radians, (8, 18, 13, -157))
hn = (math.sin(HP1) + math.sin(HP2)) / 2; hC = math.cos(HP1) ** 2 + 2 * hn * math.sin(HP1); hrho0 = math.sqrt(hC - 2 * hn * math.sin(HP0)) / hn
def proj_hi(lon, lat): return proj(lon, lat, HL0, hn, hC, hrho0)
def project_geom(g, fn):
    polys = [g] if g.geom_type == "Polygon" else list(g.geoms)
    out = []
    for p in polys:
        ext = [fn(x, y) for x, y in p.exterior.coords]
        ints = [[fn(x, y) for x, y in r.coords] for r in p.interiors]
        out.append(Polygon(ext, ints))
    return MultiPolygon(out) if len(out) > 1 else out[0]
main, hawaii = {}, {}
for f in simp:
    g = shape(f["geometry"]).buffer(0)
    p = f["properties"]; key = (p["c"], p["id"], p["st"])
    if p["c"] == "us" and p["st"] == "15": hawaii[key] = project_geom(g, proj_hi)
    else: main[key] = project_geom(g, proj)
    f["geometry"] = None  # free memory
# simplify in projected units once the scale is known (below), so tolerance = fraction of a viewBox unit
# ---------- fit to viewBox ----------
W = 1000.0
minx = min(g.bounds[0] for g in main.values()); maxx = max(g.bounds[2] for g in main.values())
miny = min(g.bounds[1] for g in main.values())
maxy = proj(-100, 75.5)[1]   # crop the empty High Arctic band: nothing north of 75.5 N is lost but uninhabited islands
s = W / (maxx - minx); H = round((maxy - miny) * s, 1)
def to_svg(x, y): return (x - minx) * s, (maxy - y) * s   # flip y for SVG
TOL = 0.45 / s   # 0.45 viewBox units (about 2.5 km): invisible at any screen size
MIN_PART, MIN_HOLE = 0.25, 1.5   # square viewBox units: islets and small lakes vanish at any screen size
def prune(g, min_part=MIN_PART, min_hole=MIN_HOLE):
    polys = [g] if g.geom_type == "Polygon" else list(g.geoms)
    biggest = max(polys, key=lambda p: p.area)
    keep = []
    for p in polys:
        if p.area < min_part and p is not biggest: continue
        keep.append(Polygon(p.exterior.coords, [r.coords for r in p.interiors if Polygon(r.coords).area >= min_hole]))
    return MultiPolygon(keep) if len(keep) > 1 else keep[0]
def tidy(g):
    g2 = prune(g.simplify(TOL, preserve_topology=True).buffer(0))
    return g2 if not g2.is_empty else g
main = {k: tidy(g) for k, g in main.items()}
import sys; sys.stdout.write("simplified main | secs %.1f\n" % (time.time() - t0))
# Hawaii inset: scale to about 110 units wide, placed bottom-left
hminx = min(g.bounds[0] for g in hawaii.values()); hmaxx = max(g.bounds[2] for g in hawaii.values())
hminy = min(g.bounds[1] for g in hawaii.values()); hmaxy = max(g.bounds[3] for g in hawaii.values())
hs = 120.0 / (hmaxx - hminx); hw, hh = 120.0, (hmaxy - hminy) * hs
hawaii = {k: prune(g.simplify(0.45 / hs, preserve_topology=True).buffer(0), MIN_PART / hs / hs * s * s, MIN_HOLE / hs / hs * s * s) for k, g in hawaii.items()}
HX, HY = 40.0, H - hh - 30.0
def to_svg_hi(x, y): return HX + (x - hminx) * hs, HY + (hmaxy - y) * hs
def path(g, fn):
    polys = [g] if g.geom_type == "Polygon" else list(g.geoms)
    parts = []
    for p in polys:
        for ring in [p.exterior] + list(p.interiors):
            pts = [fn(x, y) for x, y in ring.coords]
            parts.append("M" + "L".join("%.1f %.1f" % (x, y) for x, y in pts[:-1]) + "Z")
    return "".join(parts)
us, ca = {}, {}
for (c, i, st), g in main.items(): (us if c == "us" else ca)[i] = path(g, to_svg)
for (c, i, st), g in hawaii.items(): us[i] = path(g, to_svg_hi)
# state / province outlines from the SAME simplified geometry so edges coincide
def union_by(prefix_c, fn, pool):
    groups = {}
    for (c, i, st), g in pool.items():
        if c == prefix_c: groups.setdefault(st, []).append(g)
    return "".join(path(prune(unary_union(gs).buffer(0)), fn) for gs in groups.values())
t2 = time.time()
us_states = union_by("us", to_svg, main) + union_by("us", to_svg_hi, hawaii)
ca_prov = union_by("ca", to_svg, main)
print("outlines | secs", round(time.time() - t2, 1))
out = {"vb": [0, 0, int(W), int(math.ceil(H))], "us": us, "ca": ca, "us_states": us_states, "ca_prov": ca_prov,
       "hi_box": [round(HX - 8, 1), round(HY - 8, 1), round(hw + 16, 1), round(hh + 16, 1)]}
json.dump(out, open("pipeline/out/geom.json", "w"), separators=(",", ":"))
tot = sum(len(v) for v in us.values()) + sum(len(v) for v in ca.values())
print("viewBox", out["vb"], "| us paths", len(us), "| ca paths", len(ca), "| path chars", tot, "| outlines chars", len(us_states) + len(ca_prov), "| total secs", round(time.time() - t0, 1))
