"""Plant kinds, graft compatibility, and starter genomes."""

from __future__ import annotations

from dataclasses import dataclass

from sim.genetics import Genome, PhenotypeRules


@dataclass(frozen=True)
class Species:
    id: str
    family: str
    common_name: str
    # Scion families many rootstocks can accept (same family often OK; intergeneric is special).
    graft_families_accepted: frozenset[str]


def default_species() -> list[Species]:
    return [
        Species(
            id="malus_domestica",
            family="Rosaceae",
            common_name="Apple",
            graft_families_accepted=frozenset({"Rosaceae"}),
        ),
        Species(
            id="pyrus_communis",
            family="Rosaceae",
            common_name="Pear",
            graft_families_accepted=frozenset({"Rosaceae"}),
        ),
        Species(
            id="cydonia_oblonga",
            family="Rosaceae",
            common_name="Quince",
            graft_families_accepted=frozenset({"Rosaceae"}),
        ),
        Species(
            id="solanum_lycopersicum",
            family="Solanaceae",
            common_name="Tomato",
            graft_families_accepted=frozenset({"Solanaceae"}),
        ),
        Species(
            id="solanum_melongena",
            family="Solanaceae",
            common_name="Eggplant",
            graft_families_accepted=frozenset({"Solanaceae"}),
        ),
        Species(
            id="capsicum_annuum",
            family="Solanaceae",
            common_name="Pepper",
            graft_families_accepted=frozenset({"Solanaceae"}),
        ),
    ]


def species_by_id() -> dict[str, Species]:
    return {s.id: s for s in default_species()}


def starter_genome(species_id: str) -> Genome:
    """Baseline cultivar-like genomes; tweak per species flavor.

    Morphology loci (all diploid):
    - leaf: foliage habit — narrow, oval, broad, compound, needle_like
    - root_spread: below-ground spread — fibrous, narrow, med, wide
    - shaft: main stem / trunk height habit — short, med, tall
    """
    base = {
        "sugar": ("med", "med"),
        "acid": ("med", "med"),
        "vigor": ("med", "med"),
        "dwarf": ("no", "no"),
        "disease": ("res", "sus"),
        "leaf": ("oval", "oval"),
        "root_spread": ("med", "med"),
        "shaft": ("med", "med"),
    }
    if species_id.startswith("malus"):
        base = {
            **base,
            "sugar": ("high", "low"),
            "acid": ("high", "med"),
            "vigor": ("high", "med"),
            "leaf": ("broad", "oval"),
            "root_spread": ("med", "med"),
            "shaft": ("tall", "med"),
        }
    elif species_id.startswith("pyrus"):
        base = {
            **base,
            "sugar": ("high", "low"),
            "acid": ("high", "med"),
            "vigor": ("high", "med"),
            "leaf": ("oval", "broad"),
            "root_spread": ("wide", "med"),
            "shaft": ("tall", "tall"),
        }
    elif species_id.startswith("cydonia"):
        base = {
            **base,
            "sugar": ("med", "high"),
            "acid": ("high", "med"),
            "vigor": ("med", "med"),
            "leaf": ("broad", "broad"),
            "root_spread": ("wide", "wide"),
            "shaft": ("med", "short"),
        }
    elif species_id.startswith("solanum_lycopersicum"):
        base = {
            **base,
            "sugar": ("high", "high"),
            "acid": ("low", "med"),
            "vigor": ("med", "high"),
            "leaf": ("compound", "compound"),
            "root_spread": ("fibrous", "narrow"),
            "shaft": ("tall", "tall"),
        }
    elif species_id.startswith("solanum_melongena"):
        base = {
            **base,
            "sugar": ("med", "med"),
            "acid": ("low", "low"),
            "vigor": ("med", "med"),
            "leaf": ("broad", "oval"),
            "root_spread": ("med", "wide"),
            "shaft": ("med", "tall"),
        }
    elif species_id.startswith("capsicum"):
        base = {
            **base,
            "sugar": ("low", "med"),
            "acid": ("med", "high"),
            "vigor": ("med", "med"),
            "leaf": ("narrow", "oval"),
            "root_spread": ("narrow", "med"),
            "shaft": ("med", "med"),
        }
    return Genome(dict(base))


def default_phenotype_rules() -> PhenotypeRules:
    return PhenotypeRules(
        dominance={
            "sugar": "high",
            "acid": "high",
            "vigor": "high",
            "dwarf": "yes",
            "disease": "res",
            # Wider / taller alleles win when heterozygous (simple incomplete dominance proxy).
            "root_spread": "wide",
            "shaft": "tall",
            # Compound and broad leaves read as “larger” canopy vs narrow/needle.
            "leaf": "compound",
        }
    )


def graft_compatible(scion: Species, rootstock: Species) -> bool:
    return rootstock.family in scion.graft_families_accepted
