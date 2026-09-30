# NOAA tide gauge figures — GitHub Pages + WordPress

Upload this entire **SLR/** folder to the existing repository. Keep the same
filenames: existing WordPress iframe URLs will continue to work.

## What changed in this revision

- The amount chart now uses NOAA's published **changeNTDE** and **changePOR**
  from the production **observedSL** API. It no longer calculates five-year averages.
- The amount chart retains the original monthly MSL values. Black horizontal
  lines show the epoch/first-five-year baseline and the recent five-year mean.
  Their elevations come from NOAA's published differences and datum offset,
  not a new averaging calculation. See DATA_NOTES.md for limitations.
- Both embeds now show only the chart and controls. Status badges and all footer
  text/links have been removed; fallback loading continues silently.
- An unavailable comparison remains unavailable. Selecting NTDE never silently
  switches to a period-of-record comparison; null never means zero.
- The original trend chart remains NOAA's **full-record SINGLE trend**. Its fitted
  years are retained in snapshots for WordPress captions. It is not the newer since-1992 trend.
- Shared fallbacks for Toke Point, Neah Bay, and Seattle include the published
  amounts, source units, comparison dates, station notes, source URLs, and retrieval
  dates. Old browser caches with inferred comparisons are not reused.
- Both pages remain standalone Canvas/JavaScript HTML: no Highcharts, Plotly,
  external JavaScript, Python server, or WordPress charting plugin is needed.

## Upload and embed

1. Extract the ZIP and upload the contents of **SLR/** into the existing **SLR/**
   folder in GitHub. Replace matching files; do not create SLR/SLR/.
2. Leave Pages configured for your branch and **/(root)**. You do not need to
   reconfigure Pages. No scheduled GitHub Actions workflow is included.
3. Open https://dinnon.github.io/Sanctuary_Watch_Figures/SLR/
4. Enter a seven-digit station ID, choose a chart, and click **View station**.
5. Copy the generated iframe into Sanctuary Watch Graphic Data's **Code** field.

Existing direct URLs:

- Trend: https://dinnon.github.io/Sanctuary_Watch_Figures/SLR/embed.html?station=9440910
- Amount: https://dinnon.github.io/Sanctuary_Watch_Figures/SLR/embed_amount.html?station=9440910

Change the station ID for another location. WordPress supplies the heading;
each embed contains only the chart and controls. Add interpretation and source
attribution in WordPress. The generated iframe remains 650 px tall and can be
resized in your embed code.

## Data and interpretation

| File | NOAA product | What is displayed |
| --- | --- | --- |
| embed.html | sealvltrends, SINGLE | Deseasonalized monthly MSL, published full-record fitted trend and supplied confidence limits |
| embed_amount.html | observedSL | Unadjusted monthly MSL and NOAA's published NTDE/POR amount of change |

The rate and amount are different statistics and may have different signs or
reference periods. Do not compare the full-record rate directly to NOAA's
since-1992 rate as though they were the same product.

All displayed elevations and change amounts are in **feet**; the rate is in
**feet per century**. Original API values remain in their source units.
Monthly observations can extend beyond the averaging period used for NOAA's
published summary. Retrieval dates, monthly coverage, and comparison midpoints remain in the
saved JSON; they are not printed in the embed. See **DATA_NOTES.md** for the scientific details.

Sliders and drag-to-zoom change only the view. They do not recalculate either
statistic. Hover/tap shows monthly values; **All years** resets the chart.
Missing observations are not filled or interpolated.

These are independent visualizations of NOAA data, not NOAA's official charts.

## Live data and fallback behavior

Each visit initially displays the best valid bundled or browser-cached dataset,
then requests current data directly from NOAA. Successful responses are validated
before replacing the saved view. A network error, invalid units, unsupported
response, or older monthly series leaves the valid fallback intact.

The amount summary and monthly series are fetched and cached together. Live
monthly values are never paired with a cached summary. There is no guarantee of
transactional consistency inside NOAA's API, but the application never knowingly
mixes its own snapshots.

No saved/live status or retrieval date is shown in the embed. A new station without
a bundled or previously cached snapshot needs NOAA to respond on its first visit.
If it cannot, the page displays a clear message rather than invented data.

Browser caching belongs to that visitor and may be blocked or cleared. It does
**not** update the repository. Bundled snapshots are the shared fallback available
to first-time visitors during an outage. Refresh those occasionally to keep the
offline copy current.

## Add or refresh a shared fallback

From this SLR folder, with Python 3.9+ (standard library only):

~~~bash
python tools/add_station.py 9449880 --label "Friday Harbor, WA"
python tools/build_embed.py
~~~

To refresh the three included stations:

~~~bash
python tools/add_station.py 9440910
python tools/add_station.py 9443090
python tools/add_station.py 9447130
python tools/build_embed.py
~~~

The script retrieves both products, checks IDs, units, nulls, dates, and monthly
values before writing the station snapshot, then updates stations.json. If NOAA
fails validation, existing snapshots are retained. This shared-snapshot command
currently requires both the full-record SINGLE and observedSL products. The live
amount embed can still display stations lacking a supported full-record trend.

Re-upload the rebuilt HTML files and changed JSON files to GitHub. Keep tools/
and documentation with the project for future maintenance. The HTML files embed
their fallback JSON, so they can also be opened locally without a server.

Optional reproducible checks, with Node.js 18+ and no npm packages:

~~~bash
node tools/test_data.cjs
node tools/test_interactions.cjs
~~~

The second check uses a lightweight simulated DOM/canvas to test interaction
logic. It does not certify browser layout or WordPress rendering; preview both
embeds in your WordPress modal after uploading.

## Sources

- [NOAA Derived Product API](https://api.tidesandcurrents.noaa.gov/dpapi/prod/)
- [NOAA Trends and Extremes](https://tidesandcurrents.noaa.gov/trends-and-extremes/main-product.html)
- [NOAA example notebooks](https://github.com/NOAA-CO-OPS/Coastal_Hazards_Example_Notebooks)
- [Graphic Data Code embed guide](https://ioos.github.io/sanctuarywatch_graphicdata/figure-types/#code)
