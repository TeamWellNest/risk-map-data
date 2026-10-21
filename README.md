# WellNest Radon Risk Map: data

Open public data prepared for the interactive radon risk map at
https://wellnesthq.com/risk-map (United States and Canada, lookup by ZIP code
and Canadian postal code). Built and maintained by WellNestHQ Inc.

## Files

| File | What it is |
|---|---|
| `data/riskmap.v1.json` | Projected SVG paths for every U.S. county and Canadian census division, state and province outlines, each area's published radon figures, the FSA to census division table, and metadata (tiers, credits). |
| `data/lookup.v1.json` | ZIP (ZCTA) to county FIPS, by largest land-area overlap. |
| `pipeline/` | The Python scripts that build both files from the raw downloads (`raw/`, not committed; download links in `pipeline/SOURCES.md`). |

Served to the page through jsDelivr, pinned to a commit.

## Sources and credits

- **U.S. measured results:** CDC National Environmental Public Health Tracking Network, Radon Tests from Labs, share of pre-mitigation tests at or above 4 pCi/L by county, 2008 to 2017 window. https://www.cdc.gov/environmental-health-tracking/php/data-research/radon-testing.html
- **U.S. zones:** U.S. Environmental Protection Agency, Map of Radon Zones (1993; county table republished June 2024). Public domain. https://www.epa.gov/radon/epa-map-radon-zones-0
- **U.S. boundaries and ZIP codes:** U.S. Census Bureau, Cartographic Boundary Files 2021 (counties, 1:20,000,000) and the 2020 ZCTA to County Relationship File. Public domain.
- **Canada measured results:** Cross-Canada Survey of Radon working group: a collaboration between the Evict Radon National Study, BC Centre for Disease Control and Health Canada. Cross-Canada Survey of Radon Exposure in the Residential Buildings of Urban and Rural Communities. Canada. Cross Canada Radon Survey. 2024. Version 1.1. Available at: www.crosscanadaradon.ca. Figures reproduced as published in the Section XVI census division tables.
- **Canada boundaries and postal codes:** Adapted from Statistics Canada, 2021 Census Boundary Files (census divisions and forward sortation areas), 2021. This does not constitute an endorsement by Statistics Canada of this product. Contains information licensed under the Open Government Licence - Canada.

## License

The pipeline code and the map's own design (projection, simplification,
tiers, file layout) are released under the MIT License (see `LICENSE`).
The underlying statistics remain the work of their producers listed above and
are reused under their own terms; please credit them, not us, for the numbers.
