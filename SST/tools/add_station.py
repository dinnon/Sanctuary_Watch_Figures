#!/usr/bin/env python3
"""Save/refresh a NOAA trend station and register it in the static site."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://api.tidesandcurrents.noaa.gov/dpapi/prod/webapi/product/sealvltrends.json"
ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site" if (ROOT / "site").exists() else ROOT


def get(**params):
    url = BASE + "?" + urlencode(params)
    with urlopen(Request(url, headers={"User-Agent": "NOAA-Sea-Level-Station-Viewer/1.0"}), timeout=60) as r:
        return json.load(r), url


def add(station, label=None):
    monthly, monthly_url = get(station=station, details="monthlymeans", units="metric", trendType="SINGLE")
    result, trend_url = get(station=station)
    trend = next((t for t in result.get("SeaLvlTrends", []) if t.get("stationId") == station), None)
    if not trend or monthly.get("stationID") != station or monthly.get("units") != "meters" or monthly.get("trendType") != "SINGLE":
        raise ValueError("Station lacks the expected NOAA sea level trends product")
    if trend.get("trendUnits") != "inches/decade" or not isinstance(trend.get("trend"), (float, int)):
        raise ValueError("Unexpected NOAA trend units or value")
    data = monthly.get("data", [])
    if not data:
        raise ValueError("Station has no monthly means")
    rows = []
    for r in data:
        if not isinstance(r.get("year"), int) or not isinstance(r.get("month"), int) or not 1 <= r["month"] <= 12:
            raise ValueError("Invalid month")
        rows.append({"y": r["year"], "m": r["month"], "obs": r.get("mslDeseasonalized"),
                     "raw": r.get("msl"), "trend": r.get("trendLine"),
                     "lo": r.get("lowerConfidence"), "hi": r.get("upperConfidence")})
    rows.sort(key=lambda r: (r["y"], r["m"]))
    if len({(r["y"], r["m"]) for r in rows}) != len(rows):
        raise ValueError("Duplicate months")
    name = label or f'{monthly.get("stationName", trend.get("stationName", station))}, WA'
    snapshot = {"station": station, "name": name, "retrieved_utc": datetime.now(timezone.utc).isoformat(),
                "latest_month": f'{rows[-1]["y"]:04d}-{rows[-1]["m"]:02d}',
                "trend_mm_year": round(trend["trend"] * 2.54, 3), "trend_end": trend["endDate"],
                "source_monthly": monthly_url, "source_trend": trend_url, "rows": rows}
    dest = SITE / "snapshots" / (station + ".json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(snapshot, separators=(",", ":")) + "\n", encoding="utf-8")
    config = SITE / "stations.json"
    stations = json.loads(config.read_text(encoding="utf-8")) if config.exists() else []
    stations = [s for s in stations if s["id"] != station] + [{"id": station, "name": name}]
    stations.sort(key=lambda s: s["name"])
    config.write_text(json.dumps(stations, indent=2) + "\n", encoding="utf-8")
    print(f'{station} {name}: {len(rows)} months through {snapshot["latest_month"]}, trend {snapshot["trend_mm_year"]:+.3f} mm/year')


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("station", help="7-digit NOAA CO-OPS station ID")
    p.add_argument("--label", help="Display name (otherwise inferred from NOAA)")
    args = p.parse_args()
    if not args.station.isdigit() or len(args.station) != 7:
        p.error("Station must be a 7-digit NOAA ID")
    add(args.station, args.label)
