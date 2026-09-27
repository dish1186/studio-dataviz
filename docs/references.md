# References: methods (Dish's data pipeline)

Sources behind the formulas and thresholds used in the data pipeline. Each entry notes where it's used and how it was verified.

## Visibility → light extinction (METAR Step 7)

**Koschmieder, H. (1924).** Theorie der horizontalen Sichtweite. *Beiträge zur Physik der freien Atmosphäre*, 12, 33–55 and 171–181.
- Origin of the relation between visual range and atmospheric light extinction: visual range = ln(1/ε) ÷ b_ext, where ε is the observer's contrast threshold. With ε = 0.02 (2%), ln(50) = 3.912, so **b_ext (km⁻¹) = 3.912 ÷ visual range (km)**.
- Verified: year, volume and pages 33–55 from US EPA HERO, reference 3119984 (https://hero.epa.gov/hero/index.cfm/reference/details/reference_id/3119984). Journal name and the second page range (171–181) from the reference list of *Tellus* 21(5), doi:10.3402/tellusa.v21i5.10112. That list gives the year as 1926 and the author initial as "M."; the volume spans 1924–25, and EPA HERO gives H. Koschmieder, 1924.
- Not read in the original (German, 1924). Cited via the secondary sources above.

**Environment and Climate Change Canada (2014).** *Georgia Basin–Puget Sound Airshed Characterization Report 2014*, Chapter 9 (Visibility). https://www.canada.ca/en/environment-climate-change/services/air-pollution/publications/georgia-basin-puget-sound-report-2014/chapter-9.html
- Uses the same relation in air-quality practice: "VR (km) = 3910 / bext(Mm⁻¹)", i.e. 3.91 ÷ b_ext in km⁻¹. Notes that it "assumes uniform extinction along the path."

**Pitchford, M. L., & Malm, W. C. (1994).** Development and applications of a standard visual index. *Atmospheric Environment*, 28(5), 1049–1054. https://doi.org/10.1016/1352-2310(94)90264-X
- Defines the deciview haze index, dv = 10 × ln(b_ext / 10 Mm⁻¹), used in U.S. regional-haze tracking. Shows that extinction (not visual range) is the quantity that scales with haze. Citation verified from the IMPROVE Data User Guide (Hand, 2023), https://vista.cira.colostate.edu/Improve/wp-content/uploads/2023/10/IMPROVE_Data_User_Guide_24October2023.pdf

## Alternative threshold (noted, not used)

**Meteorological optical range (MOR), WMO convention**: "the length of atmosphere over which a beam of light travels before its luminous flux is reduced to 5% of its original value" (UK Met Office, *How we measure visibility*, https://weather.metoffice.gov.uk/guides/observations/how-we-measure-visibility). The WMO standard itself is the *Guide to Instruments and Methods of Observation* (WMO-No. 8); Claude could not open its visibility chapter to quote it directly.
- With a 5% threshold the constant becomes ln(20) ≈ 3.0 instead of 3.912. This multiplies every extinction value by the same factor (3.0/3.912 ≈ 0.77). Absolute values change; relative patterns, rankings, trends and anomalies do not.

## Not verified
- How ASOS sensors internally convert their measured extinction to the reported visibility (threshold and day/night algorithm). Not checked; should be looked up in the ASOS User's Guide (NOAA/FAA/DoD) before the appendix states anything about it.
