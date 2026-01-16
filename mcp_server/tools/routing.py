"""
Route Case Tool
Provides the route_case and get_routing_rules MCP tools.
"""

from typing import Dict, Any, List, Optional
import logging

from ..config_loader import get_config_loader

logger = logging.getLogger(__name__)


def route_case(
    category_id: str,
    severity_score: int,
    industry: str = "banking",
    risk_flags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Route a case to the appropriate team based on classification and severity.

    This tool:
    1. Evaluates routing rules from configuration
    2. Matches based on category, severity, and risk flags
    3. Returns the assigned team and SLA information
    4. Provides escalation path if needed

    Args:
        category_id: The classified category ID
        severity_score: Severity score (1-5)
        industry: The industry configuration to use
        risk_flags: Optional list of risk flag types detected
        metadata: Optional additional metadata for routing decisions

    Returns:
        Dict containing:
            - assigned_team: Team name to route to
            - team_display_name: Human-readable team name
            - sla_hours: SLA in hours
            - escalation_path: Next level escalation
            - priority_override: Whether priority was overridden
            - routing_reason: Explanation of routing decision
            - notes: Additional notes for the team

    Raises:
        ValueError: If required parameters are invalid
    """
    if not category_id:
        raise ValueError("category_id is required")
    if not isinstance(severity_score, int) or severity_score < 1 or severity_score > 5:
        raise ValueError("severity_score must be an integer between 1 and 5")

    risk_flags = risk_flags or []
    metadata = metadata or {}
    config_loader = get_config_loader()

    # Load routing rules
    try:
        routing_rules = config_loader.get_routing_rules(industry)
        thresholds = config_loader.get_sampling_thresholds(industry)
    except FileNotFoundError:
        logger.warning(f"Industry '{industry}' not found, using banking defaults")
        industry = 'banking'
        routing_rules = config_loader.get_routing_rules(industry)
        thresholds = config_loader.get_sampling_thresholds(industry)

    # Find matching routing rule
    matched_rule = None
    routing_reason = None

    for rule in routing_rules:
        conditions = rule.get('conditions', {})
        
        # Check if this is the default rule
        if conditions.get('default', False):
            if matched_rule is None:
                matched_rule = rule
                routing_reason = "Default routing rule applied"
            continue

        # Check category match
        rule_categories = conditions.get('categories', [])
        category_match = len(rule_categories) == 0 or category_id in rule_categories

        # Check severity threshold
        severity_min = conditions.get('severity_min', 0)
        severity_match = severity_score >= severity_min

        # Check risk flags
        rule_risk_flags = conditions.get('risk_flags', [])
        risk_match = len(rule_risk_flags) == 0 or any(
            flag in risk_flags for flag in rule_risk_flags
        )

        # If all conditions match, this rule applies
        if category_match and severity_match and risk_match:
            # Higher priority rules (earlier in list with more specific conditions)
            # should override default
            specificity = (
                len(rule_categories) +
                (1 if severity_min > 0 else 0) +
                len(rule_risk_flags)
            )
            
            if matched_rule is None or specificity > 0:
                matched_rule = rule
                reasons = []
                if rule_categories:
                    reasons.append(f"category '{category_id}' matched")
                if severity_min > 0:
                    reasons.append(f"severity {severity_score} >= {severity_min}")
                if rule_risk_flags:
                    matched_flags = [f for f in rule_risk_flags if f in risk_flags]
                    reasons.append(f"risk flags matched: {matched_flags}")
                routing_reason = "Matched: " + ", ".join(reasons) if reasons else "Rule conditions matched"

    # If still no match, create a default response
    if matched_rule is None:
        logger.warning(f"No routing rule matched for category={category_id}, severity={severity_score}")
        return {
            "industry": industry,
            "assigned_team": "general_intake",
            "team_display_name": "General Intake Queue",
            "sla_hours": 48,
            "escalation_path": "supervisor",
            "priority_override": False,
            "routing_reason": "No specific rule matched - routed to general intake",
            "notes": None
        }

    # Calculate adjusted SLA based on severity
    base_sla = matched_rule.get('sla_hours', 24)
    sla_multiplier = {
        5: 0.25,
        4: 0.5,
        3: 1.0,
        2: 1.5,
        1: 2.0
    }.get(severity_score, 1.0)
    
    adjusted_sla = max(0.5, base_sla * sla_multiplier)  # Minimum 30 minutes

    # Check for priority override
    high_risk_review = thresholds.get('high_risk_always_review', True)
    priority_override = high_risk_review and len(risk_flags) > 0

    result = {
        "industry": industry,
        "category_id": category_id,
        "severity_score": severity_score,
        "assigned_team": matched_rule.get('name'),
        "team_display_name": matched_rule.get('display_name', matched_rule.get('name')),
        "sla_hours": round(adjusted_sla, 2),
        "base_sla_hours": base_sla,
        "escalation_path": matched_rule.get('escalation_path'),
        "priority_override": priority_override,
        "routing_reason": routing_reason,
        "notes": matched_rule.get('notes'),
        "risk_flags_considered": risk_flags
    }

    logger.info(
        f"Routed case: team={result['assigned_team']}, "
        f"sla={result['sla_hours']}h, reason={routing_reason}"
    )

    return result


def get_routing_rules(industry: str) -> Dict[str, Any]:
    """
    Get all routing rules for an industry.

    This tool returns the complete routing configuration including:
    - All team definitions and conditions
    - SLA information
    - Escalation paths

    Args:
        industry: The industry configuration to retrieve

    Returns:
        Dict containing:
            - industry: The industry name
            - rules: List of routing rules with conditions
            - teams: Summary of all teams
            - thresholds: Sampling/confidence thresholds
    """
    config_loader = get_config_loader()

    try:
        routing_rules = config_loader.get_routing_rules(industry)
        thresholds = config_loader.get_sampling_thresholds(industry)
    except FileNotFoundError:
        raise ValueError(f"Industry '{industry}' not found")

    # Build team summary
    teams = {}
    for rule in routing_rules:
        team_name = rule.get('name')
        teams[team_name] = {
            "display_name": rule.get('display_name', team_name),
            "sla_hours": rule.get('sla_hours'),
            "escalation_path": rule.get('escalation_path'),
            "is_default": rule.get('conditions', {}).get('default', False)
        }

    return {
        "industry": industry,
        "rules": routing_rules,
        "teams": teams,
        "team_count": len(teams),
        "thresholds": thresholds
    }


def get_available_teams(industry: str) -> List[Dict[str, Any]]:
    """
    Get list of available teams for an industry.

    Args:
        industry: The industry to look up

    Returns:
        List of team dictionaries with name, display_name, and SLA
    """
    routing_info = get_routing_rules(industry)
    return [
        {
            "name": name,
            **info
        }
        for name, info in routing_info.get('teams', {}).items()
    ]
