"""
Score Severity Tool
Provides the score_severity MCP tool for assessing intake severity.
"""

from typing import Dict, Any, List, Optional
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


def score_severity(
    text: str,
    category_id: Optional[str] = None,
    industry: str = "banking",
    llm_provider: str = "groq"
) -> Dict[str, Any]:
    """
    Score the severity of an intake request.
    """
    if not text or not text.strip():
        raise ValueError("Intake text cannot be empty")

    text = text.strip()
    config_loader = get_config_loader()
    llm_client = get_llm_client(llm_provider)

    # Load configuration
    try:
        severity_rules = config_loader.get_severity_rules(industry)
        risk_flags = config_loader.get_risk_flags(industry)
        thresholds = config_loader.get_sampling_thresholds(industry)
    except FileNotFoundError:
        logger.warning(f"Industry '{industry}' not found, using banking defaults")
        industry = 'banking'
        severity_rules = config_loader.get_severity_rules(industry)
        risk_flags = config_loader.get_risk_flags(industry)
        thresholds = config_loader.get_sampling_thresholds(industry)

    # Analyze severity
    analysis = llm_client.analyze_severity(
        text, 
        category_id or "unknown", 
        severity_rules, 
        risk_flags, 
        industry
    )

    severity_score = analysis.get('severity_score', 2)
    risk_flags_found = analysis.get('risk_flags_found', [])

    # Determine escalation based on severity and risk flags
    high_risk_review = thresholds.get('high_risk_always_review', True)
    escalation_recommended = (
        severity_score >= 4 or
        (high_risk_review and len(risk_flags_found) > 0)
    )

    # Calculate SLA multiplier (lower = faster response needed)
    sla_multiplier = {
        5: 0.25,  # Critical: 25% of normal SLA
        4: 0.5,   # High: 50% of normal SLA
        3: 1.0,   # Medium: Normal SLA
        2: 1.5,   # Low: 150% of normal SLA
        1: 2.0    # Minimal: 200% of normal SLA
    }.get(severity_score, 1.0)

    result = {
        "industry": industry,
        "category_id": category_id,
        "severity_score": severity_score,
        "severity_level": analysis.get('severity_level', 'medium'),
        "priority": analysis.get('priority', 'normal'),
        "risk_flags_found": risk_flags_found,
        "risk_flag_count": len(risk_flags_found),
        "urgency_indicators": analysis.get('urgency_indicators', []),
        "escalation_recommended": escalation_recommended,
        "sla_multiplier": sla_multiplier,
        "explanation": analysis.get('explanation', 'No explanation available')
    }

    logger.info(
        f"Scored severity: score={severity_score}, "
        f"priority={result['priority']}, "
        f"risk_flags={len(risk_flags_found)}"
    )

    return result


def get_severity_thresholds(industry: str) -> Dict[str, Any]:
    """
    Get severity threshold information for an industry.

    Args:
        industry: The industry to look up

    Returns:
        Dict containing severity level definitions and thresholds
    """
    config_loader = get_config_loader()
    severity_rules = config_loader.get_severity_rules(industry)
    
    thresholds = {}
    for level, rules in severity_rules.items():
        if isinstance(rules, dict):
            thresholds[level] = {
                "score": rules.get('score'),
                "keywords_count": len(rules.get('keywords', [])),
                "conditions_count": len(rules.get('conditions', []))
            }
    
    return thresholds


def check_risk_flags(text: str, industry: str) -> Dict[str, List[str]]:
    """
    Check text for risk flags without full severity analysis.

    Args:
        text: The text to check
        industry: The industry to use for risk flag definitions

    Returns:
        Dict mapping risk flag types to matched keywords
    """
    if not text:
        return {}

    text_lower = text.lower()
    config_loader = get_config_loader()
    risk_flags = config_loader.get_risk_flags(industry)

    matches = {}
    for flag_type, keywords in risk_flags.items():
        matched = [kw for kw in keywords if kw.lower() in text_lower]
        if matched:
            matches[flag_type] = matched

    return matches
