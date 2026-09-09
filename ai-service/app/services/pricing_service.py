"""
Pricing Recommendation Service — Gate 10.

Calculates transparent, deterministic, and explainable pricing recommendations
for artisan handicraft products using a hybrid cost-plus + market-range system.

Per 10_GATE_PRICING_ENGINE.md:
- Does NOT pretend to have a sophisticated ML pricing model without historical data.
- Exact Calculation:
    production_cost = raw_material_cost + labour_cost + packaging_cost + other_cost
    base_price = production_cost * margin_multiplier
- Clamps / adjusts against available benchmark market ranges.
- Returns: recommended, minimum, maximum, currency, explanation.
"""

import logging
from typing import Dict, Optional, Tuple

from app.models.pricing import PricingBreakdown, PricingResult

logger = logging.getLogger("artisan_ai_service.pricing")

# Market benchmark ranges (min, avg, max) in INR by category/material
MARKET_BENCHMARKS: Dict[str, Tuple[float, float, float]] = {
    # format: (market_min, market_avg, market_max)
    "bamboo": (350.0, 750.0, 1500.0),
    "cane": (400.0, 800.0, 1600.0),
    "clay": (150.0, 450.0, 1200.0),
    "terracotta": (200.0, 500.0, 1400.0),
    "pottery": (250.0, 600.0, 1800.0),
    "wood": (500.0, 1200.0, 3000.0),
    "woodcarving": (600.0, 1500.0, 3500.0),
    "silk": (1200.0, 2800.0, 6500.0),
    "cotton": (400.0, 950.0, 2200.0),
    "textiles": (450.0, 1100.0, 2500.0),
    "brass": (800.0, 2000.0, 5000.0),
    "metal": (700.0, 1800.0, 4500.0),
    "leather": (600.0, 1400.0, 3200.0),
    "jewelry": (300.0, 900.0, 2500.0),
    "default": (300.0, 750.0, 1800.0),
}


def _get_market_range(category: Optional[str], material: Optional[str]) -> Tuple[float, float, float]:
    """Retrieve market benchmark (min, avg, max) based on material or category."""
    keys = []
    if material:
        keys.append(material.strip().lower())
    if category:
        keys.append(category.strip().lower())

    for k in keys:
        for benchmark_key, bench_range in MARKET_BENCHMARKS.items():
            if benchmark_key in k:
                return bench_range

    return MARKET_BENCHMARKS["default"]


def calculate_price_recommendation(
    raw_material_cost: float,
    labour_cost: float,
    packaging_cost: float = 0.0,
    other_cost: float = 0.0,
    category: Optional[str] = None,
    material: Optional[str] = None,
    quality: Optional[str] = "standard",
    demand: Optional[str] = "medium",
    margin_multiplier: Optional[float] = 1.35,
) -> PricingResult:
    """
    Calculate an explainable, deterministic price recommendation.

    Args:
        raw_material_cost: Direct cost of materials.
        labour_cost: Artisan labour cost.
        packaging_cost: Packaging materials cost.
        other_cost: Miscellaneous overhead.
        category: Broad category (e.g. Handicrafts).
        material: Primary material (e.g. Bamboo).
        quality: Artisan quality ('standard', 'high', 'premium').
        demand: Market demand level ('low', 'medium', 'high').
        margin_multiplier: Target profit markup (default 1.35).

    Returns:
        PricingResult with recommended, minimum, maximum, currency, explanation, and breakdown.
    """
    if raw_material_cost < 0 or labour_cost < 0 or packaging_cost < 0 or other_cost < 0:
        raise ValueError("Cost values cannot be negative.")

    production_cost = round(raw_material_cost + labour_cost + packaging_cost + other_cost, 2)
    if production_cost <= 0:
        raise ValueError("Total production cost must be greater than zero.")

    margin = margin_multiplier if (margin_multiplier and margin_multiplier >= 1.0) else 1.35
    base_price = round(production_cost * margin, 2)

    # Quality adjustment
    q_norm = (quality or "standard").strip().lower()
    if q_norm == "premium":
        quality_factor = 0.15
    elif q_norm == "high":
        quality_factor = 0.10
    else:
        quality_factor = 0.0
    quality_adj = round(base_price * quality_factor, 2)

    # Demand adjustment
    d_norm = (demand or "medium").strip().lower()
    if d_norm == "high":
        demand_factor = 0.10
    elif d_norm == "low":
        demand_factor = -0.05
    else:
        demand_factor = 0.0
    demand_adj = round(base_price * demand_factor, 2)

    calculated_recommendation = round(base_price + quality_adj + demand_adj, 2)

    # Market range comparison & clamping
    m_min, m_avg, m_max = _get_market_range(category, material)

    # Ensure minimum covers production cost + at least 15% margin
    min_cost_floor = round(production_cost * 1.15, 2)
    suggested_min = max(min_cost_floor, round(calculated_recommendation * 0.88, 2))

    # Recommended price clamped sensibly
    # If production cost is higher than market average, maintain artisan margin
    final_recommended = max(calculated_recommendation, min_cost_floor)

    # Maximum price offers room for retail/festival peaks
    suggested_max = max(round(final_recommended * 1.25, 2), round(m_max, 2))

    # Round to attractive marketplace integers (.99 or clean round numbers)
    rec_int = round(final_recommended)
    min_int = round(suggested_min)
    max_int = round(suggested_max)

    # Generate transparent explanation
    explanation = (
        f"Production cost is calculated at ₹{production_cost:g} (Materials: ₹{raw_material_cost:g}, "
        f"Labour: ₹{labour_cost:g}, Packaging: ₹{packaging_cost:g}, Overhead: ₹{other_cost:g}). "
        f"Applying a {int((margin - 1.0) * 100)}% base markup yields ₹{base_price:g}. "
        f"Adjustments: quality '{quality}' ({'+' if quality_adj >= 0 else ''}₹{quality_adj:g}), "
        f"demand '{demand}' ({'+' if demand_adj >= 0 else ''}₹{demand_adj:g}). "
        f"Benchmarked against category/material market range (₹{int(m_min)}–₹{int(m_max)}). "
        f"Recommended selling price is ₹{rec_int}, with a fair range of ₹{min_int} to ₹{max_int}."
    )

    breakdown = PricingBreakdown(
        raw_material_cost=raw_material_cost,
        labour_cost=labour_cost,
        packaging_cost=packaging_cost,
        other_cost=other_cost,
        production_cost=production_cost,
        base_price=base_price,
        quality_adjustment=quality_adj,
        demand_adjustment=demand_adj,
    )

    return PricingResult(
        recommended=float(rec_int),
        minimum=float(min_int),
        maximum=float(max_int),
        currency="INR",
        explanation=explanation,
        breakdown=breakdown,
    )
