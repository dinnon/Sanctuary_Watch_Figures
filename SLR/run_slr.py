#!/usr/bin/env python3
"""Sanctuary Watch SLR: single IDE entry point.

Open this file and click Run in VS Code, Spyder, or PyCharm.
Only edit the settings in the next section.
"""
from __future__ import annotations

# ---------------------- USER SETTINGS ----------------------
REFRESH_NOAA = True        # True = request latest NOAA data; False = offline rebuild
RUN_TESTS = True           # Execute existing Node tests if Node.js is installed
STOP_ON_TEST_FAILURE = False  # Tests report a failure without discarding completed exports
FAIL_ON_STATION_ERROR = False  # True = abort if any station cannot refresh
# Gallery station IDs are the authoritative set; edit gallery.html to add stations.
# -----------------------------------------------------------

import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TOOLS = ROOT / "tools"
GALLERY = ROOT / "gallery.html"
STATIONS = ROOT / "stations.json"
SNAPSHOTS = ROOT / "snapshots"
REPORT = ROOT / "data" / "run_report.json"


def gallery_stations():
    html = GALLERY.read_text(encoding="utf-8")
    ids = re.findall(r'<article\s+class="card"\s+data-station="(\d{7})"', html)
    if not ids or len(ids) != len(set(ids)):
        raise RuntimeError("Gallery contains zero or duplicate station IDs")
    return ids


def execute(script, *args):
    subprocess.run([sys.executable, str(TOOLS / script), *args], cwd=ROOT, check=True)


def main():
    ids = gallery_stations()
    SNAPSHOTS.mkdir(parents=True, exist_ok=True)
    refreshed, failures = [], {}
    print(f"\nSanctuary Watch SLR — {len(ids)} gallery stations")
    print("Mode:", "Refresh NOAA + rebuild" if REFRESH_NOAA else "Offline rebuild")
    for index, station in enumerate(ids, 1):
        print(f"\n[{index}/{len(ids)}] {station}", flush=True)
        if REFRESH_NOAA:
            try:
                execute("add_station.py", station)
                refreshed.append(station)
            except subprocess.CalledProcessError as exc:
                failures[station] = f"NOAA refresh failed (exit {exc.returncode})"
                print("WARNING:", failures[station], "— preserving any previous snapshot")
                if FAIL_ON_STATION_ERROR:
                    raise
        elif not (SNAPSHOTS / (station + ".json")).exists():
            failures[station] = "No saved snapshot (offline mode)"

    # Build the web pages and standardized exports from saved snapshots.
    # Existing station snapshots are retained when NOAA refresh fails.
    execute("build_embed.py")

    produced = sorted(p.stem for p in SNAPSHOTS.glob("*.json"))
    missing = sorted(set(ids) - set(produced))
    report = {
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "refresh" if REFRESH_NOAA else "offline",
        "gallery_station_ids": ids,
        "refreshed_station_ids": refreshed,
        "snapshot_station_ids": produced,
        "missing_gallery_snapshots": missing,
        "refresh_errors": failures,
        "data_directory": "SLR/data",
        "note": "Web gallery may query NOAA live; exported files use locally saved snapshots only."
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    test_results = {}
    if RUN_TESTS and shutil.which("node"):
        for test in ("test_data.cjs", "test_interactions.cjs"):
            script = TOOLS / test
            if script.exists():
                print("Running", test)
                outcome = subprocess.run(["node", str(script)], cwd=ROOT, check=False)
                test_results[test] = {"passed": outcome.returncode == 0, "exit_code": outcome.returncode}
                if outcome.returncode != 0:
                    print(f"WARNING: {test} failed (exit {outcome.returncode}); exported datasets are still available.")
                    if STOP_ON_TEST_FAILURE:
                        raise RuntimeError(f"Validation test failed: {test}")
    elif RUN_TESTS:
        print("Node.js not detected; JavaScript tests skipped.")

    report["test_results"] = test_results
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("\nDone. Files: SLR/data/*.csv, SLR/data/*.json")
    print(f"Snapshots: {len(produced)}; gallery stations: {len(ids)}")
    if missing:
        print("Missing snapshots:", ", ".join(missing))
    if failures:
        print("Refresh issues:", ", ".join(failures))
    print("See data/run_report.json for station-level outcomes.")
    if missing:
        print("WARNING: Some gallery stations do not have exports. No values were invented.")
    if any(not result["passed"] for result in test_results.values()):
        print("WARNING: One or more validation tests failed. Review the Node output before publishing.")


if __name__ == "__main__":
    main()
