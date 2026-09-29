# NOAA tide gauge figures — GitHub Pages + Sanctuary Watch Graphic Data

This folder is ready for a **GitHub web-interface upload**. `index.html` accepts a NOAA station ID, shows a station-based title, previews its chart, and generates the exact iframe snippet for the Graphic Data **Code** figure field. `embed.html` is the independent chart with no visible title or descriptive page text. Both files work at any GitHub Pages account/repository path; the home page detects its own hosted URL.

## Upload and test

1. Extract the ZIP. It contains a top-level **`SLR/`** folder. At the root of `Sanctuary_Watch_Figures`, choose **Add file → Upload files** and drag the extracted `SLR` folder into GitHub's upload area. Keep `index.html` beside `embed.html` inside `SLR/`.
2. In **Settings → Pages**, choose **Deploy from a branch**, your branch (usually `main`), and **/(root)**. Save. No scheduled GitHub Actions workflow is included.
3. Open `https://dinnon.github.io/Sanctuary_Watch_Figures/SLR/`. Enter a seven-digit station ID and choose **View station**. The page shows the station title above the chart once NOAA responds. Use **Copy iframe code**, then paste the snippet into Graphic Data's **Code** field and preview that modal.
4. The chart-only URL follows `https://dinnon.github.io/Sanctuary_Watch_Figures/SLR/embed.html?station=9440910`. For another station, change just the seven-digit ID. The home page computes the correct hosted URL automatically.

GitHub Pages remains configured to publish from `main` and `/(root)`; adding the `SLR/` folder does not require setting up Pages again. If you remove the old root `index.html`, the repository's bare Pages URL will need a replacement home page, but `/SLR/` will work on its own. If WordPress strips an iframe from the Code field, that is a WordPress/plugin permission setting to address on that installation, rather than a change to the chart URL.

The [Graphic Data Code figure guide](https://ioos.github.io/sanctuarywatch_graphicdata/figure-types/#code) calls for a valid HTML/JavaScript/iframe snippet. Paste the generated **iframe snippet**, not the complete source of `embed.html`. The Code field displays the hosted chart while the WordPress modal handles its heading, caption, and surrounding content.

## Chart behavior

The chart requests NOAA's monthly mean sea level and published single trend directly in each visitor's browser. The first load starts from a bundled saved dataset for Neah Bay (9443090), Toke Point (9440910), or Seattle (9447130); valid newer live data replaces it. Successful data is also saved in that visitor's browser cache. A small notice appears only when the chart is using saved data. If NOAA fails, a bundled or browser-cached dataset keeps the chart available.

Any seven-digit NOAA ID can be supplied in `?station=ID`, but a new station must have NOAA's **published sea level trend** product to plot. The home page learns its name from NOAA and fills in the figure title and iframe accessibility title. Its first visit needs NOAA to respond. Browser cache is personal to the visitor; a shared fallback for everyone requires adding that station's snapshot to the HTML.

Use the visible **From** and **To** year sliders beneath the plot to focus on a period, or drag horizontally across the plot. **All years** (or double-clicking the plot) resets the view. Hover/tap for monthly values. The plot is in millimeters relative to NOAA's station MSL datum. Relative sea level includes local land movement; a negative trend at a gauge does not imply falling global sea level. Missing months are left missing. The WordPress figure text should provide station context and a link to [NOAA CO-OPS](https://api.tidesandcurrents.noaa.gov/dpapi/prod).

## Add or refresh a shared fallback

From inside the extracted `SLR/` folder, with Python 3.9+:

```bash
python tools/add_station.py 9449880 --label "Friday Harbor, WA"
python tools/build_embed.py
```

The first command fetches NOAA data, validates the station ID and trend product, writes `snapshots/9449880.json`, and updates `stations.json`. The second rebuilds **both** `embed.html` (bundled fallbacks) and `index.html` (home-page station list). Upload the changed HTML, JSON, and station list through GitHub's interface. Rerun the same two commands occasionally if you want the published fallback updated; the browser-direct live series advances without doing so.
