# halomaps-hotspot-registry

A curated, sourced register of **road corridors** where drivers face elevated
vehicle-crime risk, plus the community's route-choice labels (`eval/`). It is
consumed by HaloMaps; merging here ships nothing until HaloMaps bumps its pin.

The one rule that matters more than every other: **a corridor is a road, never
an area.** No polygons, radii or suburbs — see README.md and CONTRIBUTING.md
rule 1c.

Working on a corridor, a route label, an incident case, or a question about any
of them: use the `hotspot-registry` skill (`.claude/skills/hotspot-registry`) —
it carries the workflow and a script that renders a trial's routes. The rules
themselves live in CONTRIBUTING.md and eval/README.md; `python3 validate.py` is
the authoritative check and runs in CI.
