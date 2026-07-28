# Findings

## USGS National Water Use Data
- URL: https://waterdata.usgs.gov/nwis/wu
- Bulk download by state: https://waterdata.usgs.gov/{state_code}/nwis/water_use
- Format: tab-delimited, county-level
- Key category: "Public Supply" (PS) = municipal water systems
- Fields: county FIPS, year, PS freshwater withdrawals (Mgal/d)
- Available years: 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020
- National total PS withdrawals 2020: ~39,000 Mgal/d (needs verification)

## EPA NPDES / ECHO
- API: https://echo.epa.gov/api/
- Facility search: https://echo.epa.gov/api/facility/search
- Bulk data: https://www.epa.gov/echo/download-export-data
- ICIS-NPDES discharge monitoring reports (DMRs)
- Pollutants: Total Nitrogen (00670), Ammonia-N (00608), BOD (00310), TSS (00530)
- Units: lbs/day for loads, MGD for flow

## Per-Capita Constants (literature)
- Domestic water use: 80-100 gal/person/day (EPA, AWWA)
- Wastewater flow: 60-110 gal/person/day (Metcalf & Eddy)
- Total nitrogen: 9-14 g N/person/day (EPA design manuals)
- Ammonia-N: 4-7 g/person/day
- BOD5: 55-90 g/person/day (standard: 60-80)
- TSS: 8-18 g/person/day
