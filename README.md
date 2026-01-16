# Intelligent Intake and Triage MCP Server

A fully functional MCP (Model Context Protocol) server that exposes tools, resources, and prompts for intelligent intake classification, severity scoring, and case routing. Built for the Neutrinos MCP Hackathon.

## Core Pattern

```
MCP resources (intake data) → LLM calls (classification/scoring) → MCP resource updates (routing)
```

## Features

- **Config-Driven**: Categories, severity rules, and routing logic live in YAML configs, not hardcoded
- **Multi-Industry Support**: Banking, Healthcare, IT Services, Retail, and Logistics
- **LLM-Powered**: Uses Groq API (llama-3.3-70b-versatile) for intelligent classification
- **Fallback Mode**: Keyword-based classification when LLM is unavailable
- **Stateless**: Horizontally scalable design for enterprise use

## Supported Industries

| Industry    | Use Case                        |
| ----------- | ------------------------------- |
| Banking     | Complaint intake and escalation |
| Healthcare  | Patient inquiry triage          |
| IT Services | Support ticket classification   |
| Retail      | Customer feedback routing       |
| Logistics   | Shipment exception handling     |

## MCP Tools

| Tool                  | Description                                |
| --------------------- | ------------------------------------------ |
| `classify_intake`     | Classify free-text intake into categories  |
| `score_severity`      | Score severity (1-5) and detect risk flags |
| `route_case`          | Route case to appropriate team with SLA    |
| `get_routing_rules`   | Get routing rules for an industry          |
| `process_intake_full` | Full pipeline: classify → score → route    |
| `list_industries`     | List available industry configurations     |

## MCP Resources

| Resource URI                   | Description                  |
| ------------------------------ | ---------------------------- |
| `intake://queues`              | All intake queue information |
| `intake://queues/{industry}`   | Queue for specific industry  |
| `intake://taxonomy/{industry}` | Category taxonomy            |
| `intake://routing/{industry}`  | Routing configuration        |
| `intake://industries`          | All industry summaries       |

## Quick Start

### 1. Clone and Setup

```bash
git clone <repo-url>
cd Neutrinos-MCP-Hackathon
python -m venv .venv
.\.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 4. Run the MCP Server

```bash
python -m mcp_server.server
```

## Project Structure

```
├── mcp_server/
│   ├── server.py           # Main MCP server with FastMCP
│   ├── config_loader.py    # YAML/JSON config management
│   ├── tools/
│   │   ├── classify.py     # classify_intake tool
│   │   ├── severity.py     # score_severity tool
│   │   └── routing.py      # route_case tool
│   ├── resources/
│   │   └── queues.py       # MCP resources
│   └── llm/
│       └── groq_client.py  # Groq API integration
├── configs/
│   ├── banking.yaml        # 15 categories + routing rules
│   ├── healthcare.yaml
│   ├── it_services.yaml
│   ├── retail.yaml
│   └── logistics.yaml
└── requirements.txt
```

## Configuration Structure

Each industry config includes:

- **Categories**: Taxonomy with keywords and subcategories (15+ per industry)
- **Severity Rules**: Score thresholds (1-5) with keyword triggers
- **Risk Flags**: High-priority keyword dictionaries
- **Routing Rules**: Decision tree for team assignment with SLAs

## Testing

```python
# Test classification
from mcp_server.tools.classify import classify_intake
result = classify_intake("My credit card was stolen", "banking")
print(result)

# Test severity scoring
from mcp_server.tools.severity import score_severity
result = score_severity("Emergency: system is completely down", "system_outage", "it_services")
print(result)

# Test routing
from mcp_server.tools.routing import route_case
result = route_case("unauthorized_transactions", 5, "banking", ["fraud_indicators"])
print(result)
```

## Environment Variables

| Variable           | Description          | Required   |
| ------------------ | -------------------- | ---------- |
| `GROQ_API_KEY`     | Groq API key for LLM | Optional\* |
| `DEFAULT_INDUSTRY` | Default industry     | No         |

\*If not set, falls back to keyword-based classification

## License

MIT License
