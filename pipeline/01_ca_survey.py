"""Extract the 2024 Cross-Canada Survey of Radon census-division table (report
section XVI, PDF pages 65 to 71) into pipeline/out/ca_survey_2024.json.
Values are copied exactly as printed; nothing is re-binned or recomputed
except the share at or above 100 (the two printed bands added together).
Run:  .venv/bin/python -I pipeline/01_ca_survey.py
"""
import json, re, sys, pdfplumber
PDF = "raw/cross-canada-2024/2024-Cross-Canada-Radon-Survey-Report-V24.pdf"
pdf = pdfplumber.open(PDF)
units = []
band_re = re.compile(r"(?:\(?(\d+ in \d+)\)?\s+)?([\d.]+)\s+(< 100|100-200|≥ 200)")
for pn in range(64, 71):
    for table in pdf.pages[pn].extract_tables():
        for row in table:
            if not row or not row[0] or not re.match(r"^\d{4}", row[0].strip()):
                continue
            ids = re.findall(r"\d{4}", row[0])
            name = " ".join((row[1] or "").split())
            prov = " ".join((row[2] or "").split())
            n = int(row[3].replace(",", ""))
            bands = {}
            for ratio, pct, label in band_re.findall(row[4].replace("\n", " ")):
                bands[label] = {"ratio": ratio, "pct": float(pct)}
            if set(bands) != {"< 100", "100-200", "≥ 200"}:
                sys.exit("band parse failed on %s: %r" % (ids, row[4]))
            def num(s):
                s = (s or "").replace(",", "").strip()
                return float(s) if s else None
            units.append({
                "ids": ids, "name": name, "prov": prov, "n": n,
                "p_lt100": bands["< 100"]["pct"], "p_100_200": bands["100-200"]["pct"],
                "p_ge200": bands["≥ 200"]["pct"],
                "r_lt100": bands["< 100"]["ratio"], "r_100_200": bands["100-200"]["ratio"],
                "r_ge200": bands["≥ 200"]["ratio"],
                "gm": num(row[5]), "ci_lo": num(row[6]), "ci_hi": num(row[7]), "max": num(row[8]),
            })
ids_all = [i for u in units for i in u["ids"]]
print("units:", len(units), "| census divisions covered:", len(set(ids_all)), "| duplicates:", len(ids_all) - len(set(ids_all)))
print("clusters:", sum(1 for u in units if len(u["ids"]) > 1), "| total readings:", sum(u["n"] for u in units))
bad = [u for u in units if abs(u["p_lt100"] + u["p_100_200"] + u["p_ge200"] - 100) > 0.3]
print("rows whose three bands do not sum to 100 (+/-0.3):", len(bad), [(u["ids"], u["p_lt100"] + u["p_100_200"] + u["p_ge200"]) for u in bad][:5])
json.dump(units, open("pipeline/out/ca_survey_2024.json", "w"), ensure_ascii=False, indent=0)
print("first:", units[0]); print("last:", units[-1])
