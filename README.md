# halomaps-hotspot-registry

A curated, sourced register of **road corridors** in South Africa where drivers
are documented to be at elevated risk of vehicle crime — smash-and-grab,
stoning, hijacking, robbery at a forced stop.

It exists because official crime data cannot answer the question a driver is
actually asking. SAPS publishes crime per **police precinct**, and a metro
precinct spans 8–12 km. That is enough to say "this suburb has a lot of crime"
and nowhere near enough to say "be alert on this stretch of tar". This register
supplies the missing granularity, by hand, with a citation for every claim.

It is consumed by [HaloMaps](https://halomaps.co.za), a safer-route navigation
app for South Africa, and is published separately so that every entry can be
checked, challenged and corrected by anyone.

## This is a register of ROADS, never of areas

Read this before proposing anything.

An entry traces **a road**. It must never become a polygon, a suburb, a radius
or a neighbourhood. In South Africa the distance between a list of dangerous
*roads* and a list of dangerous *areas* is almost nothing in the data and
everything in what the thing becomes: the second is a redlining map. It would
track apartheid spatial planning almost exactly, and software that quietly
steers people around whole communities does real economic harm to the people and
businesses inside them.

Naming a stretch of road a driver is currently on is a traffic advisory.
Shading a neighbourhood is a verdict on the people who live there.

The schema has no polygon type. That is not an oversight, and pull requests
adding one will be declined. See [CONTRIBUTING.md](CONTRIBUTING.md) for the full
rules.

## Route-choice labels (`eval/`)

The register says *where* to be careful. [`eval/`](eval/) holds the community's
answer to a harder question — between the real candidate routes for a trip, which
would a careful local driver take at this hour? — with a rationale per label.
HaloMaps scores every change to its route chooser against these before it ships.
See [`eval/README.md`](eval/README.md).

## The data

Everything lives in [`corridors.json`](corridors.json), validated against
[`schema.json`](schema.json) on every push and pull request.

```jsonc
{
  "schema_version": 1,
  "hotspots": [
    {
      "id": "potsdam-road",              // stable slug, used to withdraw an entry
      "road": "Potsdam Road (M5)",       // shown VERBATIM to the driver
      "risk": 0.7,                       // (0, 1] — also selects the tier, below
      "rationale": "Why this is listed, in the curator's own words.",
      "sources": ["https://…"],          // published evidence, at least one
      "reviewed_on": "2026-09-20",       // when a human last confirmed it
      "hours": ["18:00-05:59"],          // optional: when the hazard applies (SAST), or "always"
      "mode": "forced_stop",             // optional: how drivers are attacked
      "corridor": [[-33.81215, 18.54047], [-33.8346, 18.52586]]   // [lat, lng]
    }
  ]
}
```

### Two tiers, chosen by `risk`

| Tier | `risk` | Effect on a route that enters the corridor |
|---|---|---|
| **avoid** | ≥ 0.5 | Scored as riskier, an alternative is generated around it, the road is named to the driver, and the route cannot be labelled the safest |
| **advise** | 0 < `risk` < 0.5 | The road is named to the driver and the route cannot be labelled the safest — but **no** attempt is made to route around it |

The advisory tier is for roads a driver cannot realistically avoid. Every route
to Cape Town International runs on the N2; trying to route around it returns
worse alternatives and helps nobody, but the driver still wants to be told which
road they are on.

Pick **avoid** only where the official data is genuinely blind to the corridor
*and* a realistic alternative exists.

## Using it

### As a git submodule (how HaloMaps consumes it)

```bash
git submodule add https://github.com/Business-Blacksmiths/halomaps-hotspot-registry.git path/to/hotspots
git submodule update --init --recursive
```

A submodule pins an **exact commit**, not a branch. That is deliberate for a
safety dataset: nothing published here reaches anyone's navigation app until a
human bumps the pointer in the consuming repository and that change is reviewed.
Merging a corridor here is a proposal, not a deployment.

To take a later version:

```bash
git submodule update --remote path/to/hotspots
git add path/to/hotspots && git commit -m "chore: bump hotspot registry"
```

CI that runs tests against this data must check submodules out explicitly —
`actions/checkout` does **not** do it by default:

```yaml
- uses: actions/checkout@v5
  with:
    submodules: true
```

### Directly

`corridors.json` is a plain file in a public repository; read it however you
like. If you consume it in something people rely on, please pin a commit rather
than tracking `main`, for the reason above.

## Validating a change locally

No dependencies beyond Python 3:

```bash
python3 validate.py
```

It checks the schema and the authoring rules that can be machine-checked, and is
the same script CI runs.

## Contributing

Corrections are especially welcome — an entry that is out of date is worse than
no entry. If a corridor listed here has improved, say so and it will be
withdrawn. See [CONTRIBUTING.md](CONTRIBUTING.md).

### Recommended: contribute with a coding agent

This repository ships a skill for AI coding agents —
[`.claude/skills/hotspot-registry`](.claude/skills/hotspot-registry/SKILL.md) —
and we recommend using one to make your change. Open the checkout in
[Claude Code](https://claude.com/claude-code) (the skill is picked up
automatically; other agents can be pointed at the `SKILL.md` file) and describe
what you want in plain language:

- *"Add the stretch of Voortrekker Road through Parow — here are two articles."*
- *"I want to label the Sunningdale to Canal Walk trip at 2am; I'd take Koeberg
  Road and stay off Malibongwe."*
- *"Why would an entry for the Nyanga area be declined?"*

The agent knows the rules (roads never areas, evidence before tier, `hours` and
`mode` only from the sources), renders a trial's candidate routes so you can
look at them (`scripts/trial.py`), formats the entry, runs `validate.py`, and
drafts the PR. What it will not do is supply the evidence or the preference:
sources come from you, and a route label records *your* choice with *your*
rationale — the skill is explicit that the agent helps you say it, not decide
it. You can of course edit the JSON by hand; the same rules and the same
validator apply either way.

## Licence and disclaimer

Data is published under [CC BY 4.0](LICENSE). Attribute it, and do not present
it as an official or law-enforcement source. It is a curated, best-effort
reading of published reporting. It is **not** a guarantee of anyone's safety,
the absence of a road from this list means nothing, and no entry should be read
as a statement about the people who live near it.
