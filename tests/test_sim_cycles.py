"""Integration tests: several seasons of orchard + soil + graft + breeding."""

from __future__ import annotations

import random
import unittest

from sim import (
    FieldPlot,
    Orchard,
    LifecycleStage,
    current_lifecycle_stage,
    default_phenotype_rules,
    genome_for_breed,
    graft_compatible,
    species_by_id,
    starter_genome,
)
from sim.genetics import cross_parents, mutate
from sim.graft import GraftedPlant
from sim.soil import PlotSoil, random_plot_soil


def _assert_soil_invariants(self: unittest.TestCase, soil: PlotSoil) -> None:
    self.assertGreaterEqual(soil.nutrient_index, 0.0)
    self.assertLessEqual(soil.nutrient_index, 1.0)
    self.assertGreaterEqual(soil.water_saturation, 0.0)
    self.assertLessEqual(soil.water_saturation, 1.0)
    self.assertGreaterEqual(soil.organic_matter, 0.0)
    self.assertLessEqual(soil.organic_matter, 1.0)
    self.assertGreaterEqual(soil.drainage, 0.0)
    self.assertLessEqual(soil.drainage, 1.0)
    self.assertGreaterEqual(soil.compaction, 0.0)
    self.assertLessEqual(soil.compaction, 1.0)
    self.assertGreaterEqual(soil.ph, 4.8)
    self.assertLessEqual(soil.ph, 8.2)


class TestOrchardCycles(unittest.TestCase):
    def test_multi_season_runs_and_soil_stays_in_bounds(self) -> None:
        rng = random.Random(7)
        rules = default_phenotype_rules()
        pear = species_by_id()["pyrus_communis"]
        plots = [
            FieldPlot(soil=random_plot_soil(rng)),
            FieldPlot(soil=random_plot_soil(rng)),
        ]
        plots[0].plant_graft_from_breed("apple_spur_type", pear)
        plots[1].plant_graft_from_breed("apple_standard", pear)
        orchard = Orchard(plots=plots)

        all_harvests: list = []
        for _ in range(10):
            h = orchard.run_season(
                rng,
                rules,
                seeds_per_harvest=2,
                mutation_rate=0.02,
            )
            all_harvests.extend(h)
            for p in plots:
                _assert_soil_invariants(self, p.soil)

        self.assertEqual(orchard.season, 10)
        # First mature harvest after 2 seasons; then both plots each season.
        self.assertGreaterEqual(len(all_harvests), 12)
        for result in all_harvests:
            self.assertEqual(result.species_id, "malus_domestica")
            self.assertIn("leaf", result.traits_snapshot)
            self.assertIn("shaft", result.traits_snapshot)
            self.assertEqual(len(result.seeds), 2)

    def test_harvest_only_when_mature_then_replant_from_seed(self) -> None:
        rng = random.Random(99)
        rules = default_phenotype_rules()
        # Solanaceae rootstock for tomato scion (pear would be incompatible).
        eggplant_stock = species_by_id()["solanum_melongena"]
        plot = FieldPlot(soil=random_plot_soil(rng))
        plot.plant_graft_from_breed("tomato_indeterminate", eggplant_stock)
        orchard = Orchard(plots=[plot])

        h1 = orchard.run_season(rng, rules, seeds_per_harvest=1)
        self.assertEqual(h1, [])
        h2 = orchard.run_season(rng, rules, seeds_per_harvest=1)
        self.assertEqual(len(h2), 1)
        seed = h2[0].seeds[0]
        self.assertEqual(seed.species_id, "solanum_lycopersicum")
        self.assertIn("leaf", seed.genome.loci)

        plot.plant = None
        plot.plant_seed(seed, eggplant_stock, rng)
        h3 = orchard.run_season(rng, rules, seeds_per_harvest=1)
        self.assertEqual(h3, [])
        h4 = orchard.run_season(rng, rules, seeds_per_harvest=1)
        self.assertEqual(len(h4), 1)

    def test_incompatible_graft_raises(self) -> None:
        apple = species_by_id()["malus_domestica"]
        tomato = species_by_id()["solanum_lycopersicum"]
        self.assertFalse(graft_compatible(apple, tomato))
        with self.assertRaises(ValueError):
            GraftedPlant(
                scion_species=apple,
                rootstock_species=tomato,
                scion_genome=starter_genome(apple.id),
                rootstock_genome=starter_genome(tomato.id),
            )

    def test_genetics_cross_and_mutate_roundtrip(self) -> None:
        rng = random.Random(3)
        a = genome_for_breed("pepper_compact")
        b = genome_for_breed("eggplant_open")
        child = cross_parents(a, b, rng)
        child = mutate(child, rng, 0.05)
        self.assertTrue(set(child.loci.keys()))
        for _ in range(20):
            child = mutate(child, rng, 0.1)
            for _name, pair in child.loci.items():
                self.assertEqual(len(pair), 2)


class TestLifecycleStages(unittest.TestCase):
    def test_graft_apple_stages_default_mature_after_2(self) -> None:
        pear = species_by_id()["pyrus_communis"]
        plot = FieldPlot()
        plot.plant_graft_from_breed("apple_standard", pear)
        p = plot.plant
        assert p is not None
        self.assertFalse(p.started_from_seed)
        self.assertEqual(current_lifecycle_stage(p), LifecycleStage.GRAFT_ESTABLISHING)
        p.tick_season()
        self.assertEqual(current_lifecycle_stage(p), LifecycleStage.FLOWERING)
        p.tick_season()
        self.assertEqual(current_lifecycle_stage(p), LifecycleStage.PRODUCTIVE)
        self.assertEqual(p.seasons_productive, 1)

    def test_seed_replant_uses_germination_then_productive(self) -> None:
        rng = random.Random(0)
        egg = species_by_id()["solanum_melongena"]
        plot = FieldPlot()
        plot.plant_graft_from_breed("tomato_indeterminate", egg)
        orchard = Orchard(plots=[plot])
        rules = default_phenotype_rules()
        orchard.run_season(rng, rules, seeds_per_harvest=1)
        h2 = orchard.run_season(rng, rules, seeds_per_harvest=1)
        self.assertEqual(len(h2), 1)
        seed = h2[0].seeds[0]
        plot.plant = None
        plot.plant_seed(seed, egg, rng)
        s = plot.plant
        assert s is not None
        self.assertTrue(s.started_from_seed)
        self.assertEqual(current_lifecycle_stage(s), LifecycleStage.GERMINATION)
        s.tick_season()
        self.assertEqual(current_lifecycle_stage(s), LifecycleStage.SEEDLING)
        s.tick_season()
        self.assertEqual(current_lifecycle_stage(s), LifecycleStage.PRODUCTIVE)


if __name__ == "__main__":
    unittest.main()
