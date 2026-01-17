"""
Intelligent Intake and Triage MCP Server

This is the main MCP server implementation using FastMCP.
It exposes tools, resources, and prompts for intake classification,
severity scoring, and case routing.

Core Pattern: MCP resources (intake data) → LLM calls (classification/scoring) → MCP resource updates (routing)
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables from mcp_server/.env
_server_dir = Path(__file__).parent
_env_path = _server_dir / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    # Fallback to root .env if server-specific doesn't exist
    load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import FastMCP
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    logger.error("FastMCP not installed. Run: pip install fastmcp")
    raise

# Import our modules
from mcp_server.config_loader import get_config_loader, load_config
from mcp_server.tools.classify import classify_intake, get_category_info
from mcp_server.tools.severity import score_severity, check_risk_flags, get_severity_thresholds
from mcp_server.tools.routing import route_case, get_routing_rules, get_available_teams
from mcp_server.resources.queues import (
    get_intake_queues,
    get_category_taxonomy,
    get_routing_config,
    list_available_industries,
    get_industry_summary
)


# Initialize the MCP server
mcp = FastMCP(
    name="intake-triage-server"
)


# ============================================================================
# MCP TOOLS
# ============================================================================

@mcp.tool()
def classify_intake_tool(
    text: str,
    industry: Optional[str] = None,
    auto_detect_industry: bool = True
) -> Dict[str, Any]:
    """
    Classify intake text into a category.

    Analyzes free-text intake and classifies it into an appropriate category
    using LLM-powered classification with fallback to keyword matching.

    Args:
        text: The intake text to classify (complaint, request, inquiry)
        industry: Optional industry context (banking, healthcare, it_services, retail, logistics).
                  If not provided and auto_detect_industry is True, will be detected from text.
        auto_detect_industry: Whether to auto-detect industry from text if not provided

    Returns:
        Classification result with category, confidence, and explanation
    """
    try:
        return classify_intake(text, industry, auto_detect_industry)
    except Exception as e:
        logger.error(f"Error in classify_intake: {e}")
        return {"error": str(e)}


@mcp.tool()
def score_severity_tool(
    text: str,
    category_id: Optional[str] = None,
    industry: str = "banking"
) -> Dict[str, Any]:
    """
    Score the severity of an intake request.

    Analyzes intake text to determine severity level, priority,
    and identifies any risk flags that require attention.

    Args:
        text: The intake text to analyze
        category_id: Optional category ID for additional context
        industry: The industry context for severity rules

    Returns:
        Severity assessment with score (1-5), priority level, and risk flags
    """
    try:
        return score_severity(text, category_id, industry)
    except Exception as e:
        logger.error(f"Error in score_severity: {e}")
        return {"error": str(e)}


@mcp.tool()
def route_case_tool(
    category_id: str,
    severity_score: int,
    industry: str = "banking",
    risk_flags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Route a case to the appropriate team.

    Uses configuration-driven routing rules to determine the best team
    for handling a case based on category, severity, and risk factors.

    Args:
        category_id: The classified category ID
        severity_score: Severity score (1-5)
        industry: The industry context for routing rules
        risk_flags: Optional list of risk flag types detected

    Returns:
        Routing decision with team assignment, SLA, and escalation path
    """
    try:
        return route_case(category_id, severity_score, industry, risk_flags)
    except Exception as e:
        logger.error(f"Error in route_case: {e}")
        return {"error": str(e)}


@mcp.tool()
def get_routing_rules_tool(industry: str) -> Dict[str, Any]:
    """
    Get routing rules for an industry.

    Returns the complete routing configuration including all teams,
    conditions, SLA definitions, and escalation paths.

    Args:
        industry: The industry to get routing rules for

    Returns:
        Complete routing rules configuration
    """
    try:
        return get_routing_rules(industry)
    except Exception as e:
        logger.error(f"Error in get_routing_rules: {e}")
        return {"error": str(e)}


