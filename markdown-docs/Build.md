# Project Build Order & Development Approach

This document explains the logical order in which this MCP-based Intelligent Intake Triage System was built, useful for understanding the architecture and explaining the development approach in interviews.

---

## Build Philosophy: Bottom-Up with Configuration-First

The project follows a **bottom-up, configuration-driven** approach where foundational layers are built first, then progressively higher layers that depend on them.

---

## Phase-by-Phase Build Order

```
┌────────────────────────────────────────────────────────────────────────────┐
│                           BUILD ORDER OVERVIEW                             │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PHASE 1: Configuration Foundation                                        │
│   ├── configs/*.yaml (Industry configuration files)                        │
│   └── config_loader.py (Configuration management)                          │
│                                                                            │
│   PHASE 2: LLM Integration Layer                                           │
│   ├── llm/groq_client.py (Groq API client)                                 │
│   └── llm/gemini_client.py (Gemini API client)                             │
│                                                                            │
│   PHASE 3: Core Business Logic (MCP Tools)                                 │
│   ├── tools/classify.py (Classification logic)                             │
│   ├── tools/severity.py (Severity scoring logic)                           │
│   └── tools/routing.py (Case routing logic)                                │
│                                                                            │
│   PHASE 4: Extensibility Layer                                             │
│   └── adapters/generic_yaml_adapter.py (Plug-and-play configs)             │
│                                                                            │
│   PHASE 5: MCP Server & Resources                                          │
│   ├── server.py (FastMCP server with tools/resources/prompts)              │
│   └── resources/queues.py (MCP resource providers)                         │
│                                                                            │
│   PHASE 6: Client Application                                              │
│   ├── app.py (FastAPI web application)                                     │
│   ├── file_extractor.py (Document processing)                              │
│   └── templates/*.html (Web UI)                                            │
│                                                                            │
│   PHASE 7: Deployment & Testing                                            │
│   ├── Dockerfile & docker-compose.yml                                      │
│   └── test_data/* (Sample files for testing)                               │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Phase Breakdown

### PHASE 1: Configuration Foundation

**Why Start Here?**  
Everything in this system is **configuration-driven**. Categories, severity rules, routing logic, and risk flags are all defined in YAML files. Starting here ensures the data structure is solid before writing any logic.

```
BUILD ORDER:
┌─────────────────────────────────────────────────────────────────────────┐
│ 1.1 Define YAML Schema                                                  │
│     └── Decide structure: categories, severity_rules, routing_rules     │
│                                                                         │
│ 1.2 Create First Industry Config (banking.yaml)                         │
│     ├── Define categories (fraud, account_access, loans, etc.)          │
│     ├── Define severity levels (critical/high/medium/low with keywords) │
│     ├── Define risk flags (fraud_risk, regulatory, etc.)                │
│     └── Define routing rules (team assignments, SLA, conditions)        │
│                                                                         │
│ 1.3 Build config_loader.py                                              │
│     ├── list_industries() - Scan configs/ folder                        │
│     ├── load_config() - Parse YAML with caching                         │
│     ├── get_categories() - Extract category list                        │
│     ├── get_severity_rules() - Extract severity definitions             │
│     ├── get_routing_rules() - Extract routing logic                     │
│     └── get_risk_flags() - Extract risk indicators                      │
│                                                                         │
│ 1.4 Add More Industry Configs                                           │
│     └── healthcare.yaml, it_services.yaml, retail.yaml, etc.            │
└─────────────────────────────────────────────────────────────────────────┘

KEY DECISIONS:
• Use YAML over JSON (more readable, supports comments)
• Implement config caching to avoid repeated file reads
• Make config structure generic enough for any industry
```

---

### PHASE 2: LLM Integration Layer

**Why Build This Before Tools?**  
The classification, severity, and routing tools need LLM capabilities. Building the LLM clients first creates a clean abstraction that tools can use without knowing which provider is active.

```
BUILD ORDER:
┌─────────────────────────────────────────────────────────────────────────┐
│ 2.1 Create LLM Client Interface (conceptual)                            │
│     ├── classify_text(text, categories, industry) -> category_result    │
│     ├── analyze_severity(text, rules, flags) -> severity_result         │
│     └── detect_industry(text, industries) -> industry_result            │
│                                                                         │
│ 2.2 Build groq_client.py                                                │
│     ├── Initialize Groq API with GROQ_API_KEY                           │
│     ├── classify_text() - Prompt engineering for classification         │
│     ├── analyze_severity() - Prompt for severity analysis               │
│     ├── detect_industry() - Prompt for industry detection               │
│     ├── Add vision model support (llama-4-scout-17b-16e)                │
│     └── Add fallback methods (_fallback_classify, etc.)                 │
│                                                                         │
│ 2.3 Build gemini_client.py                                              │
│     ├── Same interface as groq_client                                   │
│     ├── Use gemini-2.5-flash for text and vision                        │
│     └── Implement same fallback methods                                 │
│                                                                         │
│ 2.4 Test LLM Clients Independently                                      │
│     └── Verify JSON parsing, error handling, fallbacks                  │
└─────────────────────────────────────────────────────────────────────────┘

