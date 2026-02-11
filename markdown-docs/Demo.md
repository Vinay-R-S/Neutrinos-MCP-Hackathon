# Intelligent Intake and Triage System - Detailed Architecture

This document provides a comprehensive architectural overview of the MCP-based Intelligent Intake and Triage System.

---

## System Architecture Diagram

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                                    USER INTERFACE LAYER                                   │
├───────────────────────────────────────────────────────────────────────────────────────────┤ 
│                                                                                           │
│  ┌──────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                           MCP CLIENT (mcp_client/)                                   │ │
│  ├──────────────────────────────────────────────────────────────────────────────────────┤ │
│  │                                                                                      │ │
│  │  ┌───────────────────────────────────────────────────────────────────────────────┐   │ │
│  │  │                          app.py (FastAPI Application)                         │   │ │
│  │  ├───────────────────────────────────────────────────────────────────────────────┤   │ │
│  │  │  • GET /              → Renders index.html (submission form)                  │   │ │
│  │  │  • GET /about         → Renders about.html (system info)                      │   │ │
│  │  │  • POST /submit       → Web form submission (returns HTML result)             │   │ │
│  │  │  • POST /api/submit   → JSON API endpoint (returns JSON result)               │   │ │
│  │  │  • GET /api/industries → Lists available industries                           │   │ │
│  │  │  • process_with_mcp() → Orchestrates the 3-step pipeline                      │   │ │
│  │  └───────────────────────────────────────────────────────────────────────────────┘   │ │
│  │                                         │                                            │ │
│  │  ┌───────────────────────────────────────────────────────────────────────────────┐   │ │
│  │  │                      file_extractor.py (Document Parser)                      │   │ │
│  │  ├───────────────────────────────────────────────────────────────────────────────┤   │ │
│  │  │  • extract_text_from_file() → Routes to appropriate extractor                 │   │ │
│  │  │  • extract_from_txt()       → Plain text extraction                           │   │ │
│  │  │  • extract_from_pdf()       → PDF extraction using pypdf                      │   │ │
│  │  │  • extract_from_docx()      → Word document extraction                        │   │ │
│  │  │  • extract_from_excel()     → Excel extraction using openpyxl                 │   │ │
│  │  │  • extract_from_image()     → Image base64 encoding for vision models         │   │ │
│  │  └───────────────────────────────────────────────────────────────────────────────┘   │ │
│  │                                                                                      │ │
│  │  ┌───────────────────────────────────────────────────────────────────────────────┐   │ │
│  │  │                              templates/ (HTML Pages)                          │   │ │
│  │  ├───────────────────────────────────────────────────────────────────────────────┤   │ │
│  │  │  • index.html  → Issue submission form with file upload                       │   │ │
│  │  │  • result.html → Triage results display page                                  │   │ │
│  │  │  • about.html  → System information and documentation                         │   │ │
│  │  └───────────────────────────────────────────────────────────────────────────────┘   │ │
│  │                                                                                      │ │
│  │  ┌───────────────────────────────────────────────────────────────────────────────┐   │ │
│  │  │                            static/ (Assets)                                   │   │ │
│  │  ├───────────────────────────────────────────────────────────────────────────────┤   │ │
│  │  │  • css/style.css → Styling for web interface                                  │   │ │
│  │  │  • js/main.js    → Client-side JavaScript                                     │   │ │
│  │  └───────────────────────────────────────────────────────────────────────────────┘   │ │
│  │                                                                                      │ │
│  └──────────────────────────────────────────────────────────────────────────────────────┘ │
│                                              │                                            │
└──────────────────────────────────────────────┼────────────────────────────────────────────┘
                                               │
                                               ▼ Direct Python Import
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                                     MCP SERVER LAYER                                      │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                           │
│  ┌──────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                        MCP SERVER (mcp_server/)                                      │ │
│  ├──────────────────────────────────────────────────────────────────────────────────────┤ │
│  │                                                                                      │ │
│  │  ┌────────────────────────────────────────────────────────────────────────────────┐  │ │
│  │  │                      server.py (FastMCP Server Entry Point)                    │  │ │
│  │  ├────────────────────────────────────────────────────────────────────────────────┤  │ │
│  │  │  FastMCP("intake-triage-server")                                               │  │ │
│  │  │                                                                                │  │ │
│  │  │  MCP TOOLS:                                                                    │  │ │
│  │  │  ├── @mcp.tool() classify_intake_tool()      → Classification endpoint         │  │ │
│  │  │  ├── @mcp.tool() score_severity_tool()       → Severity scoring endpoint       │  │ │
│  │  │  ├── @mcp.tool() route_case_tool()           → Case routing endpoint           │  │ │
│  │  │  ├── @mcp.tool() get_routing_rules_tool()    → Get routing configuration       │  │ │
│  │  │  ├── @mcp.tool() process_intake_full()       → Full pipeline in one call       │  │ │
│  │  │  ├── @mcp.tool() list_industries()           → List available industries       │  │ │
│  │  │  └── @mcp.tool() get_industry_info()         → Get industry details            │  │ │
│  │  │                                                                                │  │ │
│  │  │  MCP RESOURCES:                                                                │  │ │
│  │  │  ├── @mcp.resource("intake://queues")        → All intake queues               │  │ │
│  │  │  ├── @mcp.resource("intake://queues/{ind}")  → Industry-specific queue         │  │ │
│  │  │  ├── @mcp.resource("intake://taxonomy/{i}")  → Category taxonomy               │  │ │
│  │  │  ├── @mcp.resource("intake://routing/{i}")   → Routing configuration           │  │ │
│  │  │  └── @mcp.resource("intake://industries")    → List all industries             │  │ │
│  │  │                                                                                │  │ │
│  │  │  MCP PROMPTS:                                                                  │  │ │
│  │  │  ├── @mcp.prompt() classify_intake_prompt()  → Classification prompt           │  │ │
│  │  │  └── @mcp.prompt() triage_decision_prompt()  → Triage summary prompt           │  │ │
│  │  └────────────────────────────────────────────────────────────────────────────────┘  │ │
│  │                                         │                                            │ │
│  │  ┌───────────────────────────────────────────────────────────────────────────────┐   │ │
│  │  │                   config_loader.py (Configuration Management)                 │   │ │
│  │  ├───────────────────────────────────────────────────────────────────────────────┤   │ │
│  │  │  class ConfigLoader:                                                          │   │ │
│  │  │  ├── list_industries()          → List available YAML configs                 │   │ │
│  │  │  ├── load_config()              → Load and cache industry config              │   │ │
│  │  │  ├── load_generic_config()      → Load arbitrary YAML files                   │   │ │
│  │  │  ├── get_categories()           → Get category definitions                    │   │ │
│  │  │  ├── get_severity_rules()       → Get severity rule definitions               │   │ │
│  │  │  ├── get_risk_flags()           → Get risk flag keywords                      │   │ │
│  │  │  ├── get_routing_rules()        → Get routing team rules                      │   │ │
│  │  │  └── get_sampling_thresholds()  → Get confidence thresholds                   │   │ │
│  │  │                                                                               │   │ │
│  │  │  Helper Functions:                                                            │   │ │
│  │  │  ├── get_config_loader()        → Singleton accessor                          │   │ │
│  │  │  ├── load_config()              → Convenience function                        │   │ │
│  │  │  └── load_generic_config()      → Plug-and-play YAML loader                   │   │ │
│  │  └───────────────────────────────────────────────────────────────────────────────┘   │ │
│  │                                                                                      │ │
│  └──────────────────────────────────────────────────────────────────────────────────────┘ │
│                                              │                                            │
└──────────────────────────────────────────────┼────────────────────────────────────────────┘
                                               │
                      ┌────────────────────────┼────────────────────────┐
                      ▼                        ▼                        ▼
