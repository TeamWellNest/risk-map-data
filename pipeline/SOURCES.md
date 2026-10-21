# Raw downloads expected in raw/ (not committed)

| Folder | File | From |
|---|---|---|
| raw/epa-zones/ | radon-zones-202406.json | https://www.epa.gov/system/files/other-files/2024-06/radon-zones-202406.json |
| raw/cdc-tracking/ | labs_pct_pre_mitigation_by_level_county_2008-2017.json, labs_num_buildings_tested_county_2008-2017.json | https://ephtracking.cdc.gov/apigateway/api/v1 (indicator 144, measures 868 and 864, county, 2017 window) |
| raw/census/ | cb_2021_us_county_20m.zip | https://www2.census.gov/geo/tiger/GENZ2021/shp/cb_2021_us_county_20m.zip |
| raw/zcta-county/ | tab20_zcta520_county20_natl.txt | https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/tab20_zcta520_county20_natl.txt |
| raw/statcan/ | lcd_000b21s_e_cartographic_wgs84_generalized0.002deg.geojson, lfsa000b21s_e_cartographic_wgs84_generalized0.0005deg.geojson | https://geo.statcan.gc.ca/geo_wa/rest/services/2021/Cartographic_boundary_files/MapServer (layers 4 and 14, outSR 4326) |
| raw/cross-canada-2024/ | 2024-Cross-Canada-Radon-Survey-Report-V24.pdf | https://evictradon.org/wp-content/uploads/2025/11/2024-Cross-Canada-Radon-Survey-Report-V24.pdf |

Python 3.9+, virtual environment with: pyshp, shapely, pdfplumber.
Run the scripts in order 01 to 05 with `.venv/bin/python -I`.
