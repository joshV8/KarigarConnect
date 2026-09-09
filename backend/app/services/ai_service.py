import logging
from typing import Optional
from fastapi import HTTPException, status
import httpx
from pydantic import ValidationError

from app.config import (
    AI_MODE,
    AI_SERVICE_URL,
    AI_SERVICE_TIMEOUT,
)
from app.schemas.ai import AIProcessRequest, AIProcessResponse

logger = logging.getLogger("artisan.ai_service")


class AIService:
    """Service to handle communication with Person 2's AI pipeline / service."""

    def __init__(
        self,
        mode: Optional[str] = None,
        service_url: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.mode = (mode or AI_MODE).lower().strip()
        self.service_url = (service_url or AI_SERVICE_URL).rstrip("/")
        self.timeout = timeout or AI_SERVICE_TIMEOUT

    async def process_product(self, request_data: AIProcessRequest) -> AIProcessResponse:
        """Send product metadata, image URL, and optional audio URL to AI service."""
        if self.mode == "mock":
            logger.info(
                f"[MOCK_AI] Simulating AI pipeline for product_id={request_data.product_id}"
                + (f" with audio_url={request_data.audio_url}" if request_data.audio_url else " (no audio)")
            )
            return self._mock_process_response(request_data)

        # Remote AI Mode (Connecting to Person 2's FastAPI service)
        target_url = f"{self.service_url}/process"
        logger.info(f"[REMOTE_AI] Forwarding product {request_data.product_id} to {target_url}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    target_url,
                    json=request_data.model_dump(),
                )
                response.raise_for_status()
                raw_json = response.json()

        except httpx.ConnectError as exc:
            logger.error(f"Cannot connect to AI service at {target_url}: {exc}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Service is currently unreachable. Please ensure Person 2's AI service is running.",
            )
        except httpx.TimeoutException as exc:
            logger.error(f"AI service timed out after {self.timeout}s: {exc}")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"AI Service timed out after {self.timeout} seconds.",
            )
        except httpx.HTTPStatusError as exc:
            logger.error(f"AI service returned HTTP {exc.response.status_code}: {exc.response.text}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI Service error (HTTP {exc.response.status_code}).",
            )
        except Exception as exc:
            logger.error(f"Unexpected error communicating with AI service: {exc}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to communicate with the external AI service.",
            )

        # Validate structured AI response
        try:
            validated_response = AIProcessResponse.model_validate(raw_json)
            return validated_response
        except ValidationError as val_err:
            logger.error(f"AI service returned malformed data: {val_err}. Raw: {raw_json}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI Service returned malformed or incomplete data structure.",
            )

    def _mock_process_response(self, request: AIProcessRequest) -> AIProcessResponse:
        """Realistic mock response — includes transcription when audio_url is provided."""
        has_audio = bool(request.audio_url)
        lang = request.language or "hi"

        # Simulate language-specific transcription when audio or voice_text is present
        transcription: Optional[str] = None
        translated_text: Optional[str] = None
        if has_audio:
            if lang == "mr":
                transcription = "ही बांबूची हाताने बनवलेली टोपली आहे"
                translated_text = "This is a handwoven bamboo basket"
            elif lang == "hi":
                transcription = "यह बांस की हाथ से बुनी हुई टोकरी है"
                translated_text = "This is a handwoven bamboo basket"
            elif lang == "gu":
                transcription = "આ હાથ વણેલ વાંસની ટોપલી છે"
                translated_text = "This is a handwoven bamboo basket"
            else:
                transcription = "This is a handwoven bamboo basket"
                translated_text = "This is a handwoven bamboo basket"
        elif request.voice_text:
            transcription = request.voice_text
            translated_text = "Handcrafted artisan traditional creation"

        return AIProcessResponse(
            product_name="Handwoven Bamboo Basket",
            description_en=(
                "A beautifully handcrafted bamboo basket made by skilled artisans "
                "using traditional techniques passed down through generations."
            ),
            description_hi=(
                "पारंपरिक तकनीकों का उपयोग करके कुशल कारीगरों द्वारा बनाई गई "
                "सुंदर हस्तनिर्मित बांस की टोकरी।"
            ),
            category="Home Decor",
            material="Bamboo",
            seo_title="Handwoven Bamboo Basket — Artisan Crafted",
            seo_keywords=[
                "bamboo basket",
                "handmade basket",
                "artisan basket",
                "eco friendly basket",
                "traditional craft",
            ],
            transcription=transcription,
            translated_text=translated_text,
            processed_image_url=None,  # Person 2 will supply this when ready
        )

    async def analyze_negotiation(
        self, enquiry_message: str, material_cost: float, labour_cost: float
    ) -> dict:
        """Evaluate a buyer's offer against the artisan's floor price and capacity."""
        if self.mode == "mock":
            logger.info("[MOCK_AI] Simulating negotiation analysis...")
            # Calculate sustainable floor (cost + 15% margin)
            floor_price = (material_cost + labour_cost) * 1.15
            
            # Simple mock evaluation
            if "650" in enquiry_message:
                return {
                    "is_sustainable": False,
                    "evaluation_summary": f"The buyer is offering ₹650, but your sustainable floor price (with 15% margin) is ₹{floor_price:.0f}. This offer would result in a loss or negligible profit.",
                    "proposed_counter_offers": [
                        f"Counter-offer: ₹{floor_price + 20:.0f}/unit for 150 units",
                        "Accept ₹700 if buyer increases delivery time to 30 days."
                    ]
                }
            else:
                return {
                    "is_sustainable": True,
                    "evaluation_summary": f"The buyer's offer looks reasonable and is above your sustainable floor price of ₹{floor_price:.0f}.",
                    "proposed_counter_offers": [
                        "Accept the offer as is.",
                        "Counter-offer: Accept, but request 50% advance payment."
                    ]
                }
                
        # Remote AI Mode (Forward to AI Microservice)
        target_url = f"{self.service_url}/negotiate"
        logger.info(f"[REMOTE_AI] Forwarding negotiation analysis to {target_url}")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    target_url,
                    json={
                        "enquiry_message": enquiry_message,
                        "material_cost": material_cost,
                        "labour_cost": labour_cost
                    },
                )
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            logger.error(f"Failed to communicate with AI service for negotiation: {exc}")
            # Fallback mock logic if remote fails
            floor_price = (material_cost + labour_cost) * 1.15
            return {
                "is_sustainable": False,
                "evaluation_summary": f"The buyer's offer needs review. Your sustainable floor price is ₹{floor_price:.0f}.",
                "proposed_counter_offers": [
                    f"Counter-offer: ₹{floor_price + 20:.0f}/unit",
                ]
            }

# Global singleton instance
ai_service = AIService()
