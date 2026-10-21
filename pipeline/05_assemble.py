"""Assemble the published files:
  data/riskmap.v1.json  map paths + area values + FSA table + metadata
  data/lookup.v1.json   ZIP (ZCTA) -> county FIPS
  pipeline/out/summary.json  ranked lists and national figures for the page copy
Run:  .venv/bin/python -I pipeline/05_assemble.py
"""
import json, datetime, collections
geom = json.load(open("pipeline/out/geom.json"))
us = json.load(open("pipeline/out/us_data.json"))
units = json.load(open("pipeline/out/ca_survey_2024.json"))
fsa_cd = json.load(open("pipeline/out/fsa_cd.json"))
zip_county = json.load(open("pipeline/out/zip_county.json"))
cds = json.load(open("raw/statcan/lcd_000b21s_e_cartographic_wgs84_generalized0.002deg.geojson"))["features"]
PR = {"10":"NL","11":"PE","12":"NS","13":"NB","24":"QC","35":"ON","46":"MB","47":"SK","48":"AB","59":"BC","60":"YT","61":"NT","62":"NU"}
CDTYPE = {"CDR":"Census Division","CT":"County","CTY":"County","DIS":"District","DM":"District Municipality","MRC":"Regional County Municipality","RD":"Regional District","REG":"Region","RM":"Regional Municipality","TÉ":"Territoire équivalent","TE":"Territoire équivalent","UC":"United Counties","MU":"Municipality","CDR ":"Census Division","TER":"Territory"}
MIN_TESTS = 20   # US counties with fewer lab tests than this show the EPA zone (hatched), not the measured share
by_cd = {}
for u in units:
    for cid in u["ids"]: by_cd[cid] = u
ca = {}
for c in cds:
    p = c["properties"]; cid = p["CDUID"]
    name = " ".join(p["CDNAME"].split())
    rec = {"n": name, "t": CDTYPE.get(p["CDTYPE"], p["CDTYPE"]), "s": PR[p["PRUID"]], "d": geom["ca"][cid]}
    u = by_cd.get(cid)
    if u:
        rec.update({"p": u["p_ge200"], "p100": round(u["p_100_200"] + u["p_ge200"], 1), "gm": u["gm"], "r": u["r_ge200"],
                    "r100": None, "x": u["n"], "mx": u["max"]})
        if len(u["ids"]) > 1: rec["cl"] = u["name"]; rec["cln"] = len(u["ids"])
    ca[cid] = rec
us_out = {}
for fips, c in us.items():
    rec = {"n": c["n"], "l": c["l"], "s": c["s"], "z": c["z"], "d": geom["us"][fips]}
    if c["p"] is not None and c["t"] is not None:
        rec["p"] = c["p"]; rec["x"] = c["t"]
    us_out[fips] = rec
meta = {
  "v": 1, "built": datetime.date.today().isoformat(),
  "tiers": [[0, 10, "Lower"], [10, 20, "Moderate"], [20, 35, "Elevated"], [35, 50, "High"], [50, 101, "Very high"]],
  "min_tests": MIN_TESTS,
  "sources": {
    "us_measured": "CDC National Environmental Public Health Tracking Network, Radon Tests from Labs, share of pre-mitigation tests at or above 4 pCi/L by county, 2008 to 2017 window, accessed Oct 2026",
    "us_zone": "US EPA, Map of Radon Zones (1993; county table republished June 2024), public domain",
    "us_boundaries": "US Census Bureau, Cartographic Boundary Files 2021 (counties, 1:20,000,000), public domain",
    "us_zip": "US Census Bureau, 2020 ZCTA to County Relationship File, public domain",
    "ca_measured": "Cross-Canada Survey of Radon working group (Evict Radon National Study, BC Centre for Disease Control, Health Canada). Cross-Canada Survey of Radon Exposure in the Residential Buildings of Urban and Rural Communities, 2024, Version 1.1, Section XVI tables, www.crosscanadaradon.ca",
    "ca_boundaries": "Adapted from Statistics Canada, 2021 Census Boundary Files (census divisions, forward sortation areas), 2021. This does not constitute an endorsement by Statistics Canada of this product. Contains information licensed under the Open Government Licence - Canada."
  }
}
out = {"meta": meta, "vb": geom["vb"], "hi_box": geom["hi_box"], "us_states": geom["us_states"], "ca_prov": geom["ca_prov"], "us": us_out, "ca": ca, "fsa": fsa_cd}
json.dump(out, open("data/riskmap.v1.json", "w"), separators=(",", ":"), ensure_ascii=False)
json.dump({"meta": {"v": 1, "built": meta["built"], "source": meta["sources"]["us_zip"]}, "zip": zip_county}, open("data/lookup.v1.json", "w"), separators=(",", ":"))
import os
print("riskmap.v1.json", round(os.path.getsize("data/riskmap.v1.json")/1e6, 2), "MB | lookup.v1.json", round(os.path.getsize("data/lookup.v1.json")/1e6, 2), "MB")
# ---- summary for the page copy ----
def tier(p):
    for lo, hi, name in meta["tiers"]:
        if lo <= p < hi: return name
# US: states ranked by share of tests >= 4 pCi/L (test-weighted across counties with data)
st = collections.defaultdict(lambda: [0.0, 0])
for fips, c in us.items():
    if c["p"] is not None and c["t"]:
        st[c["s"]][0] += c["p"] * c["t"]; st[c["s"]][1] += c["t"]
us_states = sorted(((round(v[0] / v[1], 1), v[1], s) for s, v in st.items() if v[1] >= 200), reverse=True)
measured = [c for c in us.values() if c["p"] is not None and (c["t"] or 0) >= MIN_TESTS]
us_counties = sorted(((c["p"], c["t"], c["l"] + ", " + c["s"]) for c in measured if c["t"] >= 100), reverse=True)
ca_units = sorted(((u["p_ge200"], u["n"], u["name"] + " (" + u["prov"] + ")") for u in units), reverse=True)
nat_us = sum(c["p"] * c["t"] for c in us.values() if c["p"] is not None and c["t"]) / sum(c["t"] for c in us.values() if c["p"] is not None and c["t"])
summary = {
  "us_states_top": us_states[:12], "us_states_bottom": us_states[-5:], "us_counties_top": us_counties[:12],
  "us_tests_total": sum(c["t"] for c in us.values() if c["t"]), "us_counties_measured": len(measured),
  "us_counties_total": len(us), "us_share_weighted": round(nat_us, 1),
  "us_tier_counts": collections.Counter(tier(c["p"]) for c in measured),
  "ca_units_top": ca_units[:12], "ca_units_bottom": ca_units[-5:], "ca_cd_covered": len(by_cd), "ca_cd_total": len(ca),
  "ca_readings": sum(u["n"] for u in units), "ca_tier_counts": collections.Counter(tier(u["p_ge200"]) for u in units),
}
json.dump(summary, open("pipeline/out/summary.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps(summary, indent=1, ensure_ascii=False)[:3500])
