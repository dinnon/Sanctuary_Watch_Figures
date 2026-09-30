#!/usr/bin/env python3
"""Save NOAA full-record trend and official observedSL change products together."""
import argparse
import json
import math
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://api.tidesandcurrents.noaa.gov/dpapi/prod/webapi/product/"
ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site" if (ROOT / "site").exists() else ROOT


def get(product, **params):
    url = BASE + product + ".json?" + urlencode(params)
    with urlopen(Request(url, headers={"User-Agent": "NOAA-Sea-Level-Station-Viewer/2.0"}), timeout=30) as r:
        return json.load(r), url


def finite(value):
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


def validate_monthly(monthly, station, trend_type):
    if (monthly.get("stationID") != station or monthly.get("units") != "meters"
            or monthly.get("datum") != "MSL" or monthly.get("trendType") != trend_type):
        raise ValueError("Unexpected NOAA monthly product, datum, station, or units")
    rows = monthly.get("data", [])
    previous = -1
    for row in rows:
        y, m = row.get("year"), row.get("month")
        if type(y) is not int or type(m) is not int or not 1 <= m <= 12 or y * 12 + m <= previous:
            raise ValueError("Invalid, duplicate, or out-of-order month")
        previous = y * 12 + m
        for key in ("msl", "mslDeseasonalized", "trendLine", "lowerConfidence", "upperConfidence"):
            if key not in row or (row[key] is not None and not finite(row[key])):
                raise ValueError(f"Invalid NOAA value: {key}")
    if not rows or not any(r["msl"] is not None for r in rows):
        raise ValueError("No monthly observations")
    return rows


def observed_snapshot(station, response, monthly, summary_url, monthly_url, retrieved):
    summary = next((s for s in response.get("SeaLvlTrendsObserved", []) if s.get("stationId") == station), None)
    if not summary or summary.get("metadata", {}).get("changeUnits") != "meters":
        raise ValueError("Missing NOAA observedSL summary or unexpected change units")
    change = summary.get("seaLvlChange", {})
    for key in ("changePOR", "changeNTDE", "changeNTDEoffset"):
        if key not in change or (change[key] is not None and not finite(change[key])):
            raise ValueError(f"Invalid NOAA change: {key}")
    for key in ("porStartMidpoint", "porEndMidpoint", "ntdeStartMidpoint", "ntdeEndMidpoint"):
        if key not in change:
            raise ValueError(f"Missing NOAA midpoint: {key}")
        if change[key] is not None:
            datetime.strptime(change[key], "%m/%d/%Y")
    rows = validate_monthly(monthly, station, "NTDE")
    return {"schema_version": 2, "product": "observedSL", "station": station,
            "name": summary["metadata"].get("stationName") or monthly["stationName"],
            "retrieved_utc": retrieved, "latest_month": f'{rows[-1]["year"]:04d}-{rows[-1]["month"]:02d}',
            "source_summary": summary_url, "source_monthly": monthly_url,
            "summary": summary, "monthly": monthly}


def add(station, label=None):
    # Fetch everything before writing. Failure leaves the previous snapshot intact.
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = [pool.submit(get, "sealvltrends", station=station, details="monthlymeans", units="metric", trendType="SINGLE"),
                pool.submit(get, "sealvltrends", station=station),
                pool.submit(get, "observedSL", station=station, units="metric"),
                pool.submit(get, "observedSL", station=station, details="monthlymeans", units="metric", trendType="NTDE")]
        (monthly, monthly_url), (result, trend_url), (observed, observed_url), (obs_monthly, obs_url) = [j.result() for j in jobs]
    retrieved = datetime.now(timezone.utc).isoformat()
    observed_data = observed_snapshot(station, observed, obs_monthly, observed_url, obs_url, retrieved)
    trend = next((t for t in result.get("SeaLvlTrends", []) if t.get("stationId") == station and t.get("trendType") == "SINGLE"), None)
    if not trend or trend.get("trendUnits") != "inches/decade" or not finite(trend.get("trend")):
        raise ValueError("Station lacks the supported full-record SINGLE trend; no files changed")
    for key in ("startDate", "endDate"):
        datetime.strptime(trend[key], "%m/%d/%Y")
    source_rows = validate_monthly(monthly, station, "SINGLE")
    rows = [{"y": r["year"], "m": r["month"], "obs": r["mslDeseasonalized"], "raw": r["msl"],
             "trend": r["trendLine"], "lo": r["lowerConfidence"], "hi": r["upperConfidence"]} for r in source_rows]
    name = label or monthly.get("stationName") or station
    snapshot = {"station": station, "name": name, "retrieved_utc": retrieved,
                "latest_month": f'{rows[-1]["y"]:04d}-{rows[-1]["m"]:02d}',
                "trend_mm_year": trend["trend"] * 2.54, "trend_start": trend["startDate"], "trend_end": trend["endDate"],
                "source_monthly": monthly_url, "source_trend": trend_url, "source_info": monthly.get("info"),
                "trend_summary": trend, "rows": rows, "observed": observed_data}
    dest = SITE / "snapshots" / (station + ".json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    pending = dest.with_suffix(".json.tmp")
    pending.write_text(json.dumps(snapshot, separators=(",", ":"), allow_nan=False) + "\n", encoding="utf-8")
    pending.replace(dest)
    config = SITE / "stations.json"
    stations = json.loads(config.read_text(encoding="utf-8")) if config.exists() else []
    stations = [s for s in stations if s["id"] != station] + [{"id": station, "name": name}]
    stations.sort(key=lambda s: s["name"])
    pending = config.with_suffix(".json.tmp")
    pending.write_text(json.dumps(stations, indent=2) + "\n", encoding="utf-8")
    pending.replace(config)
    c = observed_data["summary"]["seaLvlChange"]
    print(f'{station} {name}: through {snapshot["latest_month"]}; official change (m): NTDE={c["changeNTDE"]}, POR={c["changePOR"]}')


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("station", help="7-digit NOAA CO-OPS station ID")
    p.add_argument("--label", help="Display name (otherwise inferred from NOAA)")
    args = p.parse_args()
    if not args.station.isdigit() or len(args.station) != 7:
        p.error("Station must be a 7-digit NOAA ID")
    add(args.station, args.label)