┌─────────────────────────────┐ ┌─────────────────────────────┐ ┌─────────────────────────────┐
│      TOOLS LAYER            │ │      LLM LAYER              │ │    ADAPTERS LAYER           │
│     (mcp_server/tools/)     │ │    (mcp_server/llm/)        │ │  (mcp_server/adapters/)     │
├─────────────────────────────┤ ├─────────────────────────────┤ ├─────────────────────────────┤
│                             │ │                             │ │                             │
│ ┌─────────────────────────┐ │ │ ┌─────────────────────────┐ │ │ ┌─────────────────────────┐ │
│ │    classify.py          │ │ │ │   groq_client.py        │ │ │ │ generic_yaml_adapter.py │ │
│ ├─────────────────────────┤ │ │ ├─────────────────────────┤ │ │ ├─────────────────────────┤ │
│ │ classify_intake()       │ │ │ │ class GroqClient:       │ │ │ │ class GenericYAMLAdapter│ │
│ │ ├─ Auto-detect industry │ │ │ │ ├─ classify_text()      │ │ │ │ ├─ KEY_MAPPINGS         │ │
│ │ ├─ Load config          │ │ │ │ ├─ analyze_severity()   │ │ │ │ ├─ CATEGORY_FIELD_MAP   │ │
│ │ ├─ Call LLM for classif │ │ │ │ ├─ detect_industry()    │ │ │ │ ├─ SEVERITY_LEVEL_MAP   │ │
│ │ ├─ Check thresholds     │ │ │ │ ├─ _fallback_classify() │ │ │ │ ├─ is_standard_format() │ │
│ │ └─ Return result        │ │ │ │ ├─ _fallback_severity() │ │ │ │ ├─ detect_schema()      │ │
│ │                         │ │ │ │ └─ _fallback_detect()   │ │ │ │ ├─ normalize_config()   │ │
│ │ get_category_info()     │ │ │ │                         │ │ │ │ ├─ normalize_categories │ │
│ └─────────────────────────┘ │ │ │ Models Used:            │ │ │ │ ├─ normalize_severity   │ │
│                             │ │ │ ├─ llama-3.3-70b        │ │ │ │ ├─ normalize_routing    │ │
│ ┌─────────────────────────┐ │ │ │ └─ llama-4-scout-17b    │ │ │ │ └─ discover_schema_llm  │ │
│ │    severity.py          │ │ │ │     (vision)            │ │ │ └─────────────────────────┘ │
│ ├─────────────────────────┤ │ │ └─────────────────────────┘ │ │                             │
│ │ score_severity()        │ │ │                             │ │ Enables plug-and-play       │
│ │ ├─ Load severity rules  │ │ │ ┌─────────────────────────┐ │ │ for any YAML structure      │
│ │ ├─ Load risk flags      │ │ │ │   gemini_client.py      │ │ │                             │
│ │ ├─ Call LLM for scoring │ │ │ ├─────────────────────────┤ │ └─────────────────────────────┘
│ │ ├─ Check escalation     │ │ │ │ class GeminiClient:     │ │
│ │ └─ Calculate SLA mult   │ │ │ │ ├─ classify_text()      │ │
│ │                         │ │ │ │ ├─ analyze_severity()   │ │
│ │ get_severity_thresholds │ │ │ │ ├─ detect_industry()    │ │
│ │ check_risk_flags()      │ │ │ │ └─ _fallback_* methods  │ │
│ └─────────────────────────┘ │ │ │                         │ │
│                             │ │ │ Model Used:             │ │
│ ┌─────────────────────────┐ │ │ │ └─ gemini-2.5-flash     │ │
│ │    routing.py           │ │ │ └─────────────────────────┘ │
│ ├─────────────────────────┤ │ │                             │
│ │ route_case()            │ │ └─────────────────────────────┘
│ │ ├─ Load routing rules   │ │
│ │ ├─ Match conditions:    │ │
│ │ │  ├─ Category match    │ │
│ │ │  ├─ Severity min      │ │
│ │ │  └─ Risk flag match   │ │
│ │ ├─ Calculate SLA        │ │
│ │ └─ Return assignment    │ │
│ │                         │ │
│ │ get_routing_rules()     │ │
│ │ get_available_teams()   │ │
│ └─────────────────────────┘ │
│                             │
│ ┌─────────────────────────┐ │
│ │    __init__.py          │ │
│ ├─────────────────────────┤ │
│ │ Exports all tool funcs  │ │
│ └─────────────────────────┘ │
│                             │
└─────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    RESOURCES LAYER                                      │
│                                 (mcp_server/resources/)                                 │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│  ┌───────────────────────────────────────────────────────────────────────────────────┐  │
│  │                              queues.py (MCP Resources)                            │  │
│  ├───────────────────────────────────────────────────────────────────────────────────┤  │
│  │  • get_intake_queues()        → Returns queue info per industry                   │  │
│  │  • get_category_taxonomy()    → Returns complete category hierarchy               │  │
│  │  • get_routing_config()       → Returns full routing configuration                │  │
│  │  • list_available_industries()→ Returns list of industry names                    │  │
│  │  • get_industry_summary()     → Returns summary of industry config                │  │
│  └───────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                  CONFIGURATION LAYER                                     │
│                                      (configs/)                                          │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  Industry-Specific YAML Configuration Files (Plug-and-Play):                             │
│                                                                                          │
│  ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐ │
│  │  banking.yaml     │ │  healthcare.yaml  │ │  it_services.yaml │ │  retail.yaml      │ │
│  ├───────────────────┤ ├───────────────────┤ ├───────────────────┤ ├───────────────────┤ │
│  │ industry: banking │ │ industry: health  │ │ industry: it_svc  │ │ industry: retail  │ │
│  │ categories:       │ │ categories:       │ │ categories:       │ │ categories:       │ │
│  │   - id, name,     │ │   - id, name,     │ │   - id, name,     │ │   - id, name,     │ │
│  │     keywords,     │ │     keywords,     │ │     keywords,     │ │     keywords,     │ │
│  │     description   │ │     description   │ │     description   │ │     description   │ │
│  │ severity_rules:   │ │ severity_rules:   │ │ severity_rules:   │ │ severity_rules:   │ │
│  │   critical/high/  │ │   critical/high/  │ │   critical/high/  │ │   critical/high/  │ │
│  │   medium/low      │ │   medium/low      │ │   medium/low      │ │   medium/low      │ │
│  │ risk_flags:       │ │ risk_flags:       │ │ risk_flags:       │ │ risk_flags:       │ │
│  │   fraud, security │ │   safety, privacy │ │   security, data  │ │   fraud, safety   │ │
│  │ routing_rules:    │ │ routing_rules:    │ │ routing_rules:    │ │ routing_rules:    │ │
│  │   team, SLA, cond │ │   team, SLA, cond │ │   team, SLA, cond │ │   team, SLA, cond │ │
│  └───────────────────┘ └───────────────────┘ └───────────────────┘ └───────────────────┘ │
│                                                                                          │
│  ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐                       │
│  │  logistics.yaml   │ │  restaurant.yaml  │ │  education.yaml   │                       │
│  ├───────────────────┤ ├───────────────────┤ ├───────────────────┤                       │
│  │ (Same structure)  │ │ (Same structure)  │ │ (Same structure)  │                       │
│  └───────────────────┘ └───────────────────┘ └───────────────────┘                       │
│                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
Neutrinos-MCP-Hackathon/
│
├── configs/                          # Industry Configuration Files (YAML)
│   ├── banking.yaml                  # Banking industry config
│   ├── healthcare.yaml               # Healthcare industry config
│   ├── it_services.yaml              # IT Services industry config
│   ├── retail.yaml                   # Retail industry config
│   ├── logistics.yaml                # Logistics industry config
│   ├── restaurant.yaml               # Restaurant industry config
│   └── education.yaml                # Education industry config
│
├── mcp_client/                       # Frontend Client Application
│   ├── __init__.py                   # Package initialization
│   ├── app.py                        # FastAPI web application (Port 8001)
│   ├── file_extractor.py             # Document text extraction utility
│   ├── requirements.txt              # Client dependencies
│   ├── .env.example                  # Environment template
│   ├── templates/                    # Jinja2 HTML Templates
│   │   ├── index.html                # Main submission form
│   │   ├── result.html               # Results display page
│   │   └── about.html                # About/Documentation page
│   └── static/                       # Static Assets
│       ├── css/style.css             # Stylesheet
│       └── js/main.js                # Client-side JavaScript
│
├── mcp_server/                       # Backend MCP Server
│   ├── __init__.py                   # Package initialization
│   ├── server.py                     # FastMCP server entry point (Port 8000)
│   ├── config_loader.py              # Configuration management
│   ├── requirements.txt              # Server dependencies
│   ├── .env                          # API keys (GROQ, GEMINI)
│   ├── .env.example                  # Environment template
│   │
│   ├── tools/                        # MCP Tools (Core Business Logic)
│   │   ├── __init__.py               # Tool exports
│   │   ├── classify.py               # Classification tool
│   │   ├── severity.py               # Severity scoring tool
│   │   └── routing.py                # Case routing tool
│   │
│   ├── llm/                          # LLM Client Implementations
│   │   ├── __init__.py               # LLM exports
│   │   ├── groq_client.py            # Groq API client (Llama models)
│   │   └── gemini_client.py          # Google Gemini API client
│   │
│   ├── adapters/                     # Configuration Adapters
│   │   ├── __init__.py               # Adapter exports
│   │   └── generic_yaml_adapter.py   # Plug-and-play YAML normalizer
│   │
│   └── resources/                    # MCP Resources
│       ├── __init__.py               # Resource exports
│       └── queues.py                 # Queue/taxonomy resource providers
│
├── test_data/                        # Sample Test Files
│   ├── sample.pdf                    # Test PDF document
│   ├── Bill.webp                     # Test image
│   └── sample.doc                    # Test Word document
│
├── Dockerfile                        # Docker build configuration
├── docker-compose.yml                # Docker Compose setup
├── requirements.txt                  # Root dependencies
├── README.md                         # Project documentation
└── .env                              # Root environment file
```

---

## Detailed Application Flow

### 1. User Submits Issue (Entry Point)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ USER submits through Browser (http://localhost:8001) or cURL API            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   INPUT:                                                                    │
│   ┌───────────────────────────────────────────────────────────────────────┐ │
│   │ • issue_text: "My banking app got hacked and money was withdrawn"     │ │
│   │ • industry: "banking" (optional - can be auto-detected)               │ │
│   │ • llm_provider: "groq" or "gemini"                                    │ │
│   │ • files: [Bill.webp, sample.pdf] (optional attachments)               │ │
│   └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│   ENDPOINTS:                                                                │
│   • Web Form: POST /submit → Returns HTML (result.html)                     │
│   • JSON API: POST /api/submit → Returns JSON response                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
```

