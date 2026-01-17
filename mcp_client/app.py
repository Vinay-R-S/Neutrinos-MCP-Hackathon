"""
MCP Client - FastAPI Application
Web interface for submitting issues/complaints and connecting to MCP Server.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv

from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Load environment variables from mcp_client/.env
_client_dir = Path(__file__).parent
_env_path = _client_dir / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    load_dotenv()

# Add parent directory to path for mcp_server imports
sys.path.insert(0, str(_client_dir.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import MCP server modules
try:
    from mcp_server.config_loader import get_config_loader
    from mcp_server.tools.classify import classify_intake
    from mcp_server.tools.severity import score_severity
    from mcp_server.tools.routing import route_case
    MCP_SERVER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"MCP Server modules not available: {e}")
    MCP_SERVER_AVAILABLE = False

# Import file extractor (relative import for package)
from .file_extractor import extract_text_from_file

# Initialize FastAPI
app = FastAPI(
    title="Intelligent Intake & Triage",
    description="Submit issues and complaints for intelligent routing",
    version="1.0.0"
)

# Mount static files
static_dir = _client_dir / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Setup templates
templates_dir = _client_dir / "templates"
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the main submission page."""
    industries = []
    if MCP_SERVER_AVAILABLE:
        try:
            loader = get_config_loader()
            industries = loader.list_industries()
        except Exception as e:
            logger.error(f"Failed to load industries: {e}")
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "industries": industries
    })


@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    """Render the about page."""
    return templates.TemplateResponse("about.html", {"request": request})


@app.post("/submit")
async def submit_intake(
    request: Request,
    issue_text: str = Form(""),
    industry: Optional[str] = Form(None),
    llm_provider: str = Form("groq"),
    files: List[UploadFile] = File(default=[])
):
    """Process submitted issue and files."""
    try:
        # Combine text from form and files
        combined_text = issue_text.strip()
        extracted_files = []
        
        # Extract text from uploaded files
        for file in files:
            if file.filename:
                try:
                    content = await file.read()
                    extracted = extract_text_from_file(content, file.filename)
                    if extracted:
                        extracted_files.append({
                            "filename": file.filename,
                            "text": extracted[:500] + "..." if len(extracted) > 500 else extracted
                        })
                        combined_text += f"\n\n[From {file.filename}]:\n{extracted}"
                except Exception as e:
                    logger.error(f"Failed to extract from {file.filename}: {e}")
                    extracted_files.append({
                        "filename": file.filename,
                        "text": f"Error: {str(e)}"
                    })
        
        if not combined_text.strip():
            return templates.TemplateResponse("result.html", {
                "request": request,
                "error": "Please provide an issue description or upload files.",
                "result": None
            })
        
        # Process with MCP Server
        # Process with MCP Server
        if MCP_SERVER_AVAILABLE:
            result = process_with_mcp(combined_text, industry, llm_provider)
        else:
            result = {
                "error": "MCP Server not available",
                "classification": None,
                "severity": None,
                "routing": None
            }
        
        return templates.TemplateResponse("result.html", {
            "request": request,
            "result": result,
            "original_text": issue_text[:300] + "..." if len(issue_text) > 300 else issue_text,
            "extracted_files": extracted_files,
            "error": result.get("error")
        })
        
    except Exception as e:
        logger.error(f"Submit error: {e}")
        return templates.TemplateResponse("result.html", {
            "request": request,
            "error": str(e),
            "result": None
        })


@app.get("/api/industries")
async def get_industries():
    """Get list of available industries."""
    if not MCP_SERVER_AVAILABLE:
        return JSONResponse({"industries": [], "error": "MCP Server not available"})
    
    try:
        loader = get_config_loader()
        industries = loader.list_industries()
        return JSONResponse({"industries": industries})
    except Exception as e:
        return JSONResponse({"industries": [], "error": str(e)})


def process_with_mcp(text: str, industry: Optional[str] = None, llm_provider: str = "groq") -> dict:
    """Process text through MCP Server pipeline."""
    try:
        # Step 1: Classify
        classification = classify_intake(text, industry, auto_detect_industry=True, llm_provider=llm_provider)
        detected_industry = classification.get('industry', 'banking')
        category_id = classification.get('category_id')
        
        # Step 2: Score severity
        severity = score_severity(text, category_id, detected_industry, llm_provider=llm_provider)
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
                "category_id": category_id,
                "severity_score": severity_score,
                "severity_level": severity.get('severity_level'),
                "priority": severity.get('priority'),
                "assigned_team": routing.get('team_display_name'),
                "team_id": routing.get('assigned_team'),
                "sla_hours": routing.get('sla_hours'),
                "escalation_path": routing.get('escalation_path'),
                "requires_review": classification.get('requires_review', False),
                "requires_review": classification.get('requires_review', False),
                "confidence": classification.get('confidence', 0),
                "llm_provider": classification.get('llm_provider', 'groq')
            }
        }
    except Exception as e:
        logger.error(f"MCP processing error: {e}")
        return {"error": str(e), "success": False}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
