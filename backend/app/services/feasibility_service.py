"""
Order Feasibility Engine Service.

Pure deterministic math + AI-enhanced recommendation.
Parses buyer order details from enquiry message and calculates
whether the artisan can fulfill the order given their capacity constraints.
"""
import re
import logging
import os
import json
from typing import Tuple, Optional

logger = logging.getLogger("artisan.feasibility")

# ─── Parse Buyer Order From Message ───────────────────────────────────────────

def _parse_order_requirements(message: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Extract (quantity, days) from a free-text buyer enquiry message.
    e.g. "Can you supply 500 bags in 15 days?" → (500, 15)
    """
    # Match quantity — looks for numbers followed by unit keywords
    qty_patterns = [
        r"(\d[\d,]*)\s*(?:units?|pieces?|pcs|bags?|items?|qty|quantity)",
        r"(?:supply|deliver|order|want|need|require)[^\d]*(\d[\d,]*)",
        r"(\d[\d,]*)\s*(?:handcraft|handmade|artisan)",
    ]
    quantity = None
    for pat in qty_patterns:
        m = re.search(pat, message, re.IGNORECASE)
        if m:
            quantity = int(m.group(1).replace(",", ""))
            break

    # Match days / deadline
    day_patterns = [
        r"(\d+)\s*days?",
        r"within\s+(\d+)\s*days?",
        r"in\s+(\d+)\s*days?",
        r"by\s+(\d+)\s*days?",
    ]
    days = None
    for pat in day_patterns:
        m = re.search(pat, message, re.IGNORECASE)
        if m:
            days = int(m.group(1))
            break

    return quantity, days


# ─── Core Feasibility Math ─────────────────────────────────────────────────────

def calculate_feasibility(
    enquiry_message: str,
    current_inventory: int,
    monthly_capacity: int,
    num_workers: int,
    raw_material_availability_pct: float,
) -> dict:
    """
    Core feasibility engine.

    Returns a FeasibilityResponse-compatible dict.
    """
    quantity, deadline_days = _parse_order_requirements(enquiry_message)

    # If we could not parse, try generic assumptions
    if quantity is None:
        quantity = 100
    if deadline_days is None:
        deadline_days = 30

    # ── Calculation ──────────────────────────────────────────────────────────
    # Workers scale capacity linearly (base capacity assumed for 1 worker)
    worker_scaled_capacity = monthly_capacity * num_workers
    # Raw material availability throttles production rate
    effective_capacity = worker_scaled_capacity * (raw_material_availability_pct / 100.0)
    # Daily rate
    production_rate_per_day = effective_capacity / 30.0

    # Units that must be produced (net of current stock)
    units_to_produce = max(0, quantity - current_inventory)

    # Estimated days to produce remaining units
    if production_rate_per_day > 0:
        estimated_days = units_to_produce / production_rate_per_day
    else:
        estimated_days = float("inf")

    can_fulfill_on_time = estimated_days <= deadline_days

    # ── Recommendations ──────────────────────────────────────────────────────
    if can_fulfill_on_time:
        status_emoji = "✅"
        status_label = "Order is Feasible"
        summary = (
            f"You can fulfill {quantity} units within {deadline_days} days. "
            f"With {num_workers} worker(s) and {raw_material_availability_pct:.0f}% raw materials, "
            f"production will take ~{estimated_days:.0f} day(s). You have {current_inventory} units in stock."
        )
        recommended_response = (
            f"We can deliver {quantity} units within {deadline_days} days. "
            f"Please confirm the order and we will begin production immediately."
        )
        split_suggestion = None
    else:
        status_emoji = "❌"
        status_label = "Cannot Fulfill on Time"
        summary = (
            f"You cannot deliver {quantity} units in {deadline_days} days. "
            f"With {current_inventory} units in stock and a production rate of ~{production_rate_per_day:.1f} units/day "
            f"({num_workers} worker(s), {raw_material_availability_pct:.0f}% raw material), "
            f"full production would take ~{estimated_days:.0f} days."
        )

        # Split delivery: what can be delivered in the requested time?
        first_batch = current_inventory + int(production_rate_per_day * deadline_days)
        first_batch = min(first_batch, quantity)
        remaining = quantity - first_batch
        days_for_remaining = int(remaining / production_rate_per_day) if production_rate_per_day > 0 else 30
        total_days = deadline_days + days_for_remaining

        recommended_response = (
            f"We are unable to supply {quantity} units within {deadline_days} days with our current capacity. "
            f"We propose a split delivery: {first_batch} units in {deadline_days} days and "
            f"the remaining {remaining} units in {days_for_remaining} additional days (total {total_days} days). "
            f"Please let us know if this works for you."
        )
        split_suggestion = (
            f"Deliver {first_batch} units in {deadline_days} days + remaining {remaining} units in {days_for_remaining} more days"
        )

    return {
        "can_fulfill_on_time": can_fulfill_on_time,
        "status_emoji": status_emoji,
        "status_label": status_label,
        "summary": summary,
        "breakdown": {
            "required_units": quantity,
            "inventory_available": current_inventory,
            "units_to_produce": units_to_produce,
            "production_rate_per_day": round(production_rate_per_day, 2),
            "estimated_days": round(estimated_days, 1),
            "raw_material_adjusted_rate": round(effective_capacity, 1),
            "can_fulfill": can_fulfill_on_time,
        },
        "recommended_response": recommended_response,
        "split_delivery_suggestion": split_suggestion if not can_fulfill_on_time else None,
    }


# ─── Gemini-Enhanced Version ───────────────────────────────────────────────────

def calculate_feasibility_with_ai(
    enquiry_message: str,
    current_inventory: int,
    monthly_capacity: int,
    num_workers: int,
    raw_material_availability_pct: float,
    product_name: str = "artisan product",
) -> dict:
    """
    Runs the deterministic feasibility engine first, then optionally
    enriches the recommended_response with a Gemini-polished reply.
    """
    result = calculate_feasibility(
        enquiry_message=enquiry_message,
        current_inventory=current_inventory,
        monthly_capacity=monthly_capacity,
        num_workers=num_workers,
        raw_material_availability_pct=raw_material_availability_pct,
    )

    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        return result

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=gemini_key)
        prompt = f"""You are an expert B2B negotiation assistant for an Indian artisan.
The artisan makes: {product_name}

Buyer's enquiry: "{enquiry_message}"

Feasibility analysis (already calculated):
- Can fulfill on time: {result["can_fulfill_on_time"]}
- Required units: {result["breakdown"]["required_units"]}
- Units in inventory: {result["breakdown"]["inventory_available"]}
- Units to produce: {result["breakdown"]["units_to_produce"]}
- Production rate: {result["breakdown"]["production_rate_per_day"]:.1f} units/day
- Estimated production time: {result["breakdown"]["estimated_days"]:.0f} days
- Deadline: {result["breakdown"].get("deadline_days", "as per buyer")} days
- Split delivery suggestion: {result.get("split_delivery_suggestion", "N/A")}

Write a warm, professional, polite response message (2-4 sentences) from the artisan to the buyer.
If the order is NOT feasible, propose the split delivery option clearly.
Keep it concise, respectful, and solution-focused.
Return ONLY the message text, no JSON, no explanation."""

        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.4),
        )
        if response and getattr(response, "text", None):
            result["recommended_response"] = response.text.strip()
    except Exception as exc:
        logger.warning(f"[FEASIBILITY] Gemini enhancement failed, using deterministic response: {exc}")

    return result
