# Contributing a corridor

Every entry here is a published claim that a specific, real road is dangerous.
That deserves a high bar, and most proposals are declined — not because the
danger isn't real, but because this register is deliberately narrow. Read the
rules before opening a pull request.

**Corrections and withdrawals are the most valuable contributions.** A corridor
that has improved but stays listed makes the whole register less trustworthy. If
you can show a road is better than this file says, please open a PR removing it.

## The rules

### 1. Evidence first, and `risk` picks the tier

An entry earns its place on **published evidence**, not on how much of a gap it
fills. Pick the tier with `risk`:

| Tier | `risk` | What it does |
|---|---|---|
| **avoid** | ≥ 0.5 | Routes around the corridor, scores it, names it, blocks the "safest" label |
| **advise** | 0 < `risk` < 0.5 | Names it and blocks the "safest" label. Never routes around it. |

Choose **advise** when the road is one a driver cannot realistically avoid (a
national route, the only link to an airport), or when official crime data
already scores it highly. Choose **avoid** only when the official data is blind
to the corridor *and* there is a realistic alternative road.

If you aren't sure, propose **advise**. It is the safer default: it tells the
driver without pushing them somewhere that might be worse.

> The blindness check needs production data the maintainers hold, so you are not
> expected to run it. Say what you know; the tier may be adjusted in review.

#### 1a. Faded is not the same as blind

A corridor that official data scores highly, but whose score has merely decayed
with the age of the data, is **not** invisible — the consuming app already
routes around it. It belongs in the advisory tier, for the road name. This is
the rule that stops this register growing every quarter until it lists
everywhere.

#### 1b. Standing geometry, not transient events

This register is a **standing** description of a road. A hazard that belongs to
the road itself qualifies: an unlit freeway with settlements on the verge, a
slow interchange beside a footpath, an isolated stretch with no frontage where a
forced stop cannot be seen.

A hazard that belongs to an **event** does not: protest stone-throwing, a march,
a strike, a taxi dispute. Those are real and dangerous, and they are *live* data
— they move, they end, and a navigation app should learn them from an incident
feed. Permanently down-weighting a national route for something that happens a
few days a year pushes drivers onto worse roads for the other 360.

#### 1c. Corridors are LINEAR. Never propose an area.

See the README. An entry traces a road. No polygons, no suburbs, no radii. This
is not negotiable and is the single rule most likely to get a PR closed.

#### 1d. Coverage bias is real — help correct it

Curation follows reporting, and reporting is uneven: some victims and some
suburbs get more coverage per incident than others. If this register drifts into
listing only roads through poor or historically Black and Coloured areas, it is
describing the news cycle rather than the hazard. Evidence for corridors
elsewhere is actively wanted. The fix is always *more* evidence, never dropping
well-evidenced entries.

### 2. `road` names a road, never a settlement

It is shown **verbatim** to a driver. `"Malibongwe Drive (M12)"` and
`"N7 between Melkbosstrand and Killarney Gardens"` are fine. A township or
suburb name on its own is not.

The actionable fact for someone behind the wheel is which stretch of tar to be
alert on. Naming a community in a shipped app publishes a claim about the people
who live there — and it isn't even useful, because they cannot act on it.

Using a place name to *bound* a stretch of road ("between X and Y") is fine;
that is describing the road's extent.

### 3. `rationale` and at least one `sources` entry are required

An entry nobody can check is an opinion, not a dataset. `rationale` should state
what the pattern is and why it belongs to the road. `sources` should be
published reporting, official statements, CPF or municipal communications —
something a stranger can read.

Say what the sources actually say. If the evidence is thin, say that too; a
weak-but-honest rationale is reviewable, an overstated one is not.

### 4. `risk` is in (0, 1]

Pick against the **documented pattern**, not the worst single incident.

Avoid tier:

| `risk` | Pattern |
|---|---|
| `0.85` | Sustained, corroborated hijacking or armed-robbery corridor |
| `0.70` | Frequent smash-and-grab or stoning of vehicles |
| `0.55` | Elevated but episodic |

Advisory tier — the number never drives routing, so use it to rank warnings
against each other:

| `risk` | Pattern |
|---|---|
| `0.45` | The worst corridors, where official data already scores the road highly |
| `0.40` | A named, repeatedly documented hotspot |
| `0.35` | Named by an official or CPF list without incident detail |

### 5. `reviewed_on` is when a human last checked

`YYYY-MM-DD`, not in the future. The register is reviewed quarterly. Validation
deliberately does **not** fail on age: a clock-triggered CI failure is a time
bomb, not a safety control.

### 6. `corridor` traces the road's shape

At least two `[latitude, longitude]` points, all inside South Africa. Latitude
first — swapping them is the commonest mistake and validation will catch it.

You do not need a point per block. The consumer densifies to 150 m before
indexing, so tracing the road's *shape* is enough.

### 7. Keep it tight

Trace the stretch the evidence describes, not the whole road. An entry that
over-reaches re-creates, at smaller scale, exactly the over-painting this
register exists to correct — and it makes the warning less believable.

### 8. `hours` and `mode` — say when and how, if the evidence does

Both are optional, and both are a *structured reading of your own rationale*, not
new claims. Leave them out when the sources don't say.

- `hours`: `"always"` when the pattern is not tied to a time of day, or a list of
  SAST windows like `["18:00-03:59"]` (wrapping past midnight is fine) when the
  sources do say — "overwhelmingly between 18:00 and 04:00", "after dark", "in
  the morning rush". Absent means *unknown*, and consumers must treat it that
  way; it never defaults to always.
- `mode`: how drivers are attacked — `forced_stop` (objects, stones or debris
  placed to make a driver stop), `smash_and_grab` (occupants robbed at lights or
  in slow traffic), `hijacking`, `protest_blockade`, or `unclear` when the
  sources describe a hotspot without saying how.

The consuming app uses these to decide whether a warning applies *now* and to
measure whether its AI can read the rationale as well as you can. If you think a
window is wrong, change it and say why in the PR.

## Labelling route trials

The register says where to be careful. `eval/` asks the harder question — given
the real candidate routes between two places, **which would a careful local driver
take at this hour?** — and anyone can answer it, with a rationale. See
[`eval/README.md`](eval/README.md).

## Tracing geometry

Trace against a real routing engine rather than eyeballing coordinates, and
**verify that the road name in the result matches the road you meant**. Two
corridors were dropped from the initial import because their traces quietly ran
onto neighbouring roads.

Watch for punctuation in official road names — `Borcherd's Quarry Road` has an
apostrophe, and matching on `Borcherds` silently finds nothing.

## Before you open the PR

```bash
python3 validate.py
```

No dependencies beyond Python 3. CI runs the same script.

We recommend making changes with a coding agent: the repository ships a skill
([`.claude/skills/hotspot-registry`](.claude/skills/hotspot-registry/SKILL.md),
picked up automatically by Claude Code) that walks the agent through these rules,
renders a trial's routes, formats the entry and runs the validator — while
leaving the evidence and the preference to you.

## What happens after it merges

Merging here does **not** deploy anything. Consumers pin an exact commit of this
repository, so a new corridor only reaches a navigation app when a maintainer
bumps that pointer and that change is separately reviewed. Merging a corridor
here is a proposal being accepted into the register, not a change being shipped
to drivers.
