"""Grafted individuals: scion genetics for fruit/seed, rootstock for below-ground traits."""

from __future__ import annotations

from dataclasses import dataclass

from sim.genetics import Genome, PhenotypeRules
from sim.species import Species, graft_compatible


@dataclass
class GraftedPlant:
    scion_species: Species
    rootstock_species: Species
    scion_genome: Genome
    rootstock_genome: Genome
    age_seasons: int = 0
    mature_after: int = 2
    # True if raised from seed onto rootstock (longer early lifecycle).
    started_from_seed: bool = False
    # Count of mature seasons completed (increments each tick while mature).
    seasons_productive: int = 0

    def __post_init__(self) -> None:
        if not graft_compatible(self.scion_species, self.rootstock_species):
            raise ValueError(
                f"Incompatible graft: scion {self.scion_species.id} on "
                f"rootstock {self.rootstock_species.id}"
            )

    @property
    def is_mature(self) -> bool:
        return self.age_seasons >= self.mature_after

    def expressed_traits(self, rules: PhenotypeRules) -> dict[str, str]:
        """Scion drives canopy/fruit/shaft genes; rootstock drives roots and dwarfing."""
        s = rules.express(self.scion_genome)
        r = rules.express(self.rootstock_genome)
        merged = dict(s)
        merged["vigor"] = r.get("vigor", merged.get("vigor", ""))
        merged["dwarf"] = r.get("dwarf", merged.get("dwarf", ""))
        merged["disease"] = r.get("disease", merged.get("disease", ""))
        merged["leaf"] = s.get("leaf", "")
        merged["root_spread"] = r.get("root_spread", s.get("root_spread", ""))
        merged["shaft"] = _shaft_with_dwarfing(
            s.get("shaft", ""),
            merged.get("dwarf", ""),
        )
        return merged

    def tick_season(self) -> None:
        self.age_seasons += 1
        if self.age_seasons >= self.mature_after:
            self.seasons_productive += 1


_SHAFT_ORDER = ("short", "med", "tall")


def _shaft_with_dwarfing(shaft: str, dwarf: str) -> str:
    if dwarf != "yes":
        return shaft
    try:
        i = _SHAFT_ORDER.index(shaft)
    except ValueError:
        return shaft
    return _SHAFT_ORDER[max(0, i - 1)]
