"""
Classify Intake Tool
Provides the classify_intake MCP tool for categorizing intake requests.
"""

from typing import Dict, Any, Optional
import logging

from ..config_loader import get_config_loader
from ..llm.groq_client import get_groq_client
from ..llm.gemini_client import get_gemini_client

logger = logging.getLogger(__name__)


def get_llm_client(provider: str = "groq"):
    """Get the requested LLM client."""
    if provider.lower() == "gemini":
        return get_gemini_client()
    return get_groq_client()


def classify_intake(
    text: str,
    industry: Optional[str] = None,
    auto_detect_industry: bool = True,
    llm_provider: str = "groq"
) -> Dict[str, Any]:
    """
    Classify intake text into a category using LLM or keyword matching.
    """
    if not text or not text.strip():
        raise ValueError("Intake text cannot be empty")

    text = text.strip()
    config_loader = get_config_loader()
    llm_client = get_llm_client(llm_provider)

    # Determine industry
    if industry is None and auto_detect_industry:
        available = config_loader.list_industries()
        detection = llm_client.detect_industry(text, available)
        industry = detection.get('industry', 'banking')
        industry_confidence = detection.get('confidence', 0.5)
        industry_detected = True
    else:
        industry = industry or 'banking'
        industry_confidence = 1.0
        industry_detected = False

    # Load industry configuration
    try:
        config = config_loader.load_config(industry)
        categories = config.get('categories', [])
    except FileNotFoundError:
        logger.warning(f"Industry '{industry}' not found, falling back to banking")
        industry = 'banking'
        config = config_loader.load_config(industry)
        categories = config.get('categories', [])

    # Classify the text
    classification = llm_client.classify_text(text, categories, industry)

    # Get sampling thresholds
    thresholds = config_loader.get_sampling_thresholds(industry)
    auto_route_threshold = thresholds.get('confidence_for_auto_route', 0.85)
    hitl_threshold = thresholds.get('confidence_for_hitl', 0.6)

    # Determine if review is needed
    confidence = classification.get('confidence', 0.5)
    requires_review = confidence < auto_route_threshold

    # Build result
    result = {
        "industry": industry,
        "industry_detected": industry_detected,
        "industry_confidence": industry_confidence,
        "category_id": classification.get('category_id'),
        "category_name": classification.get('category_name'),
        "subcategory": classification.get('subcategory'),
        "confidence": confidence,
        "explanation": classification.get('explanation'),
        "requires_review": requires_review,
        "review_reason": None if not requires_review else (
            "Low confidence classification" if confidence < hitl_threshold
            else "Below auto-route threshold"
        ),
        "llm_provider": llm_provider
    }

    logger.info(
        f"Classified intake: category={result['category_id']}, "
        f"confidence={confidence:.2f}, industry={industry}, provider={llm_provider}"
    )

    return result


def get_category_info(industry: str, category_id: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a specific category.

    Args:
        industry: The industry to look up
        category_id: The category ID to find

    Returns:
        Category information dict or None if not found
    """
    config_loader = get_config_loader()
    categories = config_loader.get_categories(industry)

    for category in categories:
        if category.get('id') == category_id:
            return {
                "id": category['id'],
                "name": category['name'],
                "description": category.get('description', ''),
                "keywords": category.get('keywords', []),
                "subcategories": category.get('subcategories', [])
            }

    return None
