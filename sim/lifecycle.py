"""Lifecycle stages from planting through recurring production."""

from __future__ import annotations

from enum import Enum

from sim.graft import GraftedPlant


class LifecycleStage(str, Enum):
    """Coarse stages; driven by seasons-since-planting and mature_after."""

    GERMINATION = "germination"
    SEEDLING = "seedling"
    GRAFT_ESTABLISHING = "graft_establishing"
    VEGETATIVE = "vegetative"
    FLOWERING = "flowering"  # pre–first-harvest: fruit set / ripening window
    PRODUCTIVE = "productive"  # mature: harvestable each eligible season


def current_lifecycle_stage(plant: GraftedPlant) -> LifecycleStage:
    """
    Stage after `plant.age_seasons` full seasons (0 = newly planted, no tick yet).

    Juvenile band splits differ for seed-grown vs bench-grafted stock.
    """
    a = plant.age_seasons
    m = plant.mature_after
    if m <= 0 or a >= m:
        return LifecycleStage.PRODUCTIVE

    if plant.started_from_seed:
        n1 = max(1, (m + 2) // 3)
        n2 = max(n1 + 1, (2 * m + 2) // 3)
        if a < n1:
            return LifecycleStage.GERMINATION
        if a < n2:
            return LifecycleStage.SEEDLING
        if a >= m - 1:
            return LifecycleStage.FLOWERING
        return LifecycleStage.VEGETATIVE

    if a == 0:
        return LifecycleStage.GRAFT_ESTABLISHING
    if m <= 2:
        return LifecycleStage.FLOWERING if a == m - 1 else LifecycleStage.VEGETATIVE
    if a >= m - 1:
        return LifecycleStage.FLOWERING
    return LifecycleStage.VEGETATIVE


def stage_label(plant: GraftedPlant) -> str:
    st = current_lifecycle_stage(plant)
    if st is LifecycleStage.PRODUCTIVE and plant.seasons_productive > 0:
        return f"{st.value} (yr {plant.seasons_productive} cropping)"
    return st.value.replace("_", " ")


# Water and nutrient draw multipliers vs baseline occupied plot.
_STAGE_DRAW: dict[LifecycleStage, tuple[float, float]] = {
    LifecycleStage.GERMINATION: (0.38, 0.42),
    LifecycleStage.SEEDLING: (0.58, 0.58),
    LifecycleStage.GRAFT_ESTABLISHING: (0.52, 0.48),
    LifecycleStage.VEGETATIVE: (1.0, 1.0),
    LifecycleStage.FLOWERING: (1.14, 1.2),
    LifecycleStage.PRODUCTIVE: (1.08, 1.12),
}


def resource_draw_multipliers(plant: GraftedPlant) -> tuple[float, float]:
    """(water_mult, nutrient_mult) for soil uptake this season."""
    st = current_lifecycle_stage(plant)
    return _STAGE_DRAW.get(st, (1.0, 1.0))
