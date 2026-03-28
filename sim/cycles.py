"""Planting, seasons, harvest, and seed with optional pollination partner."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from sim.breeds import breeds_by_id, genome_for_breed
from sim.genetics import Genome, PhenotypeRules, cross_parents, mutate
from sim.graft import GraftedPlant
from sim.lifecycle import resource_draw_multipliers
from sim.soil import PlotSoil, default_plot_soil
from sim.species import Species, species_by_id, starter_genome


@dataclass
class Seed:
    species_id: str
    genome: Genome


@dataclass
class HarvestResult:
    species_id: str
    traits_snapshot: dict[str, str]
    seeds: list[Seed] = field(default_factory=list)


@dataclass
class FieldPlot:
    """One grafted tree or empty, with its own soil patch."""

    plant: GraftedPlant | None = None
    soil: PlotSoil = field(default_factory=default_plot_soil)

    def plant_seed(
        self,
        seed: Seed,
        rootstock_species: Species,
        rng: random.Random,
    ) -> None:
        scion = species_by_id()[seed.species_id]
        self.plant = GraftedPlant(
            scion_species=scion,
            rootstock_species=rootstock_species,
            scion_genome=seed.genome,
            rootstock_genome=starter_genome(rootstock_species.id),
            started_from_seed=True,
        )

    def plant_graft_direct(
        self,
        scion_species: Species,
        rootstock_species: Species,
        scion_genome: Genome | None = None,
        rootstock_genome: Genome | None = None,
    ) -> None:
        self.plant = GraftedPlant(
            scion_species=scion_species,
            rootstock_species=rootstock_species,
            scion_genome=scion_genome or starter_genome(scion_species.id),
            rootstock_genome=rootstock_genome or starter_genome(rootstock_species.id),
        )

    def plant_graft_from_breed(
        self,
        breed_id: str,
        rootstock_species: Species,
    ) -> None:
        b = breeds_by_id()[breed_id]
        scion = species_by_id()[b.species_id]
        self.plant_graft_direct(
            scion,
            rootstock_species,
            scion_genome=genome_for_breed(breed_id),
            rootstock_genome=starter_genome(rootstock_species.id),
        )


@dataclass
class Orchard:
    plots: list[FieldPlot]
    season: int = 0

    def run_season(
        self,
        rng: random.Random,
        rules: PhenotypeRules,
        *,
        pollen_by_plot: dict[int, Genome] | None = None,
        seeds_per_harvest: int = 3,
        mutation_rate: float = 0.03,
    ) -> list[HarvestResult]:
        """
        Advance all plants one season. Mature plants harvest fruit + seeds.
        pollen_by_plot: optional map plot_index -> pollen donor genome (else self-pollination).
        """
        self.season += 1
        harvests: list[HarvestResult] = []
        pollen_by_plot = pollen_by_plot or {}

        for i, plot in enumerate(self.plots):
            p = plot.plant
            will_harvest = (
                p is not None
                and p.age_seasons >= p.mature_after - 1
                and p.mature_after > 0
            )
            w_mult, n_mult = (1.0, 1.0)
            if p is not None:
                w_mult, n_mult = resource_draw_multipliers(p)
            plot.soil.advance_season(
                rng,
                plot_occupied=p is not None,
                harvested_this_season=will_harvest,
                water_uptake_mult=w_mult,
                nutrient_uptake_mult=n_mult,
            )
            if p is None:
                continue
            p.tick_season()
            if not p.is_mature:
                continue
            traits = p.expressed_traits(rules)
            pollen = pollen_by_plot.get(i, p.scion_genome)
            seeds: list[Seed] = []
            for _ in range(seeds_per_harvest):
                child = cross_parents(p.scion_genome, pollen, rng)
                child = mutate(child, rng, mutation_rate)
                seeds.append(Seed(species_id=p.scion_species.id, genome=child))
            harvests.append(
                HarvestResult(
                    species_id=p.scion_species.id,
                    traits_snapshot=traits,
                    seeds=seeds,
                )
            )
        return harvests
