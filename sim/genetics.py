"""Trait genomes, crossing, and light mutation for breeding simulations."""

from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Genome:
    """Diploid string alleles per locus name (e.g. sugar: ('high','low'))."""

    loci: dict[str, tuple[str, str]]

    def gamete(self, rng: random.Random) -> dict[str, str]:
        """One allele per locus, chosen at random from each pair."""
        return {name: rng.choice(pair) for name, pair in self.loci.items()}

    def with_locus(self, name: str, a1: str, a2: str) -> Genome:
        n = dict(self.loci)
        n[name] = (a1, a2)
        return Genome(n)


def cross_parents(
    mother: Genome,
    father: Genome,
    rng: random.Random,
    *,
    crossover_rate: float = 0.15,
) -> Genome:
    """
    Build offspring: for each locus, take one random allele from each parent's gamete.
    Optionally swap entire haplotype blocks between loci (ordered by key) to mimic crossover.
    """
    keys = sorted(set(mother.loci) | set(father.loci))
    if not keys:
        return Genome({})

    # Haplotype 0 vs 1: which side of the diploid pair each gamete drew from (simplified).
    m_gam = mother.gamete(rng)
    f_gam = father.gamete(rng)

    child_loci: dict[str, tuple[str, str]] = {}
    use_maternal_first = rng.random() < 0.5

    for i, key in enumerate(keys):
        if rng.random() < crossover_rate:
            use_maternal_first = not use_maternal_first
        mp = mother.loci.get(key, ("?", "?"))
        fp = father.loci.get(key, ("?", "?"))
        m_allele = m_gam.get(key, rng.choice(mp))
        f_allele = f_gam.get(key, rng.choice(fp))
        if use_maternal_first:
            child_loci[key] = (m_allele, f_allele)
        else:
            child_loci[key] = (f_allele, m_allele)

    return Genome(child_loci)


def mutate(genome: Genome, rng: random.Random, rate: float = 0.02) -> Genome:
    """Per-locus small chance to replace one allele with a random variant."""
    if rate <= 0:
        return genome
    alleles_by_locus: dict[str, set[str]] = {}
    for name, pair in genome.loci.items():
        alleles_by_locus.setdefault(name, set()).update(pair)

    new_loci = {}
    for name, (a1, a2) in genome.loci.items():
        pool = list(alleles_by_locus.get(name, {a1, a2}))
        if len(pool) < 2:
            pool = [a1, a2, "mut"]
        na1, na2 = a1, a2
        if rng.random() < rate:
            na1 = rng.choice(pool)
        if rng.random() < rate:
            na2 = rng.choice(pool)
        new_loci[name] = (na1, na2)
    return Genome(new_loci)


@dataclass
class PhenotypeRules:
    """Maps locus -> dominant allele wins for simple display traits."""

    dominance: dict[str, str] = field(default_factory=dict)

    def express(self, genome: Genome) -> dict[str, str]:
        out: dict[str, str] = {}
        for name, (x, y) in genome.loci.items():
            dom = self.dominance.get(name)
            if dom:
                if x == dom:
                    out[name] = x
                elif y == dom:
                    out[name] = y
                else:
                    out[name] = x if x >= y else y  # stable tie-break
            else:
                out[name] = x if x == y else f"{x}/{y}"
        return out