KEY DECISIONS:
• Support multiple LLM providers (strategy pattern)
• Always include fallback (keyword-based) for reliability
• Return structured JSON from LLM responses
• Use vision models only when images are present
```

---

### PHASE 3: Core Business Logic - MCP Tools

**Why Build Tools Before Server?**  
Tools contain the actual business logic. They should be testable independently before wrapping them in the MCP server. This follows the principle of separation of concerns.

```
BUILD ORDER:
┌─────────────────────────────────────────────────────────────────────────┐
│ 3.1 Build classify.py (Classification Tool)                             │
│     ├── classify_intake(text, industry, auto_detect, llm_provider)      │
│     ├── Auto-detect industry if not provided                            │
│     ├── Load categories from config                                     │
│     ├── Call LLM client for classification                              │
│     ├── Apply confidence thresholds                                     │
│     └── Return structured classification result                         │
│                                                                         │
│ 3.2 Build severity.py (Severity Scoring Tool)                           │
│     ├── score_severity(text, category_id, industry, llm_provider)       │
│     ├── Load severity rules and risk flags from config                  │
│     ├── Call LLM client for severity analysis                           │
│     ├── Calculate SLA multiplier based on score                         │
│     └── Determine if escalation is needed                               │
│                                                                         │
│ 3.3 Build routing.py (Case Routing Tool)                                │
│     ├── route_case(category_id, severity_score, industry, risk_flags)   │
│     ├── Load routing rules from config                                  │
│     ├── Match rules by category, severity, and risk flags               │
│     ├── Select most specific matching rule                              │
│     ├── Apply SLA adjustments based on severity                         │
│     └── Return team assignment with SLA and escalation path             │
│                                                                         │
│ 3.4 Create tools/__init__.py                                            │
│     └── Export all tool functions for easy importing                    │
└─────────────────────────────────────────────────────────────────────────┘

KEY DECISIONS:
• Each tool is a pure function (input -> output)
• Tools don't know about HTTP or MCP - they just process data
• Tools depend on config_loader and llm clients
• Keep tools focused: one responsibility each
```

---

### PHASE 4: Extensibility Layer

**Why Build This After Core Tools?**  
The adapter is for handling non-standard configurations. You need to first understand the standard format (from Phase 1) before building something that converts other formats to it.

```
BUILD ORDER:
┌─────────────────────────────────────────────────────────────────────────┐
│ 4.1 Define Key Mappings                                                 │
│     ├── 'categories' <- [items, topics, types, ticket_types, ...]       │
│     ├── 'severity_rules' <- [priority_levels, urgency, impact, ...]     │
│     ├── 'routing_rules' <- [assignments, teams, queues, workflows, ...] │
│     └── 'risk_flags' <- [risks, flags, indicators, triggers, ...]       │
│                                                                         │
│ 4.2 Build generic_yaml_adapter.py                                       │
│     ├── is_standard_format() - Check if already normalized              │
│     ├── detect_schema() - Map unknown keys to expected keys             │
│     ├── normalize_categories() - Standardize category structure         │
│     ├── normalize_severity_rules() - Standardize severity levels        │
│     ├── normalize_routing_rules() - Standardize team assignments        │
│     ├── normalize_risk_flags() - Standardize risk indicators            │
│     └── normalize_config() - Full pipeline                              │
│                                                                         │
│ 4.3 Integrate Adapter into config_loader.py                             │
│     ├── Add auto_normalize flag to load_config()                        │
│     └── Call adapter when loading non-standard YAML files               │
└─────────────────────────────────────────────────────────────────────────┘

