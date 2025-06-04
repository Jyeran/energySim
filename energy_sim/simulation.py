import numpy as np
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class GridTier:
    threshold: float  # cumulative kWh threshold for this tier
    price: float      # price per kWh for energy above the threshold

def tiered_pricing(consumption: float, tiers: List[GridTier]) -> float:
    """Calculate cost of grid consumption based on tiered pricing."""
    tiers = sorted(tiers, key=lambda t: t.threshold)
    cost = 0.0
    remaining = consumption
    last_threshold = 0.0
    for tier in tiers:
        if remaining <= 0:
            break
        tier_amount = min(remaining, tier.threshold - last_threshold)
        if tier_amount > 0:
            cost += tier_amount * tier.price
            remaining -= tier_amount
        last_threshold = tier.threshold
    if remaining > 0:
        cost += remaining * tiers[-1].price
    return cost

def simulate_day(
    usage: np.ndarray,
    solar: np.ndarray,
    battery_capacity: float,
    tiers: List[GridTier],
    battery_efficiency: float = 0.9,
    initial_charge: float = 0.0,
) -> dict:
    """Simulate one day of energy flows."""
    hours = len(usage)
    charge = initial_charge
    battery_level = np.zeros(hours)
    solar_used = np.zeros(hours)
    battery_used = np.zeros(hours)
    grid_used = np.zeros(hours)

    for i in range(hours):
        demand = usage[i]
        solar_gen = solar[i]

        if solar_gen >= demand:
            solar_used[i] = demand
            surplus = solar_gen - demand
            charge += surplus * battery_efficiency
            if charge > battery_capacity:
                charge = battery_capacity
        else:
            solar_used[i] = solar_gen
            deficit = demand - solar_gen
            supply_from_battery = min(charge, deficit)
            battery_used[i] = supply_from_battery
            charge -= supply_from_battery
            grid_used[i] = deficit - supply_from_battery
        battery_level[i] = charge

    total_grid = grid_used.sum()
    cost = tiered_pricing(total_grid, tiers)

    return {
        "solar_used": solar_used,
        "battery_used": battery_used,
        "grid_used": grid_used,
        "battery_level": battery_level,
        "total_grid": total_grid,
        "cost": cost,
    }