### 2. File Extraction (mcp_client/file_extractor.py)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ FILE EXTRACTION PHASE                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   For each uploaded file:                                                   │
│                                                                             │
│   ┌─────────────────┐    ┌─────────────────────────────────────────────────┐│
│   │ Check Extension │───►│ Route to appropriate extractor:                 ││
│   └─────────────────┘    │                                                 ││
│                          │  .txt  → extract_from_txt()   : UTF-8 decode    ││
│                          │  .pdf  → extract_from_pdf()   : pypdf library   ││
│                          │  .docx → extract_from_docx()  : python-docx     ││
│                          │  .xlsx → extract_from_excel() : openpyxl        ││
│                          │  .png/.jpg/.webp → extract_from_image():        ││
│                          │         Returns {text, base64_data, mime_type}  ││
│                          │         for multimodal LLM processing           ││
│                          └─────────────────────────────────────────────────┘│
│                                                                             │
│   OUTPUT:                                                                   │
│   • combined_text = issue_text + extracted text from all files              │
│   • images[] = list of {base64_data, mime_type, filename} for vision        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
```

### 3. Process with MCP Pipeline (3-Step Orchestration)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: CLASSIFICATION (mcp_server/tools/classify.py)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   classify_intake(text, industry, auto_detect_industry, llm_provider, imgs) │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ 1.1 Industry Detection (if not provided):                           │   │
│   │     ┌─────────────────────────────────────────────────────────────┐ │   │
│   │     │ LLM Client → detect_industry(text, available_industries)    │ │   │
│   │     │                                                             │ │   │
│   │     │ Prompt: "Analyze text and determine industry from:          │ │   │
│   │     │         banking, healthcare, it_services, retail..."        │ │   │
│   │     │                                                             │ │   │
│   │     │ Returns: {industry: "banking", confidence: 0.95}            │ │   │
│   │     └─────────────────────────────────────────────────────────────┘ │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ 1.2 Load Configuration:                                             │   │
│   │     config_loader.load_config(industry) → {categories, rules...}    │   │
│   │                                                                     │   │
│   │     If non-standard YAML → GenericYAMLAdapter.normalize_config()    │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ 1.3 Classify Text:                                                  │   │
│   │     ┌─────────────────────────────────────────────────────────────┐ │   │
│   │     │ LLM Client → classify_text(text, categories, industry, imgs)│ │   │
│   │     │                                                             │ │   │
│   │     │ If images present:                                          │ │   │
│   │     │   → Use vision model (llama-4-scout-17b or gemini-flash)    │ │   │
│   │     │   → Multimodal prompt with base64 images                    │ │   │
│   │     │                                                             │ │   │
│   │     │ Prompt: "Classify intake into categories:                   │ │   │
│   │     │         - fraud_dispute: Fraud and Dispute Resolution       │ │   │
│   │     │         - account_access: Account Access Issues..."         │ │   │
│   │     │                                                             │ │   │
│   │     │ Returns JSON: {category_id, category_name, confidence,      │ │   │
│   │     │               subcategory, explanation}                     │ │   │
│   │     └─────────────────────────────────────────────────────────────┘ │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ 1.4 Check Thresholds:                                               │   │
│   │     • confidence < 0.85 → requires_review = True                    │   │
│   │     • confidence < 0.60 → review_reason = "Low confidence"          │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   OUTPUT: {                                                                 │
│     industry: "banking",                                                    │
│     category_id: "fraud_dispute",                                           │
│     category_name: "Fraud and Dispute Resolution",                          │
│     confidence: 0.92,                                                       │
│     explanation: "Text mentions hacking and unauthorized withdrawal"        │
│   }                                                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 2: SEVERITY SCORING (mcp_server/tools/severity.py)                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   score_severity(text, category_id, industry, llm_provider)                 │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ 2.1 Load Severity Configuration:                                    │   │
│   │     severity_rules = config_loader.get_severity_rules(industry)     │   │
│   │     risk_flags = config_loader.get_risk_flags(industry)             │   │
│   │                                                                     │   │
│   │     severity_rules example:                                         │   │
│   │       critical: {score: 5, keywords: [hacked, stolen, fraud]}       │   │
│   │       high:     {score: 4, keywords: [unauthorized, suspicious]}    │   │
│   │       medium:   {score: 3, keywords: [issue, problem, error]}       │   │
│   │                                                                     │   │
│   │     risk_flags example:                                             │   │
│   │       fraud_risk: [fraud, stolen, hacked, phishing]                 │   │
│   │       regulatory: [lawsuit, legal, compliance, audit]               │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ 2.2 Analyze Severity:                                               │   │
│   │     ┌─────────────────────────────────────────────────────────────┐ │   │
│   │     │ LLM Client → analyze_severity(text, category, rules, flags) │ │   │
│   │     │                                                             │ │   │
│   │     │ Prompt: "Analyze severity. Category: fraud_dispute          │ │   │
│   │     │         SEVERITY LEVELS: Score 5 CRITICAL - hacked,stolen   │ │   │
│   │     │         RISK FLAGS: fraud_risk - fraud, stolen, hacked..."  │ │   │
│   │     │                                                             │ │   │
│   │     │ Returns JSON: {severity_score, severity_level, priority,    │ │   │
│   │     │               risk_flags_found, urgency_indicators}         │ │   │
│   │     └─────────────────────────────────────────────────────────────┘ │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ 2.3 Calculate Escalation & SLA:                                     │   │
│   │     • severity_score >= 4 OR risk_flags found → escalation = True   │   │
│   │     • SLA Multiplier:                                               │   │
│   │         Score 5: 0.25x (critical - fastest)                         │   │
│   │         Score 4: 0.50x                                              │   │
│   │         Score 3: 1.00x (normal)                                     │   │
│   │         Score 2: 1.50x                                              │   │
│   │         Score 1: 2.00x (minimal - slowest)                          │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   OUTPUT: {                                                                 │
│     severity_score: 5,                                                      │
│     severity_level: "critical",                                             │
│     priority: "urgent",                                                     │
│     risk_flags_found: ["fraud_risk"],                                       │
│     escalation_recommended: true,                                           │
│     sla_multiplier: 0.25                                                    │
│   }                                                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 3: CASE ROUTING (mcp_server/tools/routing.py)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   route_case(category_id, severity_score, industry, risk_flags)             │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ 3.1 Load Routing Rules:                                             │   │
│   │     routing_rules = config_loader.get_routing_rules(industry)       │   │
│   │                                                                     │   │
│   │     routing_rules example:                                          │   │
│   │       - name: fraud_team                                            │   │
│   │         display_name: Fraud Investigation Unit                      │   │
│   │         conditions: {categories: [fraud_dispute], severity_min: 4}  │   │
│   │         sla_hours: 4                                                │   │
│   │         escalation_path: fraud_manager                              │   │
│   │       - name: general_support                                       │   │
│   │         conditions: {default: true}                                 │   │
│   │         sla_hours: 24                                               │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ 3.2 Match Routing Rules:                                            │   │
│   │     For each rule in routing_rules:                                 │   │
│   │       ├── Check category_match: category_id in rule.categories      │   │
│   │       ├── Check severity_match: severity_score >= rule.severity_min │   │
│   │       └── Check risk_match: any risk_flag in rule.risk_flags        │   │
│   │                                                                     │   │
│   │     Select most specific matching rule (highest specificity score)  │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ 3.3 Calculate Final SLA:                                            │   │
│   │     adjusted_sla = base_sla_hours × sla_multiplier                  │   │
│   │     Example: 4 hours × 0.25 = 1 hour (critical fraud case)          │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   OUTPUT: {                                                                 │
│     assigned_team: "fraud_team",                                            │
│     team_display_name: "Fraud Investigation Unit",                          │
│     sla_hours: 1.0,                                                         │
│     escalation_path: "fraud_manager",                                       │
│     routing_reason: "Matched: category 'fraud_dispute', severity 5 >= 4"    │
│   }                                                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
```

