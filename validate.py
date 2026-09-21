#!/usr/bin/env python3
"""Validate corridors.json and eval/ against the authoring rules in CONTRIBUTING.md.

Authoritative checker, and deliberately dependency-free so anyone can run it:

    python3 validate.py

Every rule here is one a machine can settle. The ones it cannot — is the
evidence real, does the hazard belong to the road rather than to an event, is
this corridor already well covered by official data — are what review is for.
"""

import datetime
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).parent
DATA = ROOT / "corridors.json"
SCHEMA = ROOT / "schema.json"
EVAL = ROOT / "eval"

SCHEMA_VERSION = 1
RISK_MAX = 1.0
AVOID_THRESHOLD = 0.5  # >= is avoid tier, < is advisory. Mirrors the consumer.
ZA_LAT = (-35.0, -22.0)
ZA_LNG = (16.0, 33.0)
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
WINDOW = re.compile(r"^([01]\d|2[0-3]):[0-5]\d-([01]\d|2[0-3]):[0-5]\d$")
MODES = {"forced_stop", "smash_and_grab", "hijacking", "protest_blockade", "unclear"}
CARD_KEY = re.compile(r"^[0-9a-f]{8}$")

# Rule 2: the driver-facing name must be a road. These are settlements that have
# appeared in drafts or reporting about listed corridors, so they are the ones
# most likely to slip into a `road` field by accident. Not a blocklist of places
# — a guard on one specific mistake.
SETTLEMENT_WORDS = [
    "du noon", "dunoon", "khayelitsha", "nyanga", "gugulethu", "langa",
    "bonteheuwel", "mitchells plain", "philippi", "delft", "elsies river",
    "manenberg", "mfuleni", "macassar", "atlantis", "kraaifontein",
]

errors: list[str] = []
warnings: list[str] = []


def err(where: str, msg: str) -> None:
    errors.append(f"{where}: {msg}")


def warn(where: str, msg: str) -> None:
    warnings.append(f"{where}: {msg}")


def check_schema_constants() -> None:
    """Keep schema.json and this script from drifting apart."""
    try:
        s = json.loads(SCHEMA.read_text())
    except FileNotFoundError:
        warn("schema.json", "missing — editor support and third-party validation will be broken")
        return
    corridor = s["$defs"]["corridor"]["properties"]
    lat, lng = corridor["corridor"]["items"]["prefixItems"]
    pairs = [
        ("schema_version", s["properties"]["schema_version"]["const"], SCHEMA_VERSION),
        ("risk maximum", corridor["risk"]["maximum"], RISK_MAX),
        ("latitude min", lat["minimum"], ZA_LAT[0]),
        ("latitude max", lat["maximum"], ZA_LAT[1]),
        ("longitude min", lng["minimum"], ZA_LNG[0]),
        ("longitude max", lng["maximum"], ZA_LNG[1]),
    ]
    for name, in_schema, here in pairs:
        if in_schema != here:
            err("schema.json", f"{name} is {in_schema} but validate.py uses {here}")


