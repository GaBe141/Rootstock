"""Per-plot soil: generated attributes and simple seasonal water/nutrient dynamics."""

from __future__ import annotations

import random
from dataclasses import dataclass


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


@dataclass
class PlotSoil:
    """
    Single-horizon soil patch for one field plot.

    All traits are abstract 0–1 scales except pH (standard 1–14 scale).
    """

    # Overall available nutrients (NPK + minors rolled together).
    nutrient_index: float = 0.55
    # Soil reaction; ~6.0–7.0 is the “easy” band for many crops.
    ph: float = 6.5
    # Plant-available water in the rooted volume this season.
    water_saturation: float = 0.5
    # Organic matter fraction proxy (affects nutrient buffering / recharge).
    organic_matter: float = 0.35
    # High = water leaves the plot faster (sand / slope); low = holds water (clay / pan).
    drainage: float = 0.5
    # Mechanical resistance / aeration inverse (high = tight soil).
    compaction: float = 0.35

    def as_dict(self) -> dict[str, float]:
        return {
            "nutrient_index": round(self.nutrient_index, 3),
            "ph": round(self.ph, 2),
            "water_saturation": round(self.water_saturation, 3),
            "organic_matter": round(self.organic_matter, 3),
            "drainage": round(self.drainage, 3),
            "compaction": round(self.compaction, 3),
        }

    def advance_season(
        self,
        rng: random.Random,
        *,
        plot_occupied: bool,
        harvested_this_season: bool,
        water_uptake_mult: float = 1.0,
        nutrient_uptake_mult: float = 1.0,
    ) -> None:
        """Weather, drainage, and crop drawdown; light nutrient recharge from OM."""
        rain = rng.uniform(0.06, 0.28)
        evap = rng.uniform(0.04, 0.12)
        drain_loss = (0.04 + 0.14 * self.drainage) * self.water_saturation
        self.water_saturation = _clamp(
            self.water_saturation + rain - evap - drain_loss,
            0.0,
            1.0,
        )

        if plot_occupied:
            wu = max(0.0, water_uptake_mult)
            nu = max(0.0, nutrient_uptake_mult)
            uptake = (0.05 + 0.06 * (1.0 - self.compaction * 0.5)) * wu
            self.water_saturation = _clamp(self.water_saturation - uptake, 0.0, 1.0)
            self.nutrient_index = _clamp(
                self.nutrient_index - 0.035 * nu,
                0.0,
                1.0,
            )

        if harvested_this_season:
            self.nutrient_index = _clamp(self.nutrient_index - 0.025, 0.0, 1.0)

        recharge = 0.012 + 0.035 * self.organic_matter
        self.nutrient_index = _clamp(self.nutrient_index + recharge, 0.0, 1.0)

        # Very slow pH drift from OM decay / leaching (toy).
        ph_shift = rng.uniform(-0.04, 0.04) + (self.organic_matter - 0.35) * 0.02
        self.ph = _clamp(self.ph + ph_shift, 4.8, 8.2)


def default_plot_soil() -> PlotSoil:
    return PlotSoil()


def random_plot_soil(rng: random.Random) -> PlotSoil:
    """Independent draws with mild realism (acid/high-OM patches, sandy drains, etc.)."""
    organic = rng.uniform(0.12, 0.62)
    drainage = rng.uniform(0.15, 0.92)
    compaction = rng.uniform(0.15, 0.75)
    # Slightly acidic bias when OM is high (toy correlation).
    ph = rng.uniform(5.6, 7.9) - (organic - 0.35) * 0.35
    ph = _clamp(ph, 4.8, 8.2)
    nutrients = rng.uniform(0.25, 0.92)
    # Wet climates / tight soil hold more starting water.
    water = rng.uniform(0.2, 0.85) * (1.0 - drainage * 0.25) + (1.0 - compaction) * 0.08
    water = _clamp(water, 0.1, 0.95)
    return PlotSoil(
        nutrient_index=nutrients,
        ph=ph,
        water_saturation=water,
        organic_matter=organic,
        drainage=drainage,
        compaction=compaction,
    )


def random_plots_soil(count: int, rng: random.Random) -> list[PlotSoil]:
    return [random_plot_soil(rng) for _ in range(count)]
