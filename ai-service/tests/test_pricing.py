"""
Gate 10 tests — Pricing Recommendation Service & Endpoint.

Per 10_GATE_PRICING_ENGINE.md acceptance criteria:
- Same inputs produce deterministic, explainable recommendations.
- Never presents fabricated market data as real.
- Production cost = raw_material + labour + packaging + other.
- Base price = production_cost * margin_multiplier.
- Explanations are transparent, detailing costs, adjustments, and market range.
- Endpoint POST /ai/recommend-price: negative costs -> 422, zero production cost -> 400, valid payload -> 200.
"""

import pytest
from app.models.pricing import PricingRequest, PricingResult
from app.services.pricing_service import calculate_price_recommendation

try:
    from fastapi.testclient import TestClient
    from app.main import app

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


# ---------------------------------------------------------------------------
# Schema and Model Validation Tests
# ---------------------------------------------------------------------------


def test_pricing_request_valid():
    req = PricingRequest(
        raw_material_cost=300.0,
        labour_cost=250.0,
        packaging_cost=50.0,
        other_cost=20.0,
        category="Handicrafts",
        material="Bamboo",
        quality="high",
        demand="medium",
    )
    assert req.raw_material_cost == 300.0
    assert req.labour_cost == 250.0
    assert req.packaging_cost == 50.0
    assert req.other_cost == 20.0
    assert req.category == "Handicrafts"


def test_pricing_result_model():
    res = PricingResult(
        recommended=799.0,
        minimum=700.0,
        maximum=950.0,
        currency="INR",
        explanation="Cost covers raw materials and labour.",
    )
    assert res.recommended == 799.0
    assert res.minimum == 700.0
    assert res.maximum == 950.0
    assert res.currency == "INR"


# ---------------------------------------------------------------------------
# Calculation and Service Tests
# ---------------------------------------------------------------------------


def test_calculate_price_recommendation_exact_math():
    """Verify exact formula: production_cost = sum(costs), base = production_cost * margin."""
    res = calculate_price_recommendation(
        raw_material_cost=300.0,
        labour_cost=250.0,
        packaging_cost=50.0,
        other_cost=0.0,
        margin_multiplier=1.25,
        quality="standard",
        demand="medium",
    )
    assert res.breakdown is not None
    assert res.breakdown.production_cost == 600.0
    assert res.breakdown.base_price == 750.0
    # Minimum must cover production cost + safety buffer
    assert res.minimum >= 600.0
    assert res.recommended >= res.minimum
    assert res.maximum >= res.recommended


def test_calculate_price_recommendation_deterministic():
    """Same inputs must always produce the exact same deterministic results."""
    run1 = calculate_price_recommendation(
        raw_material_cost=200.0,
        labour_cost=150.0,
        packaging_cost=30.0,
        material="Clay",
    )
    run2 = calculate_price_recommendation(
        raw_material_cost=200.0,
        labour_cost=150.0,
        packaging_cost=30.0,
        material="Clay",
    )
    assert run1.recommended == run2.recommended
    assert run1.minimum == run2.minimum
    assert run1.maximum == run2.maximum
    assert run1.explanation == run2.explanation


def test_calculate_price_recommendation_quality_and_demand_adjustments():
    """Higher quality and high demand adjust recommendations upwards."""
    base = calculate_price_recommendation(
        raw_material_cost=100.0,
        labour_cost=100.0,
        quality="standard",
        demand="medium",
    )
    premium = calculate_price_recommendation(
        raw_material_cost=100.0,
        labour_cost=100.0,
        quality="premium",
        demand="high",
    )
    assert premium.recommended > base.recommended
    assert premium.breakdown.quality_adjustment > 0
    assert premium.breakdown.demand_adjustment > 0


def test_calculate_price_negative_cost_raises_value_error():
    """Negative costs are rejected with ValueError."""
    with pytest.raises(ValueError, match="negative"):
        calculate_price_recommendation(raw_material_cost=-10.0, labour_cost=50.0)


def test_calculate_price_zero_production_cost_raises_value_error():
    """Zero total production cost raises ValueError."""
    with pytest.raises(ValueError, match="greater than zero"):
        calculate_price_recommendation(raw_material_cost=0.0, labour_cost=0.0)


def test_explanation_contains_required_elements():
    """Explanation details production cost, breakdown, and market range."""
    res = calculate_price_recommendation(
        raw_material_cost=300.0,
        labour_cost=250.0,
        packaging_cost=50.0,
        material="Bamboo",
    )
    assert "Production cost" in res.explanation
    assert "Materials: ₹300" in res.explanation
    assert "Labour: ₹250" in res.explanation
    assert "Recommended selling price" in res.explanation


# ---------------------------------------------------------------------------
# FastAPI Endpoint Tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="fastapi not installed")
class TestPricingEndpoint:
    def setup_method(self):
        self.client = TestClient(app)

    def test_endpoint_success_roundtrip(self):
        """POST /ai/recommend-price returns 200 with structured JSON."""
        payload = {
            "raw_material_cost": 300.0,
            "labour_cost": 250.0,
            "packaging_cost": 50.0,
            "other_cost": 50.0,
            "category": "Handicrafts",
            "material": "Bamboo",
            "quality": "high",
            "demand": "high",
        }
        res = self.client.post("/ai/recommend-price", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "recommended" in data
        assert "minimum" in data
        assert "maximum" in data
        assert "explanation" in data
        assert data["currency"] == "INR"
        assert data["recommended"] >= data["minimum"]

    def test_endpoint_rejects_negative_costs(self):
        """Rejects negative costs with HTTP 422 validation error."""
        payload = {
            "raw_material_cost": -50.0,
            "labour_cost": 100.0,
        }
        res = self.client.post("/ai/recommend-price", json=payload)
        assert res.status_code == 422

    def test_endpoint_rejects_zero_costs(self):
        """Rejects payload with 0 production cost with HTTP 400."""
        payload = {
            "raw_material_cost": 0.0,
            "labour_cost": 0.0,
            "packaging_cost": 0.0,
            "other_cost": 0.0,
        }
        res = self.client.post("/ai/recommend-price", json=payload)
        assert res.status_code == 400
        assert "greater than zero" in res.json()["detail"]
