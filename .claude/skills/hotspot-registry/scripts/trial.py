#!/usr/bin/env python3
"""Show the candidate routes of a route trial so a contributor can label it.

    python3 trial.py --list                     # every trial key, with avoidable/labelled flags
    python3 trial.py <pair>/<scenario>          # the trial's cards
    python3 trial.py <key> --geojson out.geojson  # routes as GeoJSON for geojson.io

Dependency-free. Reads eval/trials.json and eval/labels.json from the
repository root (found relative to this file).
"""

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
TRIALS = ROOT / "eval" / "trials.json"
LABELS = ROOT / "eval" / "labels.json"


def decode_polyline(encoded: str, precision: int = 5):
    """Google encoded polyline → list of (lat, lng)."""
    coords, index, lat, lng, factor = [], 0, 0, 0, 10 ** precision
    while index < len(encoded):
        for is_lat in (True, False):
            result, shift = 0, 0
            while True:
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1F) << shift
                shift += 5
                if b < 0x20:
                    break
            delta = ~(result >> 1) if result & 1 else result >> 1
            if is_lat:
                lat += delta
            else:
                lng += delta
        coords.append((lat / factor, lng / factor))
    return coords


def load():
    try:
        trials = json.loads(TRIALS.read_text())
    except FileNotFoundError:
        sys.exit(f"{TRIALS} not found — run from a checkout of the registry")
    labels = json.loads(LABELS.read_text()) if LABELS.exists() else {}
    return {t["key"]: t for t in trials}, labels


def show(trial, label):
    p, s = trial["pair"], trial["scenario"]
    print(f"{trial['key']}   at {trial['at']}   avoidable={trial['avoidable']}   control={p['control']}")
    print(f"  {p['why']}")
    print(f"  origin {p['origin']}  →  destination {p['destination']}")
    fastest = min(c["duration_sec"] for c in trial["cards"])
    for c in trial["cards"]:
        mark = "★" if label and label.get("best") == c["key"] else " "
        roads = f"  [{'; '.join(c['hotspot_roads'])}]" if c.get("hotspot_roads") else ""
        print(f"  {mark} {c['key']}  {c['type']:<8} {c['duration_sec']/60:5.1f} min  {c['km']:5.1f} km"
              f"  avoid {c['avoid_km']:4.1f} km  advise {c['advise_km']:4.1f} km"
              f"  peak official risk {c['max_cell_risk']:.2f}  incidents {c['incidents_500m']}"
              f"  +{(c['duration_sec']-fastest)/60:.1f} min{roads}")
    if label:
        print(f"  labelled by {label.get('labelled_by', '?')} on {label.get('labelled_on', '?')}: {label.get('rationale', '')}")
    else:
        print("  not labelled yet")


def geojson(trial, path):
    features = []
    for c in trial["cards"]:
        colour = "#c62828" if c["avoid_km"] > 0 else "#ef6c00" if c["advise_km"] > 0 else "#2e7d32"
        features.append({
            "type": "Feature",
            "geometry": {"type": "LineString",
                         "coordinates": [[lng, lat] for lat, lng in decode_polyline(c["polyline"])]},
            "properties": {"key": c["key"], "type": c["type"], "minutes": round(c["duration_sec"] / 60, 1),
                           "km": c["km"], "avoid_km": c["avoid_km"], "advise_km": c["advise_km"],
                           "roads": c.get("hotspot_roads", []), "stroke": colour, "stroke-width": 4},
        })
    pathlib.Path(path).write_text(json.dumps({"type": "FeatureCollection", "features": features}))
    print(f"wrote {path} — open it on https://geojson.io (red = avoid-tier corridor, orange = advise, green = clean)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("key", nargs="?", help="<pair>/<scenario>, e.g. dunoon-sunningdale-canalwalk/sat-02")
    ap.add_argument("--list", action="store_true", help="list every trial")
    ap.add_argument("--geojson", metavar="PATH", help="write the trial's routes as GeoJSON")
    args = ap.parse_args()

    trials, labels = load()
    if args.list or not args.key:
        for key, t in trials.items():
            flags = ("avoidable " if t["avoidable"] else "") + ("control " if t["pair"]["control"] else "")
            lbl = labels.get(key)
            state = "PROVISIONAL" if lbl and "PROVISIONAL" in lbl.get("rationale", "") else ("labelled" if lbl else "unlabelled")
            print(f"{key:<48} {len(t['cards'])} cards  {flags:<19} {state}")
        return
    trial = trials.get(args.key)
    if not trial:
        sys.exit(f"no trial {args.key!r} — see --list")
    show(trial, labels.get(args.key))
    if args.geojson:
        geojson(trial, args.geojson)


if __name__ == "__main__":
    main()