KEY DECISIONS:
• Make the system "plug-and-play" for any YAML structure
• Use intelligent key mapping with synonyms
• Preserve original data while normalizing structure
```

---

### PHASE 5: MCP Server & Resources

**Why Build Server Now?**  
All the business logic (tools) and data access (config, resources) are ready. Now wrap them in the MCP protocol to expose them as standardized tools, resources, and prompts.

```
BUILD ORDER:
┌──────────────────────────────────────────────────────────────────────────┐
│ 5.1 Initialize FastMCP Server in server.py                               │
│     └── mcp = FastMCP("intake-triage-server")                            │
│                                                                          │
│ 5.2 Register MCP Tools                                                   │
│     ├── @mcp.tool() classify_intake_tool() - Wraps classify.py           │
│     ├── @mcp.tool() score_severity_tool() - Wraps severity.py            │
│     ├── @mcp.tool() route_case_tool() - Wraps routing.py                 │
│     └── @mcp.tool() process_intake_full() - Full pipeline                │
│                                                                          │
│ 5.3 Build resources/queues.py                                            │
│     ├── get_intake_queues() - Return queue/team info                     │
│     ├── get_category_taxonomy() - Return category hierarchy              │
│     ├── get_routing_config() - Return routing rules                      │
│     └── list_available_industries() - Return industry list               │
│                                                                          │
│ 5.4 Register MCP Resources                                               │
│     ├── @mcp.resource("intake://queues") - All queues                    │
│     ├── @mcp.resource("intake://queues/{industry}") - Per industry       │
│     ├── @mcp.resource("intake://taxonomy/{industry}") - Categories       │
│     └── @mcp.resource("intake://routing/{industry}") - Routing config    │
│                                                                          │
│ 5.5 Register MCP Prompts                                                 │
│     ├── @mcp.prompt() classify_intake_prompt() - Classification prompt   │
│     └── @mcp.prompt() triage_decision_prompt() - Summary prompt          │
│                                                                          │
│ 5.6 Add Server Run Configuration                                         │
│     └── if __name__ == "__main__": mcp.run()                             │
└──────────────────────────────────────────────────────────────────────────┘

KEY DECISIONS:
• Use FastMCP for simplified MCP server implementation
• Tools wrap existing functions (keep logic separate)
• Resources provide read-only access to configurations
• Prompts define reusable LLM instruction templates
```

---

### PHASE 6: Client Application

**Why Build Client Last (of core components)?**  
The client is the consumer of the MCP server. It needs the server to be fully functional before you can build and test the client properly.

```
BUILD ORDER:
┌─────────────────────────────────────────────────────────────────────────┐
│ 6.1 Build basic FastAPI app (app.py)                                    │
│     ├── Initialize FastAPI application                                  │
│     ├── Configure Jinja2 templates                                      │
│     ├── Configure static file serving                                   │
│     └── GET / - Render index.html                                       │
│                                                                         │
│ 6.2 Build file_extractor.py                                             │
│     ├── extract_from_txt() - Plain text                                 │
│     ├── extract_from_pdf() - Using pypdf                                │
│     ├── extract_from_docx() - Using python-docx                         │
│     ├── extract_from_excel() - Using openpyxl                           │
│     ├── extract_from_image() - Base64 encoding for vision               │
│     └── extract_text_from_file() - Router function                      │
│                                                                         │
│ 6.3 Build HTML Templates                                                │
│     ├── index.html - Issue submission form with file upload             │
│     ├── result.html - Display triage results                            │
│     └── about.html - System documentation                               │
│                                                                         │
│ 6.4 Implement API Endpoints                                             │
│     ├── POST /submit - Web form submission (returns HTML)               │
│     ├── POST /api/submit - JSON API (returns JSON)                      │
│     └── GET /api/industries - List available industries                 │
│                                                                         │
│ 6.5 Build process_with_mcp() Orchestration                              │
│     ├── Call classify_intake() from mcp_server                          │
│     ├── Call score_severity() with classification result                │
│     ├── Call route_case() with severity result                          │
│     └── Combine and return full result                                  │
│                                                                         │
│ 6.6 Add CSS Styling (static/css/style.css)                              │
│     └── Professional UI design                                          │
└─────────────────────────────────────────────────────────────────────────┘

KEY DECISIONS:
• Keep client thin - just orchestration and UI
• Support both web form and JSON API
• Handle file uploads with async processing
• Provide visual feedback on results
```

---

### PHASE 7: Deployment & Testing

**Why Last?**  
Deployment configuration depends on knowing all components and their dependencies. Testing requires a complete system.

```
BUILD ORDER:
┌─────────────────────────────────────────────────────────────────────────┐
│ 7.1 Create Dockerfile                                                   │
│     ├── Base image: python:3.11-slim                                    │
│     ├── Install dependencies                                            │
│     ├── Copy source code                                                │
│     └── CMD to run server                                               │
│                                                                         │
│ 7.2 Create docker-compose.yml                                           │
│     ├── Define mcp_server service (port 8000)                           │
│     ├── Define mcp_client service (port 8001)                           │
│     └── Configure environment variables                                 │
│                                                                         │
│ 7.3 Create Test Data                                                    │
│     ├── sample.pdf - Test PDF extraction                                │
│     ├── Bill.webp - Test image processing                               │
│     └── sample.doc - Test DOCX extraction                               │
│                                                                         │
│ 7.4 Create README.md                                                    │
│     ├── Setup instructions                                              │
│     ├── Usage examples                                                  │
│     └── API documentation                                               │
│                                                                         │
│ 7.5 End-to-End Testing                                                  │
│     ├── Test web UI flow                                                │
│     ├── Test API endpoints                                              │
│     ├── Test with different industries                                  │
│     ├── Test file upload scenarios                                      │
│     └── Test fallback mechanisms                                        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Dependency Graph