### 4. Return Results to User

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ FINAL RESPONSE (Combined Results)                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   {                                                                         │
│     "success": true,                                                        │
│     "classification": {                                                     │
│       "industry": "banking",                                                │
│       "category_id": "fraud_dispute",                                       │
│       "category_name": "Fraud and Dispute Resolution",                      │
│       "confidence": 0.92,                                                   │
│       "explanation": "Text mentions hacking and unauthorized withdrawal"    │
│     },                                                                      │
│     "severity": {                                                           │
│       "severity_score": 5,                                                  │
│       "severity_level": "critical",                                         │
│       "priority": "urgent",                                                 │
│       "risk_flags_found": ["fraud_risk"],                                   │
│       "escalation_recommended": true                                        │
│     },                                                                      │
│     "routing": {                                                            │
│       "assigned_team": "fraud_team",                                        │
│       "team_display_name": "Fraud Investigation Unit",                      │
│       "sla_hours": 1.0,                                                     │
│       "escalation_path": "fraud_manager"                                    │
│     },                                                                      │
│     "summary": {                                                            │
│       "industry": "banking",                                                │
│       "category": "Fraud and Dispute Resolution",                           │
│       "severity_level": "critical",                                         │
│       "assigned_team": "Fraud Investigation Unit",                          │
│       "sla_hours": 1.0,                                                     │
│       "requires_review": false                                              │
│     }                                                                       │
│   }                                                                         │
│                                                                             │
│   For Web UI: Rendered in result.html with visual formatting                │
│   For API: Returns JSON directly                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## LLM Integration Details