def check(data: dict) -> None:
    if data.get("schema_version") != SCHEMA_VERSION:
        err("file", f"schema_version must be {SCHEMA_VERSION}, got {data.get('schema_version')!r}")

    hotspots = data.get("hotspots")
    if not isinstance(hotspots, list) or not hotspots:
        err("file", "hotspots must be a non-empty array")
        return

    today = datetime.date.today()
    seen_ids: dict[str, int] = {}
    tiers = {"avoid": 0, "advise": 0}

    for i, h in enumerate(hotspots):
        where = f"hotspots[{i}] ({h.get('id', 'no id')})"

        if not isinstance(h, dict):
            err(where, "must be an object")
            continue

        extra = set(h) - {"id", "road", "risk", "rationale", "sources", "reviewed_on", "corridor", "hours", "mode"}
        if extra:
            err(where, f"unknown field(s) {sorted(extra)} — the schema is closed on purpose")

        # Rule 8: optional structured reading of the rationale.
        hours = h.get("hours")
        if hours is not None and hours != "always":
            if not isinstance(hours, list) or not hours or not all(isinstance(w, str) and WINDOW.match(w) for w in hours):
                err(where, f"hours {hours!r} must be \"always\" or a non-empty list of \"HH:MM-HH:MM\" windows")
        mode = h.get("mode")
        if mode is not None and mode not in MODES:
            err(where, f"mode {mode!r} must be one of {sorted(MODES)}")

        hid = h.get("id", "")
        if not isinstance(hid, str) or not SLUG.match(hid):
            err(where, f"id {hid!r} must be a kebab-case slug")
        elif hid in seen_ids:
            err(where, f"duplicate id {hid!r}, first seen at hotspots[{seen_ids[hid]}]")
        else:
            seen_ids[hid] = i

        road = h.get("road", "")
        if not isinstance(road, str) or len(road.strip()) < 3:
            err(where, "road is required and names the road shown to the driver")
        else:
            lowered = road.lower()
            for word in SETTLEMENT_WORDS:
                # Allowed only as a bound on a stretch of road ("between X and Y").
                if word in lowered and not re.search(r"\b(between|near|past|at the)\b", lowered):
                    err(where, f"road {road!r} names the settlement {word!r} — rule 2 "
                               f"(a place name may only BOUND a stretch, e.g. 'N7 between X and Y')")

        risk = h.get("risk")
        if not isinstance(risk, (int, float)) or isinstance(risk, bool):
            err(where, "risk must be a number")
        elif not (0 < risk <= RISK_MAX):
            err(where, f"risk {risk} outside (0, {RISK_MAX}]")
        else:
            tiers["avoid" if risk >= AVOID_THRESHOLD else "advise"] += 1

        rationale = h.get("rationale", "")
        if not isinstance(rationale, str) or len(rationale.strip()) < 40:
            err(where, "rationale is required and must actually explain the entry")

        sources = h.get("sources")
        if not isinstance(sources, list) or not sources:
            err(where, "at least one source is required — an entry nobody can check is an opinion")
        else:
            for s in sources:
                if not isinstance(s, str) or not s.strip():
                    err(where, "empty source entry")
                elif not s.startswith(("http://", "https://")):
                    err(where, f"source {s!r} must be a URL someone can open")

        reviewed = h.get("reviewed_on", "")
        try:
            d = datetime.date.fromisoformat(reviewed)
            if d > today:
                err(where, f"reviewed_on {reviewed} is in the future")
            elif (today - d).days > 400:
                warn(where, f"reviewed_on {reviewed} is over a year old — review is quarterly")
        except (TypeError, ValueError):
            err(where, f"reviewed_on {reviewed!r} must be YYYY-MM-DD")

        corridor = h.get("corridor")
        if not isinstance(corridor, list) or len(corridor) < 2:
            err(where, "corridor needs at least 2 [latitude, longitude] points")
            continue
        for j, pt in enumerate(corridor):
            if not isinstance(pt, list) or len(pt) != 2 or not all(
                    isinstance(v, (int, float)) and not isinstance(v, bool) for v in pt):
                err(where, f"corridor[{j}] must be [latitude, longitude]")
                continue
            lat, lng = pt
            if not (ZA_LAT[0] <= lat <= ZA_LAT[1]) or not (ZA_LNG[0] <= lng <= ZA_LNG[1]):
                hint = " (latitude and longitude look swapped)" if (
                    ZA_LAT[0] <= lng <= ZA_LAT[1] and ZA_LNG[0] <= lat <= ZA_LNG[1]) else ""
                err(where, f"corridor[{j}] [{lat}, {lng}] is outside South Africa{hint}")

    if not tiers["avoid"]:
        warn("file", "no avoid-tier corridors — nothing generates an avoiding route")
    if not tiers["advise"]:
        warn("file", "no advisory corridors — well-measured roads get no named warning")
    print(f"{len(hotspots)} corridors: {tiers['avoid']} avoid, {tiers['advise']} advise")