```
                    ┌─────────────────────────────────────────────────────┐
                    │                     PHASE 7                         │
                    │  Dockerfile, docker-compose.yml, test_data, README  │
                    └─────────────────────────────────────────────────────┘
                                              ▲
                                              │ depends on
                    ┌─────────────────────────────────────────────────────┐
                    │                     PHASE 6                         │
                    │       app.py, file_extractor.py, templates/         │
                    └─────────────────────────────────────────────────────┘
                                              ▲
                                              │ depends on
                    ┌─────────────────────────────────────────────────────┐
                    │                     PHASE 5                         │
                    │            server.py, resources/queues.py           │
                    └─────────────────────────────────────────────────────┘
                                              ▲
                                              │ depends on
          ┌───────────────────────────────────┼─────────────────────────────────┐
          │                                   │                                 │
┌─────────────────────────┐     ┌─────────────────────────┐     ┌─────────────────────────┐
│        PHASE 4          │     │        PHASE 3          │     │        PHASE 3          │
│  generic_yaml_adapter   │     │  classify.py            │     │  severity.py, routing.py│
└─────────────────────────┘     └─────────────────────────┘     └─────────────────────────┘
          │                                   │                                 │
          │                                   ▼                                 │
          │                     ┌─────────────────────────┐                     │
          │                     │        PHASE 2          │                     │
          │                     │ groq_client, gemini_client                    │
          │                     └─────────────────────────┘                     │
          │                                   │                                 │
          └───────────────────────────────────┼─────────────────────────────────┘
                                              ▼
                    ┌─────────────────────────────────────────────────────┐
                    │                     PHASE 1                         │
                    │         config_loader.py, configs/*.yaml            │
                    └─────────────────────────────────────────────────────┘
```

---

## Interview Explanation Script

> **Interviewer**: "How did you approach building this project?"

**Answer**:

"I followed a **bottom-up, configuration-driven** approach:

1. **Started with Configuration (Phase 1)**: I first defined the YAML schema for industry configurations. This includes categories, severity rules, routing rules, and risk flags. I built `config_loader.py` to load and manage these configurations. This gives us a solid data foundation.

2. **Built LLM Integration (Phase 2)**: Next, I created abstracted LLM clients for Groq and Gemini. This separation allows us to switch providers easily. Each client implements the same interface: `classify_text()`, `analyze_severity()`, and `detect_industry()`. I also added fallback methods using keyword matching for reliability.

3. **Developed Core Tools (Phase 3)**: With configs and LLM ready, I built the three core tools:
   - `classify.py` - Classifies intake text into categories
   - `severity.py` - Scores severity and identifies risk flags
   - `routing.py` - Routes cases to appropriate teams

4. **Added Extensibility (Phase 4)**: I built `GenericYAMLAdapter` to handle non-standard configuration formats. This makes the system plug-and-play for any industry.

5. **Created MCP Server (Phase 5)**: I wrapped everything in FastMCP, exposing tools, resources, and prompts following the Model Context Protocol standard.

6. **Built the Client (Phase 6)**: Finally, I created a FastAPI web application with file upload support, calling the MCP server for processing.

7. **Deployment (Phase 7)**: Dockerized everything for easy deployment.

This approach ensures each layer is testable independently, and changes to one layer don't break others."

---

## Key Design Principles Used

| Principle                  | Application                                     |
| -------------------------- | ----------------------------------------------- |
| **Separation of Concerns** | Config, LLM, Tools, Server, Client are separate |
| **Configuration-Driven**   | All business rules come from YAML files         |
| **Strategy Pattern**       | Pluggable LLM providers (Groq/Gemini)           |
| **Adapter Pattern**        | GenericYAMLAdapter normalizes any config format |
| **Fallback Pattern**       | Keyword-based fallbacks when LLM fails          |
| **Singleton Pattern**      | ConfigLoader and LLM clients use singletons     |
| **Pipeline Pattern**       | 3-step sequential processing                    |

---

## Time Estimate for Rebuilding

| Phase                    | Estimated Time |
| ------------------------ | -------------- |
| Phase 1: Configuration   | 2 days         |
| Phase 2: LLM Integration | 2 days         |
| Phase 3: Core Tools      | 3 days         |
| Phase 4: Extensibility   | 1 day          |
| Phase 5: MCP Server      | 2 days         |
| Phase 6: Client App      | 3 days         |
| Phase 7: Deployment      | 2 days         |
| **Total**                | **~15 days**   |
