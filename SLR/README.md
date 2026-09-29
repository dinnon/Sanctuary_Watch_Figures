# NOAA tide gauge figures — GitHub Pages + Sanctuary Watch Graphic Data

This folder is ready for a **GitHub web-interface upload**. `index.html` accepts a NOAA station ID, shows a station-based title, previews either chart, and generates the exact iframe snippet for the Graphic Data **Code** figure field. The two independent embeds are:

| File | Figure |
| --- | --- |
| `embed.html` | Relative sea level: deseasonalized monthly values, NOAA's trend line, and its confidence band. |
| `embed_amount.html` | Observed amount of change: monthly mean sea level, the baseline, the most recent five-year average, and their difference. |

Both embeds have no separate page header or descriptive text. All three HTML files work at any GitHub Pages account/repository path; the home page detects its own hosted URL.

## Upload and test

1. Extract the ZIP. It contains a top-level **`SLR/`** folder. At the root of `Sanctuary_Watch_Figures`, choose **Add file → Upload files** and drag the extracted `SLR` folder into GitHub's upload area. Keep `index.html`, `embed.html`, and `embed_amount.html` together inside `SLR/`.
2. In **Settings → Pages**, choose **Deploy from a branch**, your branch (usually `main`), and **/(root)**. Save. No scheduled GitHub Actions workflow is included.
3. Open `https://dinnon.github.io/Sanctuary_Watch_Figures/SLR/`. Enter a seven-digit station ID, select a figure type (the original relative sea level plot appears first), and choose **View station**. The page shows the station title above the chart once NOAA responds. Use **Copy iframe code**, then paste the snippet into Graphic Data's **Code** field and preview that modal.
4. The amount chart URL follows `https://dinnon.github.io/Sanctuary_Watch_Figures/SLR/embed_amount.html?station=9443090`; the original trend chart uses `embed.html` instead. For another station, change just the seven-digit ID. The home page computes the correct hosted URL automatically.

GitHub Pages remains configured to publish from `main` and `/(root)`; adding the `SLR/` folder does not require setting up Pages again. If you remove the old root `index.html`, the repository's bare Pages URL will need a replacement home page, but `/SLR/` will work on its own. If WordPress strips an iframe from the Code field, that is a WordPress/plugin permission setting to address on that installation, rather than a change to the chart URL.

The [Graphic Data Code figure guide](https://ioos.github.io/sanctuarywatch_graphicdata/figure-types/#code) calls for a valid HTML/JavaScript/iframe snippet. Paste the generated **iframe snippet**, not the complete source of either embed page. The Code field displays the hosted chart while the WordPress modal handles its heading, caption, and surrounding content.

## Chart behavior

The chart requests NOAA's monthly mean sea level and published single trend directly in each visitor's browser. The first load starts from a bundled saved dataset for Neah Bay (9443090), Toke Point (9440910), or Seattle (9447130); valid newer live data replaces it. Successful data is also saved in that visitor's browser cache. A small notice appears only when the chart is using saved data. If NOAA fails, a bundled or browser-cached dataset keeps the chart available.

The **amount of change** view follows the visual structure of NOAA's [station amount plot](https://tidesandcurrents.noaa.gov/trends-and-extremes/main-product.html?mapTab=station&tab=trends&station-id=9443090&plot=relative-sea-level-change): monthly MSL, the 1983–2001 station MSL baseline at zero, the most recent five complete calendar years' mean, and their difference. **First five years** uses that station's first five complete years as a baseline; this is also the fallback if the NTDE period is unavailable. The red difference is observed historical change, not a projection. This independent implementation uses NOAA data but is not NOAA's official chart. It works without Highcharts or a charting CDN and retains the bundled and browser-cache fallbacks.

Both plots currently use **HTML Canvas and plain JavaScript**, drawn in the visitor's browser. They do not use Highcharts or Plotly. Plotly.js is MIT-licensed and can be self-hosted if the team prefers its built-in chart interactions later; changing the renderer would not require changing the NOAA data and fallback workflow.

Any seven-digit NOAA ID can be supplied in `?station=ID`, but a new station must have NOAA's **published sea level trend** product to plot. The home page learns its name from NOAA and fills in the figure title and iframe accessibility title. Its first visit needs NOAA to respond. Browser cache is personal to the visitor; a shared fallback for everyone requires adding that station's snapshot to the HTML.

Use the visible **From** and **To** year sliders beneath the plot to focus on a period, or drag horizontally across the plot. **All years** (or double-clicking the plot) resets the view. Hover/tap for monthly values. The plot is in millimeters relative to NOAA's station MSL datum. Relative sea level includes local land movement; a negative trend at a gauge does not imply falling global sea level. Missing months are left missing. The WordPress figure text should provide station context and a link to [NOAA CO-OPS](https://api.tidesandcurrents.noaa.gov/dpapi/prod).

## Add or refresh a shared fallback

From inside the extracted `SLR/` folder, with Python 3.9+:

```bash
python tools/add_station.py 9449880 --label "Friday Harbor, WA"
python tools/build_embed.py
```

The first command fetches NOAA data, validates the station ID and trend product, writes `snapshots/9449880.json`, and updates `stations.json`. The second rebuilds `embed.html`, `embed_amount.html` (both with bundled fallbacks), and `index.html` (home-page station names). Upload the changed HTML, JSON, and station list through GitHub's interface. Rerun the same two commands occasionally if you want the published fallback updated; the browser-direct live series advances without doing so.