### Provider Selection

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ LLM PROVIDER SELECTION                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   User selects llm_provider: "groq" or "gemini"                             │
│                                                                             │
│   ┌─────────────────────────────┐    ┌─────────────────────────────────────┐│
│   │     GROQ (Default)          │    │     GEMINI                          ││
│   ├─────────────────────────────┤    ├─────────────────────────────────────┤│
│   │ Text Analysis:              │    │ Text Analysis:                      ││
│   │   llama-3.3-70b-versatile   │    │   gemini-pro                        ││
│   │   (70B params, 128K ctx)    │    │   (~1M input tokens)                ││
│   │                             │    │                                     ││
│   │ Vision/Images:              │    │ Vision/Images:                      ││
│   │   llama-4-scout-17b-16e     │    │   gemini-2.5-flash                  ││
│   │   (17B params, vision)      │    │   (~1M input tokens)                ││
│   └─────────────────────────────┘    └─────────────────────────────────────┘│
│                                                                             │
│   Fallback: If LLM API fails → Keyword-based matching (lower confidence)    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Fallback Mechanisms

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ FALLBACK MECHANISMS (When LLM is unavailable)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   _fallback_classify():                                                     │
│   ├── Scan text for category keywords                                       │
│   ├── Count keyword matches per category                                    │
│   ├── Select category with most matches                                     │
│   └── Confidence capped at 0.7 (indicates fallback mode)                    │
│                                                                             │
│   _fallback_severity():                                                     │
│   ├── Scan text for severity keywords (critical, high, etc.)                │
│   ├── Check for risk flag keywords                                          │
│   └── Return basic severity assessment                                      │
│                                                                             │
│   _fallback_detect_industry():                                              │
│   ├── Industry-specific keyword sets:                                       │
│   │     banking: [bank, account, loan, credit, debit, atm...]               │
│   │     healthcare: [doctor, patient, medical, hospital...]                 │
│   │     it_services: [computer, laptop, password, network...]               │
│   └── Select industry with most keyword matches                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Plug-and-Play Configuration System

