# Rootstock

A small **Python simulation** of grafted crops, genetics, soil, and seasonal cycles—useful for prototyping games, teaching, or population ideas.

## What it models

- **Species & breeds** — Apple, pear, quince, tomato, eggplant, pepper, with named cultivar presets (`sim/breeds.py`).
- **Grafting** — Scion + rootstock genomes; compatibility by plant family; traits split between canopy (scion) and roots / dwarfing (rootstock).
- **Genetics** — Diploid loci, crossing, mutation; morph traits (leaf form, root spread, stem height) and quality-style traits (sugar, vigor, and so on).
- **Soil per plot** — Nutrients, pH, water, organic matter, drainage, compaction; seasonal weather and crop draw; optional uptake multipliers by **lifecycle stage**.
- **Lifecycle** — Stages such as germination, graft establishment, vegetative, flowering, and productive years; seed-grown plants use a longer early phase than bench-grafted stock (`sim/lifecycle.py`).
- **Seasons** — Planting, aging, harvest with seeds, optional replant onto rootstock (same idea as the CLI demo).

## Requirements

- **Python 3.10+** (stdlib only: no `pip install` needed for core sim, tests, or GUI).

## Run

From the repository root:

| Command | Purpose |
|--------|---------|
| `python demo.py` | Text demo: several seasons, cross-pollination, replant plot 2 from seed |
| `python gui.py` | Tkinter UI: field canvas, soil bars, auto-play, speed slider, replant toggle |
| `python -m unittest discover --start-directory tests --top-level-directory . -v` | Tests |

## Package layout

```
sim/
  breeds.py      # Cultivar presets → genomes
  cycles.py      # FieldPlot, Orchard, seasons, harvest, seeds
  genetics.py    # Genome, cross, mutate, phenotype rules
  graft.py       # GraftedPlant
  lifecycle.py   # Stages, soil uptake multipliers
  soil.py        # PlotSoil generation and seasonal dynamics
  species.py     # Species definitions, starter genomes, graft rules
tests/
  test_sim_cycles.py
demo.py
gui.py
```

## Extending

- Add **species** or **breeds** in `sim/species.py` and `sim/breeds.py`.
- Tune **time to first harvest** with `GraftedPlant.mature_after` (or introduce per-species defaults on the species object if you outgrow a single global default).
- Hook **yield** or **stress** by combining expressed traits with `PlotSoil` and `current_lifecycle_stage()` in `Orchard.run_season` or a thin wrapper.