@mcp.tool()
def process_intake_full(
    text: str,
    industry: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process an intake request through the full pipeline.

    This is a convenience tool that runs the complete intake processing:
    1. Classify the intake into a category
    2. Score the severity
    3. Route to the appropriate team

    Args:
        text: The intake text to process
        industry: Optional industry context (auto-detected if not provided)

    Returns:
        Complete processing result with classification, severity, and routing
    """
    try:
        # Step 1: Classify
        classification = classify_intake(text, industry, auto_detect_industry=True)
        detected_industry = classification.get('industry', 'banking')
        category_id = classification.get('category_id')

        # Step 2: Score severity
        severity = score_severity(text, category_id, detected_industry)
        severity_score = severity.get('severity_score', 2)
        risk_flags = severity.get('risk_flags_found', [])

        # Step 3: Route
        routing = route_case(category_id, severity_score, detected_industry, risk_flags)

        return {
            "success": True,
            "classification": classification,
            "severity": severity,
            "routing": routing,
            "summary": {
                "industry": detected_industry,
                "category": classification.get('category_name'),
                "severity_level": severity.get('severity_level'),
                "assigned_team": routing.get('team_display_name'),
                "sla_hours": routing.get('sla_hours'),
                "requires_review": classification.get('requires_review', False) or 
                                   severity.get('escalation_recommended', False)
            }
        }
    except Exception as e:
        logger.error(f"Error in process_intake_full: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
def list_industries() -> List[str]:
    """
    List all available industry configurations.

    Returns a list of industry names that have configuration files.
    Each industry can be used with the classification, severity, and routing tools.

    Returns:
        List of industry names (e.g., ['banking', 'healthcare', ...])
    """
    return list_available_industries()


@mcp.tool()
def get_industry_info(industry: str) -> Dict[str, Any]:
    """
    Get detailed information about an industry configuration.

    Args:
        industry: The industry to get information about

    Returns:
        Industry configuration summary
    """
    try:
        return get_industry_summary(industry)
    except Exception as e:
        logger.error(f"Error in get_industry_info: {e}")
        return {"error": str(e)}


# ============================================================================
# MCP RESOURCES
# ============================================================================

@mcp.resource("intake://queues")
def resource_intake_queues() -> str:
    """Get all intake queue information."""
    import json
    return json.dumps(get_intake_queues(), indent=2)


@mcp.resource("intake://queues/{industry}")
def resource_industry_queue(industry: str) -> str:
    """Get intake queue for a specific industry."""
    import json
    return json.dumps(get_intake_queues(industry), indent=2)


@mcp.resource("intake://taxonomy/{industry}")
def resource_category_taxonomy(industry: str) -> str:
    """Get category taxonomy for an industry."""
    import json
    try:
        return json.dumps(get_category_taxonomy(industry), indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})


@mcp.resource("intake://routing/{industry}")
def resource_routing_config(industry: str) -> str:
    """Get routing configuration for an industry."""
    import json
    try:
        return json.dumps(get_routing_config(industry), indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})


@mcp.resource("intake://industries")
def resource_industries() -> str:
    """List all available industries."""
    import json
    industries = list_available_industries()
    summaries = []
    for ind in industries:
        try:
            summaries.append(get_industry_summary(ind))
        except Exception:
            summaries.append({"industry": ind, "error": "Failed to load"})
    return json.dumps({
        "industries": industries,
        "count": len(industries),
        "summaries": summaries
    }, indent=2)


# ============================================================================
# MCP PROMPTS
# ============================================================================

@mcp.prompt()
def classify_intake_prompt(text: str, industry: str = "banking") -> str:
    """
    Generate a prompt for classifying intake text.

    Args:
        text: The intake text to classify
        industry: The industry context
    """
    config_loader = get_config_loader()
    try:
        categories = config_loader.get_categories(industry)
        category_list = "\n".join([
            f"- {cat['id']}: {cat['name']}"
            for cat in categories
        ])
    except Exception:
        category_list = "Categories not available"

    return f"""You are analyzing a customer intake request for the {industry} industry.

INTAKE TEXT:
{text}

AVAILABLE CATEGORIES:
{category_list}

Please classify this intake into the most appropriate category and explain your reasoning.
Also assess the severity (1-5) and identify any urgent indicators."""


@mcp.prompt()
def triage_decision_prompt(
    classification: Dict[str, Any],
    severity: Dict[str, Any],
    routing: Dict[str, Any]
) -> str:
    """
    Generate a summary prompt explaining triage decisions.

    Args:
        classification: Classification result
        severity: Severity assessment
        routing: Routing decision
    """
    return f"""TRIAGE SUMMARY

Classification:
- Category: {classification.get('category_name', 'Unknown')}
- Confidence: {classification.get('confidence', 0):.0%}
- Explanation: {classification.get('explanation', 'N/A')}

Severity Assessment:
- Score: {severity.get('severity_score', 0)}/5 ({severity.get('severity_level', 'unknown')})
- Priority: {severity.get('priority', 'normal')}
- Risk Flags: {', '.join(severity.get('risk_flags_found', [])) or 'None'}

Routing Decision:
- Assigned Team: {routing.get('team_display_name', 'Unknown')}
- SLA: {routing.get('sla_hours', 0)} hours
- Escalation Path: {routing.get('escalation_path', 'N/A')}
- Reason: {routing.get('routing_reason', 'N/A')}

Review Required: {'Yes' if classification.get('requires_review') or severity.get('escalation_recommended') else 'No'}"""


# ============================================================================
# SERVER ENTRY POINT
# ============================================================================

def main():
    """Run the MCP server."""
    logger.info("Starting Intelligent Intake and Triage MCP Server...")
    
    # Verify configurations are available
    config_loader = get_config_loader()
    industries = config_loader.list_industries()
    logger.info(f"Loaded {len(industries)} industry configurations: {industries}")
    
    # Run the server
    mcp.run()


if __name__ == "__main__":
    main()
