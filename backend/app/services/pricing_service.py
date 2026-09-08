import logging
from typing import Optional, Dict, Any
from app.config import (
    ARTISAN_MARGIN_PERCENT,
    DEFAULT_MARKET_ADJUSTMENT,
    DEFAULT_DEMAND_ADJUSTMENT,
)

logger = logging.getLogger("artisan.pricing_service")


class PricingService:
    """Explainable pricing engine for handcrafted artisan products.
    
    Architecture Note / Future ML Compatibility:
    -------------------------------------------
    TODO(future-ml): The current hybrid rule-based calculation can be seamlessly
    swapped with a trained machine learning model (e.g. XGBoost / Neural Pricing Model)
    by implementing an MLPricingModel interface that ingests:
      - Product category & craft material embeddings
      - Historical transaction & seasonal demand data
      - Competitor pricing & geo-location elasticity
    and returns predicted optimal price bands.
    """

    def __init__(
        self,
        default_margin_percent: float = ARTISAN_MARGIN_PERCENT,
        default_market_adj: float = DEFAULT_MARKET_ADJUSTMENT,
        default_demand_adj: float = DEFAULT_DEMAND_ADJUSTMENT,
    ):
        self.default_margin_percent = default_margin_percent
        self.default_market_adj = default_market_adj
        self.default_demand_adj = default_demand_adj

    def calculate_price(
        self,
        raw_material_cost: float,
        labour_cost: float,
        packaging_cost: float,
        market_adjustment: Optional[float] = None,
        demand_adjustment: Optional[float] = None,
        margin_percent: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Compute recommended price, minimum price, maximum price, and an explainable reason."""
        # 1. Validation & Base cost calculation
        raw = max(0.0, float(raw_material_cost or 0.0))
        labour = max(0.0, float(labour_cost or 0.0))
        pkg = max(0.0, float(packaging_cost or 0.0))
        base_cost = raw + labour + pkg

        margin_pct = (
            margin_percent
            if margin_percent is not None
            else self.default_margin_percent
        )
        mkt_adj = (
            market_adjustment
            if market_adjustment is not None
            else self.default_market_adj
        )
        dmd_adj = (
            demand_adjustment
            if demand_adjustment is not None
            else self.default_demand_adj
        )

        # 2. Margin and Recommended price calculation
        artisan_margin = base_cost * (margin_pct / 100.0)
        raw_recommended = base_cost + mkt_adj + dmd_adj + artisan_margin
        recommended_price = float(round(max(base_cost, raw_recommended)))

        # 3. Price Range (Minimum and Maximum)
        # Minimum price covers at least 100% of base cost
        if recommended_price > 0:
            minimum_price = float(round(max(base_cost, recommended_price * 0.85)))
            maximum_price = float(round(max(recommended_price, recommended_price * 1.25)))
        else:
            minimum_price = 0.0
            maximum_price = 0.0

        # Ensure strict invariant: min <= rec <= max
        minimum_price = min(minimum_price, recommended_price)
        maximum_price = max(maximum_price, recommended_price)

        # 4. Construct explainable reasoning
        parts = []
        if raw > 0:
            parts.append(f"materials (₹{int(raw)})")
        if labour > 0:
            parts.append(f"artisan labour (₹{int(labour)})")
        if pkg > 0:
            parts.append(f"packaging (₹{int(pkg)})")

        cost_breakdown_str = " + ".join(parts) if parts else "zero recorded base costs"
        reason = (
            f"Calculated from {cost_breakdown_str} with a {int(margin_pct)}% artisan profit margin"
        )
        if mkt_adj != 0 or dmd_adj != 0:
            reason += f" and market/demand adjustments (₹{int(mkt_adj + dmd_adj)})"
        reason += "."

        return {
            "recommended_price": recommended_price,
            "minimum_price": minimum_price,
            "maximum_price": maximum_price,
            "reason": reason,
        }


# Global singleton instance
pricing_service = PricingService()
