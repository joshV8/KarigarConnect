import logging
from typing import List, Dict, Any
from app.models.product import Product
from app.models.buyer import Buyer
from app.schemas.buyer import BuyerMatchResponse

logger = logging.getLogger("artisan.market_service")


class B2BBuyerProvider:
    """Provider for matching against the registered B2B wholesale buyers repository."""

    # Major procurement & artisan craft wholesale distribution hubs
    TIER1_HUBS = {"mumbai", "delhi", "jaipur", "bangalore", "kolkata", "ahmedabad", "chennai", "pune"}

    def score_buyer_for_product(self, product: Product, buyer: Buyer) -> BuyerMatchResponse:
        """Compute matching score (0-100) between an artisan product and a prospective buyer."""
        score = 10  # Baseline active buyer relevance
        reasons = ["Active wholesale partner (+10)"]

        prod_cat = (product.category or "").lower().strip()
        buyer_cat = (buyer.category or "").lower().strip()
        buyer_desc = (buyer.description or "").lower().strip()
        prod_mat = (product.material or "").lower().strip()
        buyer_loc = (buyer.location or "").lower().strip()

        # 1. Category match (+50 points)
        if prod_cat and buyer_cat and (prod_cat in buyer_cat or buyer_cat in prod_cat):
            score += 50
            reasons.append(f"Category alignment: {buyer.category} (+50)")
        elif any(word in buyer_cat for word in prod_cat.split()):
            score += 35
            reasons.append(f"Partial category alignment: {buyer.category} (+35)")

        # 2. Craft material match (+25 points)
        if prod_mat and (prod_mat in buyer_cat or prod_mat in buyer_desc):
            score += 25
            reasons.append(f"Craft material demand: {product.material} (+25)")

        # 3. Location / Regional wholesale hub relevance (+15 points)
        if buyer_loc in self.TIER1_HUBS:
            score += 15
            reasons.append(f"Major wholesale distribution hub: {buyer.location} (+15)")

        final_score = min(100, score)

        return BuyerMatchResponse(
            id=buyer.id,
            name=buyer.name,
            company=buyer.company,
            category=buyer.category,
            location=buyer.location,
            description=buyer.description,
            match_score=final_score,
            match_reasons=reasons,
        )

    def match_buyers(self, product: Product, buyers: List[Buyer]) -> List[BuyerMatchResponse]:
        """Score all buyers against the product and return them sorted by match score descending."""
        matched = [self.score_buyer_for_product(product, b) for b in buyers]
        matched.sort(key=lambda x: x.match_score, reverse=True)
        return matched


class MarketLinkageService:
    """Unified Market Linkage Service Architecture.
    
    Architecture:
    -------------
    MarketLinkageService
            |
            ├── B2BBuyerProvider (Active: Local PostgreSQL B2B buyer database)
            |
            ├── GovernmentMarketplaceProvider (Future Extension: GeM, TRIFED, ONDC)
            |     TODO(gov-integration): Official government procurement integration 
            |     requires approved OAuth & API access keys.
            |
            └── DirectBuyerProvider (Future Extension: Direct-to-Consumer / Retail)
    """

    def __init__(self):
        self.b2b_provider = B2BBuyerProvider()

    def find_matching_buyers(self, product: Product, buyers: List[Buyer]) -> List[BuyerMatchResponse]:
        """Find and rank matching B2B buyers for a given product."""
        return self.b2b_provider.match_buyers(product, buyers)


# Global singleton instance
market_service = MarketLinkageService()
