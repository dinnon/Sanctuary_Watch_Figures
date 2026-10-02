# NOAA direct-embed test and code builder

1. Extract the ZIP. Upload the entire `NOAA-Embed-Test` folder to the root of
   `Sanctuary_Watch_Figures`, alongside your existing `SLR` folder.
2. After GitHub Pages finishes updating, open:
   https://dinnon.github.io/Sanctuary_Watch_Figures/NOAA-Embed-Test/
3. Enter a seven-digit station ID and select **Preview & generate code**.
4. Preview both NOAA frames. Adjust their height if needed.
5. Copy the rate or amount iframe code for your WordPress administrator to paste
   into the Graphic Data Code field (or another iframe-capable HTML field).

Default: Neah Bay 9443090. Also try Toke Point 9440910 and Seattle 9447130.
You can share a selected station using the preview link, for example:
https://dinnon.github.io/Sanctuary_Watch_Figures/NOAA-Embed-Test/?station=9440910

Changing station IDs generates different URLs and iframe code; it does not
create or save new station files. The generated iframe points directly to NOAA,
so the WordPress embed does not depend on this test folder after you copy it.

This is one standalone HTML file, with no libraries, API keys, or build steps.
It embeds NOAA's application with plot-selection URL parameters. It does not
strip NOAA's navigation, guarantee a chart-only view, or cache the NOAA charts.
Successful embedding still needs a hosted browser test. This page cannot inspect
the cross-origin frame to certify that NOAA rendered successfully. A working
GitHub Pages preview does not establish that WordPress permits the same iframe.

If a frame is blank or blocked, open its NOAA link directly and inspect the
browser console for embedding-policy errors. The original custom SLR figures
and their cached fallbacks are separate and are not changed by this folder.
