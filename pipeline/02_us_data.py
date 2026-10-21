"""Build pipeline/out/us_data.json: per county FIPS -> EPA zone, CDC lab-test
share at or above 4 pCi/L (2008-2017 window) and the number of buildings tested.
Run:  .venv/bin/python -I pipeline/02_us_data.py
"""
import json, io, zipfile, re, shapefile, collections
# Census county names (cb_2021, 8 old Connecticut counties, matches EPA + ZCTA file)
z = zipfile.ZipFile("raw/census/cb_2021_us_county_20m.zip"); b = "cb_2021_us_county_20m"
r = shapefile.Reader(shp=io.BytesIO(z.read(b + ".shp")), dbf=io.BytesIO(z.read(b + ".dbf")), shx=io.BytesIO(z.read(b + ".shx")))
counties = {}
for rec in r.iterRecords():
    d = rec.as_dict(); counties[d["GEOID"]] = {"name": d["NAME"], "lsad": d["NAMELSAD"], "st": d["STUSPS"]}
print("census counties:", len(counties), "| excluding PR:", sum(1 for k in counties if not k.startswith("72")))

def norm(s):
    s = s.lower().replace("-", " ").replace("st. ", "st ").replace("ste. ", "ste ")
    s = re.sub(r"[^a-z0-9 ]", "", s)
    return " ".join(s.split())
by_key = {}
for fips, c in counties.items():
    by_key[(c["st"], norm(c["lsad"]))] = fips
    by_key.setdefault((c["st"], norm(c["name"])), fips)

# EPA zones
epa = json.load(open("raw/epa-zones/radon-zones-202406.json", encoding="utf-8-sig"))["data"]
# Manual crosswalk for rows whose names differ from Census (verified by hand, Oct 20, 2026)
MANUAL = {
 ("AK","valdez cordova"): None,            # split in 2019 into Chugach (02063) + Copper River (02066): handled below
 ("AK","wade hampton"): "02158",           # renamed Kusilvak Census Area
 ("AK","prince of wales outer ketchikan"): "02198",  # now Prince of Wales-Hyder
 ("AK","wrangell petersburg"): "02275",    # Wrangell City and Borough (Petersburg 02195 handled below)
 ("SD","shannon"): "02102" if False else "46102",  # renamed Oglala Lakota
 ("LA","la salle"): "22059",
 ("NM","dona ana"): "35013",
 ("MT","yellowstone national park"): None, # not a county since 1997
}
SPLIT_EXTRA = {("AK","valdez cordova"): ["02063","02066"], ("AK","wrangell petersburg"): ["02195"]}
zone = {}; unmatched = []
for row in epa:
    if row["Zone"] in (".", "", None): continue
    cs = row["County,State"]; st = cs.rsplit(",", 1)[-1].strip()
    if cs == "District of Columbia":
        zone["11001"] = int(row["Zone"]); continue
    label = row["COUNTY LABEL"]
    key = (st, norm(label)); key2 = (st, norm(cs.rsplit(",", 1)[0]))
    fips = by_key.get(key) or by_key.get(key2)
    if not fips and st == "VA":  # independent cities: EPA writes the city name only
        fips = by_key.get((st, norm(cs.rsplit(",", 1)[0]) + " city"))
    if not fips:
        mk = (st, norm(cs.rsplit(",", 1)[0]))
        if mk in MANUAL:
            fips = MANUAL[mk]
            for extra in SPLIT_EXTRA.get(mk, []): zone[extra] = int(row["Zone"])
        else:
            unmatched.append(cs); continue
    if fips: zone[fips] = int(row["Zone"])
zone.setdefault("02105", 3)  # Hoonah-Angoon Census Area: carved out of EPA's "Skagway-Hoonah-Angoon" row (Zone 3) in 2007
SKIPPED = {"Clifton Forge, VA", "South Boston, VA"}  # cities merged into Alleghany (2001) and Halifax (1995) counties
unmatched = [u for u in unmatched if u not in SKIPPED]
print("EPA county rows matched:", len(zone), "| unmatched:", len(unmatched), unmatched[:60])
missing_zone = [k for k in counties if not k.startswith("72") and k not in zone]
print("census counties (ex PR) with no EPA zone:", len(missing_zone), [(k, counties[k]["lsad"], counties[k]["st"]) for k in missing_zone][:20])

# CDC lab data 2008-2017: percent at or above 4 pCi/L = groupById 3; buildings tested
pct = json.load(open("raw/cdc-tracking/labs_pct_pre_mitigation_by_level_county_2008-2017.json", encoding="utf-8-sig"))["tableResult"]
num = json.load(open("raw/cdc-tracking/labs_num_buildings_tested_county_2008-2017.json", encoding="utf-8-sig"))["tableResult"]
p4 = {}; ntest = {}
for row in pct:
    if row["groupById"] == "3" and row["dataValue"] not in ("", None):
        p4[row["geoId"]] = float(row["dataValue"])
for row in num:
    if row["dataValue"] not in ("", None):
        ntest[row["geoId"]] = int(float(row["dataValue"]))
print("CDC counties with pct>=4:", len(p4), "| with test counts:", len(ntest))
dist = collections.Counter("<10" if n < 10 else "<20" if n < 20 else "<50" if n < 50 else ">=50" for n in ntest.values())
print("test-count distribution:", dict(dist))
out = {}
for fips, c in counties.items():
    if fips.startswith("72"): continue
    out[fips] = {"n": c["name"], "l": c["lsad"], "s": c["st"], "z": zone.get(fips), "p": p4.get(fips), "t": ntest.get(fips)}
json.dump(out, open("pipeline/out/us_data.json", "w"), separators=(",", ":"))
print("wrote", len(out), "counties; sample:", out["36061"], out["08031"])
