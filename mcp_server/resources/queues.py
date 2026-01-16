"""
Resources Module
Provides MCP resources for intake queues, taxonomy, and configuration.
"""

from typing import Dict, Any, List
import logging

from ..config_loader import get_config_loader

logger = logging.getLogger(__name__)


def get_intake_queues(industry: str = None) -> Dict[str, Any]:
    """
    Get current intake queue information.

    This resource provides information about intake queues for each industry,
    including available categories and routing teams.

    Args:
        industry: Optional specific industry to get queues for.
                  If None, returns all industries.

    Returns:
        Dict containing queue information per industry
    """
    config_loader = get_config_loader()
    available = config_loader.list_industries()

    if industry and industry in available:
        industries = [industry]
    else:
        industries = available

    queues = {}
    for ind in industries:
        try:
            config = config_loader.load_config(ind)
            routing_rules = config.get('routing_rules', [])
            
            # Build team list from routing rules
            teams = []
            for rule in routing_rules:
                teams.append({
                    "name": rule.get('name'),
                    "display_name": rule.get('display_name', rule.get('name')),
                    "sla_hours": rule.get('sla_hours', 24)
                })

            queues[ind] = {
                "industry_name": config.get('name', ind),
                "description": config.get('description', ''),
                "category_count": len(config.get('categories', [])),
                "routing_teams": teams,
                "team_count": len(teams)
            }
        except Exception as e:
            logger.error(f"Failed to load queue info for {ind}: {e}")
            queues[ind] = {"error": str(e)}

    return {
        "industries": industries,
        "queues": queues,
        "total_industries": len(industries)
    }


def get_category_taxonomy(industry: str) -> Dict[str, Any]:
    """
    Get the complete category taxonomy for an industry.

    This resource exposes the full category hierarchy including:
    - Category IDs and names
    - Descriptions
    - Keywords for matching
    - Subcategories

    Args:
        industry: The industry to get taxonomy for

    Returns:
        Dict containing category taxonomy
    """
    config_loader = get_config_loader()

    try:
        categories = config_loader.get_categories(industry)
        config = config_loader.load_config(industry)
    except FileNotFoundError:
        raise ValueError(f"Industry '{industry}' not found")

    taxonomy = []
    for cat in categories:
        taxonomy.append({
            "id": cat.get('id'),
            "name": cat.get('name'),
            "description": cat.get('description', ''),
            "keywords": cat.get('keywords', []),
            "keyword_count": len(cat.get('keywords', [])),
            "subcategories": cat.get('subcategories', []),
            "subcategory_count": len(cat.get('subcategories', []))
        })

    return {
        "industry": industry,
        "industry_name": config.get('name', industry),
        "description": config.get('description', ''),
        "categories": taxonomy,
        "category_count": len(taxonomy),
        "total_keywords": sum(c['keyword_count'] for c in taxonomy)
    }


def get_routing_config(industry: str) -> Dict[str, Any]:
    """
    Get the complete routing configuration for an industry.

    This resource exposes:
    - Routing rules and conditions
    - Severity thresholds
    - Risk flag definitions
    - Sampling/HITL thresholds

    Args:
        industry: The industry to get routing config for

    Returns:
        Dict containing complete routing configuration
    """
    config_loader = get_config_loader()

    try:
        config = config_loader.load_config(industry)
        routing_rules = config_loader.get_routing_rules(industry)
        severity_rules = config_loader.get_severity_rules(industry)
        risk_flags = config_loader.get_risk_flags(industry)
        thresholds = config_loader.get_sampling_thresholds(industry)
    except FileNotFoundError:
        raise ValueError(f"Industry '{industry}' not found")

    return {
        "industry": industry,
        "industry_name": config.get('name', industry),
        "routing_rules": routing_rules,
        "routing_rule_count": len(routing_rules),
        "severity_levels": list(severity_rules.keys()),
        "severity_rules": severity_rules,
        "risk_flag_types": list(risk_flags.keys()),
        "risk_flags": risk_flags,
        "sampling_thresholds": thresholds
    }


def list_available_industries() -> List[str]:
    """
    List all available industry configurations.

    Returns:
        List of industry names
    """
    config_loader = get_config_loader()
    return config_loader.list_industries()


def get_industry_summary(industry: str) -> Dict[str, Any]:
    """
    Get a summary of an industry's configuration.

    Args:
        industry: The industry to summarize

    Returns:
        Dict containing summary information
    """
    config_loader = get_config_loader()

    try:
        config = config_loader.load_config(industry)
        categories = config.get('categories', [])
        routing_rules = config.get('routing_rules', [])
        severity_rules = config.get('severity_rules', {})
        risk_flags = config.get('risk_flags', {})
    except FileNotFoundError:
        raise ValueError(f"Industry '{industry}' not found")

    return {
        "industry": industry,
        "name": config.get('name', industry),
        "description": config.get('description', ''),
        "category_count": len(categories),
        "categories": [c.get('id') for c in categories],
        "routing_team_count": len(routing_rules),
        "severity_level_count": len(severity_rules),
        "risk_flag_type_count": len(risk_flags)
    }
