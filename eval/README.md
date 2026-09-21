# Route-choice labels

The corridors in `../corridors.json` tell the app *where* to be careful. The files
here decide something harder: **given two or three real routes between the same
two places, which one would a careful local driver take at this hour?** HaloMaps
uses these labels to measure whether a change to its route chooser — including
its AI judgment — actually picks safer routes, before that change ships.

Preference is not one person's to hold. Anyone can label a trial, as long as they
say why.

## What is here

| File | Written by | What it is |
|---|---|---|
| `trials.json` | HaloMaps (`just eval-publish`) | The trials to label: 36 Cape Town origin→destination pairs × 2 times of day, each with its 2–3 candidate routes ("cards"): minutes, km, corridors touched, and the polyline so you can look at it. |
| `scenarios.json` | HaloMaps | The times of day a trial is judged at (SAST). |
| `labels.json` | **You** | One preference per trial, with a rationale and your handle. |
| `incident_cases.json` | **You** | Short incident descriptions with the truth about them, used to check the app can read live reports — local-language phrasing especially wanted. |

## Labelling a trial

Find the trial in `trials.json` by its `key` (`<pair>/<scenario>`), look at its
cards — paste a card's `polyline` into any polyline decoder, or ask a maintainer
for the GeoJSON — and add an entry:

```jsonc
"dunoon-sunningdale-canalwalk/sat-02": {
  "best": "94995abd",                          // the card you would drive
  "order": ["94995abd", "dbfe5190", "a19b0939"], // every card, best first (optional)
  "rationale": "The Koeberg Road card; its 0.7 km of Potsdam Road is the interchange, not the stretch the register warns about. At 02:00 the extra 2.5 minutes are worth staying off Malibongwe past Du Noon.",
  "sources": ["https://…"],                    // optional, if you are citing something
  "labelled_by": "your-github-handle",
  "labelled_on": "2026-09-21"
}
```

- `best` and `order` use the 8-character card keys from `trials.json`. A key is a
  hash of the route's geometry, so it stays the same until the road network or the
  routing engine changes that route.
- Look at the geometry before naming a road in your rationale — a trial's `why`
  is a hint written before the routes were recorded, and the polyline is what the
  app actually drives. `.claude/skills/hotspot-registry/scripts/trial.py <key>
  --geojson out.geojson` renders the cards for geojson.io.
- `rationale` is required and must actually explain the choice (40+ characters).
  It is what a reviewer — and the next contributor who disagrees — reads.
- A trial marked `"avoidable": true` has one card that is at least 1 km cleaner of
  avoid-tier corridors than another; those are the ones where the choice matters
  most. On a trial where every card crosses a listed road, pick the least bad.
- Disagree with an existing label? Open a PR that changes it and says why. Review
  decides, the same way it does for corridors.

Labels that were machine-seeded to get the set started say so in their
`rationale`; replacing them with a human reading is the most useful contribution.

## Incident cases

Each entry is a description as a driver or a traffic account might write it, and
the truth a reader would arrive at:

```jsonc
{
  "id": "case-cleared-debris",
  "description": "Update: the rocks on the N2 inbound before Borcherd's Quarry have been cleared.",
  "type": "debris",            // what the reporter selected
  "severity": 1,               // 1–3
  "age_hours": 2,
  "truth_active": false,       // was the hazard still present when this was written?
  "truth_type": "debris",      // hijack | smash_and_grab | protest_action | debris | crash | stalled_vehicle | other
  "injection": false           // true if the text tries to steer the reader's answer
}
```

Afrikaans, isiXhosa and the way local feeds actually phrase things are the gaps.

## Validation

`python3 validate.py` from the repository root checks both files (keys exist in
`trials.json`, `order` is complete, rationale and provenance present). CI runs the
same.

## What happens after it merges

Nothing ships. HaloMaps pins a commit of this repository and copies these files
into its test fixtures (`just eval-sync`); a label changes a measurement only after
that pointer is bumped in a reviewed change there, and a measurement never changes
a route directly.
