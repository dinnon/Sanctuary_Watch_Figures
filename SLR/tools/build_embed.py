#!/usr/bin/env python3
"""Build a single-file embeddable chart with bundled station snapshots."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site" if (ROOT / "site").exists() else ROOT
snapshots = {}
for path in sorted((SITE / "snapshots").glob("*.json")):
    data = json.loads(path.read_text(encoding="utf-8"))
    if path.stem != data.get("station") or not data.get("rows"):
        raise ValueError(f"Invalid snapshot: {path}")
    snapshots[path.stem] = data

template = (ROOT / "tools" / "embed.template.html").read_text(encoding="utf-8")
payload = json.dumps(snapshots, separators=(",", ":")).replace("<", "\\u003c")
(SITE / "embed.html").write_text(template.replace("__BUNDLED_SNAPSHOTS__", payload), encoding="utf-8")
amount = (ROOT / "tools" / "amount.template.html").read_text(encoding="utf-8")
(SITE / "embed_amount.html").write_text(amount.replace("__BUNDLED_SNAPSHOTS__", payload), encoding="utf-8")
stations = json.loads((SITE / "stations.json").read_text(encoding="utf-8"))
home = (ROOT / "tools" / "home.template.html").read_text(encoding="utf-8")
(SITE / "index.html").write_text(home.replace("__STATIONS__", json.dumps(stations).replace("<", "\\u003c")), encoding="utf-8")
print(f"Built {SITE / 'index.html'}, {SITE / 'embed.html'}, and {SITE / 'embed_amount.html'} with {len(snapshots)} station snapshots")
