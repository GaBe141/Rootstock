#!/usr/bin/env python3
"""Run a short multi-cycle simulation: graft, grow, harvest, replant from seed."""

from __future__ import annotations

import random
import sys

from sim import (
    FieldPlot,
    Orchard,
    Seed,
    default_breeds,
    default_phenotype_rules,
    default_species,
    random_plots_soil,
    species_by_id,
)


def main() -> None:
    rng = random.Random(42)
    rules = default_phenotype_rules()
    pear_root = species_by_id()["pyrus_communis"]  # rootstock stand-in (same family as apple)

    soils = random_plots_soil(3, rng)
    plots = [
        FieldPlot(soil=s)
        for s in soils
    ]
    orchard = Orchard(plots=plots)

    # Two apple breeds: spur-type (short shaft) vs standard (tall); pear roots for all.
    plots[0].plant_graft_from_breed("apple_spur_type", pear_root)
    plots[1].plant_graft_from_breed("apple_standard", pear_root)
    plots[2].plant_graft_from_breed("apple_standard", pear_root)

    print("Species:", ", ".join(s.common_name for s in default_species()))
    print("Breeds:", ", ".join(f"{b.label} ({b.id})" for b in default_breeds()))
    for i, p in enumerate(plots):
        print(f"Plot {i} soil: {p.soil.as_dict()}")
    print("---")

    all_seeds: list[Seed] = []

    for cycle in range(6):
        # Cross-pollinate: plot 1 pollen onto plot 0 for slightly richer genetics
        pollen_map = {0: plots[1].plant.scion_genome if plots[1].plant else None}
        pollen_map = {k: v for k, v in pollen_map.items() if v is not None}

        harvests = orchard.run_season(
            rng,
            rules,
            pollen_by_plot=pollen_map or None,
            seeds_per_harvest=2,
            mutation_rate=0.04,
        )

        print(f"Season {orchard.season} (cycle {cycle + 1})")
        for i, p in enumerate(plots):
            print(f"  plot {i} soil: {p.soil.as_dict()}")
        for h in harvests:
            m = h.traits_snapshot
            morph = {
                k: m[k]
                for k in ("leaf", "root_spread", "shaft", "dwarf")
                if k in m
            }
            print(f"  harvest {h.species_id}: morph {morph} | full {m}")
        for h in harvests:
            all_seeds.extend(h.seeds)

        # Replant one plot from best random seed (toy selection)
        if all_seeds and cycle < 5:
            pick = rng.choice(all_seeds)
            plots[2].plant = None
            plots[2].plant_seed(pick, pear_root, rng)
            print(f"  replanted plot 2 from seed (sugar locus {pick.genome.loci.get('sugar')})")

        print()

    print(f"Total seeds produced: {len(all_seeds)}")


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(0)
