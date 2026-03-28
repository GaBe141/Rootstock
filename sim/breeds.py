"""Named breeds (cultivars): same species, different morphological and quality alleles."""

from __future__ import annotations

from dataclasses import dataclass

from sim.genetics import Genome
from sim.species import starter_genome as species_starter_genome


@dataclass(frozen=True)
class Breed:
    id: str
    species_id: str
    label: str
    # Partial diploid loci; merged on top of species baseline.
    loci: dict[str, tuple[str, str]]


def default_breeds() -> list[Breed]:
    return [
        Breed(
            id="apple_spur_type",
            species_id="malus_domestica",
            label="Spur-type apple",
            loci={
                "shaft": ("short", "short"),
                "leaf": ("broad", "broad"),
                "root_spread": ("med", "narrow"),
            },
        ),
        Breed(
            id="apple_standard",
            species_id="malus_domestica",
            label="Standard vigor apple",
            loci={
                "shaft": ("tall", "tall"),
                "leaf": ("oval", "broad"),
                "root_spread": ("med", "wide"),
            },
        ),
        Breed(
            id="pear_dwarf_tree",
            species_id="pyrus_communis",
            label="Compact pear",
            loci={
                "shaft": ("short", "med"),
                "leaf": ("oval", "oval"),
                "root_spread": ("wide", "med"),
            },
        ),
        Breed(
            id="tomato_indeterminate",
            species_id="solanum_lycopersicum",
            label="Indeterminate tomato",
            loci={
                "shaft": ("tall", "tall"),
                "leaf": ("compound", "compound"),
                "root_spread": ("narrow", "med"),
            },
        ),
        Breed(
            id="tomato_determinate",
            species_id="solanum_lycopersicum",
            label="Determinate tomato",
            loci={
                "shaft": ("med", "short"),
                "leaf": ("compound", "broad"),
                "root_spread": ("fibrous", "narrow"),
            },
        ),
        Breed(
            id="pepper_compact",
            species_id="capsicum_annuum",
            label="Compact pepper",
            loci={
                "shaft": ("short", "med"),
                "leaf": ("narrow", "narrow"),
                "root_spread": ("narrow", "narrow"),
            },
        ),
        Breed(
            id="eggplant_open",
            species_id="solanum_melongena",
            label="Open habit eggplant",
            loci={
                "shaft": ("tall", "med"),
                "leaf": ("broad", "broad"),
                "root_spread": ("wide", "med"),
            },
        ),
    ]


def breeds_by_id() -> dict[str, Breed]:
    return {b.id: b for b in default_breeds()}


def genome_for_breed(breed_id: str) -> Genome:
    b = breeds_by_id()[breed_id]
    merged = dict(species_starter_genome(b.species_id).loci)
    merged.update(b.loci)
    return Genome(merged)
