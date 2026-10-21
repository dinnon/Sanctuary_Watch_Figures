#!/usr/bin/env python3
"""Export NOAA SLR station snapshots as documented IOOS-style JSON and CSV.

Standard library only. Runs offline from saved snapshots, never queries NOAA.
"""
import csv
import io
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data"
COLUMNS = ("date_yyyy-mm", "station_id", "station_name", "msl_m",
           "msl_deseasonalized_m", "noaa_trend_m", "noaa_ci_lower_m",
           "noaa_ci_upper_m", "display_trend_m", "display_ci_lower_m",
           "display_ci_upper_m")
MEASUREMENTS = COLUMNS[3:]


def month_index(mmddyyyy):
    return int(mmddyyyy[6:10]) * 12 + int(mmddyyyy[:2]) - 1


def rows_for(snapshot):
    station = snapshot["station"]
    start, end = month_index(snapshot["trend_start"]), month_index(snapshot["trend_end"])
    if start > end:
        raise ValueError("Trend dates are reversed: " + station)
    dates = set()
    output = []
    for src in snapshot["rows"]:
        year, month = src["y"], src["m"]
        if not isinstance(year, int) or not isinstance(month, int) or not 1 <= month <= 12:
            raise ValueError("Invalid calendar month: " + station)
        date = f"{year:04d}-{month:02d}"
        if date in dates:
            raise ValueError("Duplicate month: " + station + " " + date)
        dates.add(date)
        for key in ("obs", "raw", "trend", "lo", "hi"):
            value = src[key]
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))):
                raise ValueError("Invalid measurement: " + key)
        supported = start <= year * 12 + month - 1 <= end
        if src["lo"] is not None and src["hi"] is not None and src["lo"] > src["hi"]:
            raise ValueError("Reversed confidence interval: " + station + " " + date)
        output.append({
            "date_yyyy-mm": date,
            "station_id": station,
            "station_name": snapshot["name"],
            "msl_m": src["raw"],
            "msl_deseasonalized_m": src["obs"],
            "noaa_trend_m": src["trend"],
            "noaa_ci_lower_m": src["lo"],
            "noaa_ci_upper_m": src["hi"],
            "display_trend_m": src["trend"] if supported else None,
            "display_ci_lower_m": src["lo"] if supported else None,
            "display_ci_upper_m": src["hi"] if supported else None,
        })
    if not output or output != sorted(output, key=lambda r: r["date_yyyy-mm"]):
        raise ValueError("Missing or out-of-order monthly data: " + station)
    return output


def metadata(snapshot):
    summary = snapshot["trend_summary"]
    if (summary["startDate"] != snapshot["trend_start"] or
        summary["endDate"] != snapshot["trend_end"] or
        summary["stationId"] != snapshot["station"] or
        summary["trendType"] != "SINGLE"):
        raise ValueError("Trend metadata does not match snapshot")
    return {
        "Dataset": "NOAA CO-OPS Relative Sea Level — SINGLE trend",
        "Station ID": snapshot["station"],
        "Station Name": snapshot["name"],
        "Source Agency": "NOAA Center for Operational Oceanographic Products and Services",
        "Source Product": "sealvltrends (SINGLE), monthlymeans",
        "Source Monthly URL": snapshot["source_monthly"],
        "Source Trend URL": snapshot["source_trend"],
        "Source Retrieved UTC": snapshot["retrieved_utc"],
        "Latest Source Month": snapshot["latest_month"],
        "Trend Start Date": snapshot["trend_start"],
        "Trend End Date": snapshot["trend_end"],
        "Trend Rate (mm/year)": snapshot["trend_mm_year"],
        "Trend Rate Source Units": summary["trendUnits"],
        "Observation Datum": "MSL",
        "Elevation Units": "meters",
        "Confidence": "NOAA-provided lower/upper confidence limits; confidence level not reassigned",
        "Data Policy": "noaa_* fields preserve NOAA-provided values; display_* fields are null outside NOAA trend dates",
        "Missing Value": "null in JSON, empty CSV cell; no interpolation",
        "Snapshot Provenance": f"SLR/snapshots/{snapshot['station']}.json",
        "Schema": "Sanctuary Watch SLR export v1, metadata/data column arrays",
    }


def export_json(meta, rows):
    return json.dumps({"metadata": meta, "data": {
        col: [row[col] for row in rows] for col in COLUMNS
    }}, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


def export_csv(meta, rows):
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    for key, value in meta.items():
        writer.writerow([key + ":", str(value)])
    writer.writerow([])
    writer.writerow(COLUMNS)
    for row in rows:
        writer.writerow([row[c] if row[c] is not None else "" for c in COLUMNS])
    return out.getvalue()


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(content, encoding="utf-8", newline="")
    temp.replace(path)


def main():
    snapshots = sorted((ROOT / "snapshots").glob("*.json"))
    if not snapshots:
        raise SystemExit("No snapshot JSON files; run tools/add_station.py first")
    all_rows = []
    manifest = []
    for path in snapshots:
        snapshot = json.loads(path.read_text(encoding="utf-8"))
        station = path.stem
        if not re.fullmatch(r"\d{7}", station) or snapshot["station"] != station:
            raise ValueError("Snapshot filename/station mismatch: " + str(path))
        rows = rows_for(snapshot)
        meta = metadata(snapshot)
        write(OUT / f"{station}.json", export_json(meta, rows))
        write(OUT / f"{station}.csv", export_csv(meta, rows))
        all_rows.extend(rows)
        manifest.append({"station_id": station, "station_name": snapshot["name"],
                         "first_month": rows[0]["date_yyyy-mm"], "latest_month": rows[-1]["date_yyyy-mm"],
                         "rows": len(rows), "trend_start": snapshot["trend_start"],
                         "trend_end": snapshot["trend_end"], "source_retrieved_utc": snapshot["retrieved_utc"]})
    all_rows.sort(key=lambda r: (r["station_id"], r["date_yyyy-mm"]))
    combined_meta = {
        "Dataset": "NOAA CO-OPS Relative Sea Level — combined Sanctuary Watch stations",
        "Source Agency": "NOAA CO-OPS",
        "Elevation Units": "meters",
        "Observation Datum": "MSL",
        "Data Policy": "noaa_* source values preserved; display_* null outside station-specific analysis dates",
        "Station Count": len(manifest),
        "Schema": "Sanctuary Watch SLR export v1",
    }
    write(OUT / "all_stations.csv", export_csv(combined_meta, all_rows))
    write(OUT / "manifest.json", json.dumps({
        "schema_version": 1, "metadata": combined_meta, "stations": manifest,
    }, indent=2, ensure_ascii=False) + "\n")
    print(f"Exported {len(manifest)} stations / {len(all_rows)} monthly rows to {OUT}")


if __name__ == "__main__":
    main()