def check_eval() -> None:
    """eval/labels.json must label cards that exist in eval/trials.json, with a
    rationale and provenance; eval/incident_cases.json must be well-formed."""
    labels_path = EVAL / "labels.json"
    trials_path = EVAL / "trials.json"
    if labels_path.exists():
        if not trials_path.exists():
            err("eval/labels.json", "exists without eval/trials.json — nothing to label against")
        else:
            try:
                labels = json.loads(labels_path.read_text())
                trials = json.loads(trials_path.read_text())
            except json.JSONDecodeError as e:
                err("eval", f"not valid JSON: {e}")
                return
            cards = {t["key"]: [c["key"] for c in t["cards"]] for t in trials}
            today = datetime.date.today()
            for key, lbl in labels.items():
                where = f"eval/labels.json[{key}]"
                if key not in cards:
                    err(where, "no such trial in eval/trials.json — was it re-generated? (`just eval-publish`)")
                    continue
                if not isinstance(lbl, dict):
                    err(where, "must be an object")
                    continue
                best = lbl.get("best")
                if best not in cards[key]:
                    err(where, f"best {best!r} is not one of this trial's cards {cards[key]}")
                order = lbl.get("order")
                if order is not None:
                    if sorted(order) != sorted(cards[key]):
                        err(where, f"order must list every card exactly once: {cards[key]}")
                    elif order[0] != best:
                        err(where, "order[0] must equal best")
                rationale = lbl.get("rationale", "")
                if not isinstance(rationale, str) or len(rationale.strip()) < 40:
                    err(where, "rationale is required — say why this card, in your own words")
                if not isinstance(lbl.get("labelled_by"), str) or not lbl["labelled_by"].strip():
                    err(where, "labelled_by is required (your GitHub handle)")
                try:
                    if datetime.date.fromisoformat(lbl.get("labelled_on", "")) > today:
                        err(where, "labelled_on is in the future")
                except (TypeError, ValueError):
                    err(where, f"labelled_on {lbl.get('labelled_on')!r} must be YYYY-MM-DD")
                for s in lbl.get("sources", []) or []:
                    if not isinstance(s, str) or not s.startswith(("http://", "https://")):
                        err(where, f"source {s!r} must be a URL someone can open")
            print(f"{len(labels)} route labels over {len(trials)} trials")

    cases_path = EVAL / "incident_cases.json"
    if cases_path.exists():
        try:
            cases = json.loads(cases_path.read_text())
        except json.JSONDecodeError as e:
            err("eval/incident_cases.json", f"not valid JSON: {e}")
            return
        types = {"hijack", "smash_and_grab", "protest_action", "debris", "crash", "stalled_vehicle", "other", ""}
        seen = set()
        for i, c in enumerate(cases):
            where = f"eval/incident_cases.json[{i}] ({c.get('id', 'no id') if isinstance(c, dict) else '?'})"
            if not isinstance(c, dict):
                err(where, "must be an object")
                continue
            if c.get("id") in seen:
                err(where, "duplicate id")
            seen.add(c.get("id"))
            for field in ("id", "description", "type", "severity", "age_hours", "truth_active", "truth_type", "injection"):
                if field not in c:
                    err(where, f"missing {field}")
            if not isinstance(c.get("description"), str) or len(c.get("description", "")) < 10:
                err(where, "description must be a real sentence")
            if c.get("truth_type") not in types:
                err(where, f"truth_type must be one of {sorted(types)}")
            if not isinstance(c.get("truth_active"), bool) or not isinstance(c.get("injection"), bool):
                err(where, "truth_active and injection must be true/false")
        print(f"{len(cases)} incident cases")


def main() -> int:
    try:
        data = json.loads(DATA.read_text())
    except FileNotFoundError:
        print(f"error: {DATA} not found", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"error: corridors.json is not valid JSON: {e}", file=sys.stderr)
        return 1

    check_schema_constants()
    check(data)
    check_eval()

    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"error: {e}", file=sys.stderr)

    if errors:
        print(f"\nFAILED — {len(errors)} error(s). See CONTRIBUTING.md.", file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