### GenericYAMLAdapter Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ GENERIC YAML ADAPTER (mcp_server/adapters/generic_yaml_adapter.py)          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Enables loading ANY YAML structure and normalizing to expected format     │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ KEY_MAPPINGS (Field Name Alternatives):                             │   │
│   │                                                                     │   │
│   │   'categories' ←─ categories, items, topics, types, issues,         │   │
│   │                    ticket_types, complaint_types, problem_types     │   │
│   │                                                                     │   │
│   │   'severity_rules' ←─ severity, priority_levels, urgency,           │   │
│   │                       importance, criticality, impact_levels        │   │
│   │                                                                     │   │
│   │   'routing_rules' ←─ routing, assignments, teams, queues,           │   │
│   │                      workflows, departments, escalation_rules       │   │
│   │                                                                     │   │
│   │   'risk_flags' ←─ risks, flags, indicators, triggers,               │   │
│   │                   warning_signs, alert_triggers                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ NORMALIZATION FLOW:                                                 │   │
│   │                                                                     │   │
│   │   1. load_yaml_file() → Parse YAML                                  │   │
│   │   2. is_standard_format() → Check if already normalized             │   │
│   │   3. detect_schema() → Map alternative keys to expected keys        │   │
│   │   4. normalize_categories() → Standardize category structure        │   │
│   │   5. normalize_severity_rules() → Standardize severity levels       │   │
│   │   6. normalize_routing_rules() → Standardize routing teams          │   │
│   │   7. normalize_risk_flags() → Standardize risk indicators           │   │
│   │   8. Return normalized config ready for use                         │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   Example: Custom YAML with non-standard keys                               │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ INPUT (custom format):           OUTPUT (normalized):               │   │
│   │                                                                     │   │
│   │ domain: finance                  industry: finance                  │   │
│   │ ticket_types:                    categories:                        │   │
│   │   - type: loans                    - id: loans                      │   │
│   │     words: [mortgage]              name: Loans                      │   │
│   │ priority_levels:                   keywords: [mortgage]             │   │
│   │   urgent: 5                      severity_rules:                    │   │
│   │ teams:                             critical: {score: 5}             │   │
│   │   - name: loan_dept              routing_rules:                     │   │
│   │                                    - name: loan_dept                │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Summary Diagram

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    USER      │────►│  MCP CLIENT  │────►│  MCP SERVER  │────►│  LLM APIs    │
│              │     │  (Port 8001) │     │  (Port 8000) │     │ (Groq/Gemini)│
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
       │                    │                    │                    │
       │                    │                    │                    │
       ▼                    ▼                    ▼                    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌───────────────┐
