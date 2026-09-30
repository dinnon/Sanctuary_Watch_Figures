# Scientific and data-handling decisions

## Amount of change: use published numbers, not reconstructed averages

Source: NOAA production Derived Product API, `observedSL.json`, `units=metric`.
The exact source URLs and full station summary/monthly payloads are retained in
each snapshot's `observed` object. The original `seaLvlChange` fields are preserved.

- `changeNTDE`: NOAA's published change from the 1983–2001 NTDE reference to its
  latest five-year average.
- `changePOR`: NOAA's published change from the first five-year average to its
  latest five-year average.
- `changeNTDEoffset`: retained for provenance. We neither apply this offset a
  second time to the published change nor apply it to the displayed monthly line.
- The monthly line is the API's `msl`, in meters relative to the station MSL datum,
  converted to feet. It is not deseasonalized or independently datum-adjusted.
- Black horizontal levels are derived algebraically from published values:
  recent station-datum level = changeNTDE + changeNTDEoffset;
  NTDE baseline level = changeNTDEoffset;
  POR baseline level = recent station-datum level - changePOR.
  These recover elevations at the precision of NOAA's rounded published values.
- In NTDE mode the baseline bar spans 1983 through 2001 (1983 to 2002 on the
  continuous time axis). Five-year bars extend 30 months to either side of the
  calendar month of NOAA's published midpoint. Their spans are month-based
  display windows inferred from those midpoints, not newly selected sample windows.
- When NTDE change/offset is missing, or POR/NTDE recent midpoints disagree,
  absolute horizontal levels cannot be recovered this way. The bars are omitted;
  any available published change and monthly observations are still displayed.
  A missing offset is never assumed to be zero.

NOAA's published amount already reflects its own completeness and datum rules.
Our old first/last-five-year averaging calculation remains removed. The restored
horizontal bars use only the algebraic relationships above. Neither changes in zoom nor additional months
in the monthly feed cause us to recompute a different amount.

If NOAA supplies null, the comparison is unavailable. Null is never zero. NTDE
and POR are independent options: no silent baseline substitution. Station names
and annotations are rendered as text, never interpreted as HTML. NOAA annotations and event metadata remain in snapshots for WordPress captioning;
the embed no longer prints notes or source links.

## Full-record rate: keep the product and time span explicit

The original trend chart uses `sealvltrends.json`, `trendType=SINGLE`.
Monthly data use metric units. The summary response supplies inches/decade;
the exact conversion is inches/decade × 2.54 = mm/year, then × 100 / 304.8 =
feet/century. Equivalently, inches/decade × 10 / 12 = feet/century.
The source trend summary is preserved alongside the transformed plotting rows.

The chart uses NOAA's `mslDeseasonalized`, `trendLine`, `lowerConfidence`, and
`upperConfidence`. No local regression is fitted. The source's start and end
years are retained in the snapshot for WordPress captions. This full-record trend is not the `observedSL` NTDE trend
starting around 1992, and the two may differ substantially. The source URL is retained in the snapshot; there is no link below the embed.

We label the band as NOAA-supplied confidence limits, without borrowing a
confidence percentage from another product. NOAA's newer page text and API
documentation have used differing confidence-level labels; product-specific
metadata is retained rather than assuming all products use the same percentage.

## Units, precision, and time

- Feet = source meters / 0.3048 (exact definition).
- Change labels and hover values on the amount chart use three decimal places
  in feet. This is display rounding, not added measurement accuracy.
- Signs are retained, including falling local relative sea level. A negative
  local value does not imply falling global sea level.
- Original numeric precision is preserved in snapshots; nulls remain nulls.
- Monthly dates denote monthly averages, not instantaneous measurements.
- Retrieval date, last monthly record, and comparison dates are different
  concepts and are retained separately in the snapshot. A recent download is not proof that
  NOAA has updated the underlying statistical summary.

## Cache and provenance safeguards

Amount cache: `noaa-observed-sl-v2-STATION`.
Trend cache: `noaa-sealvltrends-single-v2-STATION`.
Old inferred-comparison caches are intentionally excluded.

Validation rejects mismatched stations, unexpected units/products, invalid
numeric values, malformed dates, duplicate months, and missing required fields.
For the amount chart, the summary and monthly payload are stored as one unit.
When saved copies have the same latest month, the more recently retrieved valid
copy wins, allowing NOAA corrections to supersede older copies. A shorter live
monthly series does not silently replace a longer saved series; the valid saved copy remains in use silently.

Changing a station ID can fetch a new live chart, but creating a shared offline
fallback still requires refreshing/building/uploading that station's snapshot.
Nothing in the browser writes to GitHub.

## Verification reference for this release

These are the published metric values captured for this revision, not values
calculated from monthly readings:

| Station | NTDE change (m) | POR change (m) | NTDE change (ft, displayed) | POR change (ft, displayed) |
| --- | ---: | ---: | ---: | ---: |
| Toke Point 9440910 | 0.008 | 0.059 | +0.026 | +0.194 |
| Neah Bay 9443090 | -0.047 | -0.113 | -0.154 | -0.371 |
| Seattle 9447130 | 0.077 | 0.255 | +0.253 | +0.837 |

The captured monthly feeds extend through July 2026. The published recent
comparison midpoint is July 2023; it does not move to July 2026 merely because
newer individual months exist. Read each snapshot's `retrieved_utc` for its exact
download timestamp. Live NOAA values can change after this release.

`node tools/test_data.cjs` checks official-value preservation, unit conversion,
null/zero behavior, invalid inputs, cache versioning, and generated HTML syntax.
`node tools/test_interactions.cjs` checks interaction logic, response validation,
and offline/cache behavior in a simulated DOM/canvas at two widths. Real-browser
visual validation could not be completed in the build environment because its
browser installation failed. A final GitHub Pages/WordPress visual check remains.

Sources: [NOAA API documentation](https://api.tidesandcurrents.noaa.gov/dpapi/prod/),
[NOAA product guidance](https://tidesandcurrents.noaa.gov/trends-and-extremes/main-product.html),
and [NOAA example notebooks](https://github.com/NOAA-CO-OPS/Coastal_Hazards_Example_Notebooks).

## Figure-only presentation

No status badge, footer, metadata paragraph, or source link is rendered beneath
 either embed. Fallback behavior is unchanged and silent. An in-chart error is
shown only when there is no usable dataset; an unavailable comparison is still
identified rather than represented as zero. Interpretation and source attribution
belong in WordPress. The complete provenance remains in the JSON and these docs.