│ Issue Text   │     │ File Extract │     │ Config Load  │     │ Classification│
│ + Files      │     │ (PDF/DOC/IMG)│     │ (YAML Parse) │     │ Severity      │
│ + Industry   │     │              │     │              │     │ Industry Det  │
└──────────────┘     └──────────────┘     └──────────────┘     └───────────────┘
                                                │
                           ┌────────────────────┼────────────────────┐
                           ▼                    ▼                    ▼
                    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
                    │  CLASSIFY    │     │   SEVERITY   │     │   ROUTING    │
                    │  (Step 1)    │────►│   (Step 2)   │────►│   (Step 3)   │
                    │              │     │              │     │              │
                    │ • Industry   │     │ • Score 1-5  │     │ • Team       │
                    │ • Category   │     │ • Priority   │     │ • SLA        │
                    │ • Confidence │     │ • Risk Flags │     │ • Escalation │
                    └──────────────┘     └──────────────┘     └──────────────┘
                                                                      │
                                                                      ▼
                                                               ┌──────────────┐
                                                               │   RESPONSE   │
                                                               │              │
                                                               │ JSON/HTML    │
                                                               │ with full    │
                                                               │ triage info  │
                                                               └──────────────┘
```

---

## Technology Stack

| Layer               | Technology                           | Purpose                               |
| ------------------- | ------------------------------------ | ------------------------------------- |
| **Frontend**        | FastAPI + Jinja2                     | Web UI and API endpoints              |
| **MCP Server**      | FastMCP                              | Model Context Protocol implementation |
| **LLM - Groq**      | Llama 3.3 70B, Llama 4 Scout 17B     | Text and Vision classification        |
| **LLM - Gemini**    | Gemini 2.5 Flash                     | Alternative LLM provider              |
| **Config**          | YAML + Python                        | Industry configurations               |
| **File Processing** | pypdf, python-docx, openpyxl, Pillow | Document extraction                   |
| **Deployment**      | Docker                               | Containerization                      |

---

## Key Design Patterns

1. **Singleton Pattern**: `ConfigLoader`, `GroqClient`, `GeminiClient` use global singleton instances
2. **Adapter Pattern**: `GenericYAMLAdapter` normalizes arbitrary YAML structures
3. **Pipeline Pattern**: 3-step sequential processing (Classify → Severity → Route)
4. **Fallback Pattern**: LLM calls have keyword-based fallbacks
5. **Strategy Pattern**: Pluggable LLM providers (Groq/Gemini)
6. **Configuration-Driven**: All business logic derived from YAML configs
