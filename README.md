# Intelligent Intake and Triage System

This project is an Intelligent Intake Classification and Routing System built using the Model Context Protocol (MCP).

This README provides two ways to run the project:

1. UI Mode (Browser-based)
2. Terminal Mode (curl-based JSON)

Docker is required for the MCP backend server.

## 1) Requirements

- Python 3.11+
- Docker

## 2) Environment Setup

### 2.1 Create `.env`

From project root:

```bash
cp mcp_server/.env.example .env
```

Edit `.env`:

```ini
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

DEFAULT_INDUSTRY=banking
LOG_LEVEL=INFO
```

## 3) Backend (MCP Server) - Docker

### 3.1 Build Backend Image

```bash
docker build -t intake-triage-server .
```

### 3.2 Run Backend Container

```bash
docker run --rm -p 8000:8000 --env-file .env intake-triage-server
```

### 3.3 Verify Backend

```bash
curl -i http://127.0.0.1:8000/sse
```

## 4) Frontend (UI Client) - Browser Mode

The UI client is a FastAPI server that serves HTML/CSS/JS.

### 4.1 Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4.2 Install Dependencies

```bash
pip install -r mcp_client/requirements.txt
pip install -r mcp_server/requirements.txt
```

### 4.3 Run UI Client

Run the UI on port 8001:

```bash
python -m uvicorn mcp_client.app:app --host 0.0.0.0 --port 8001 --reload
```

### 4.4 Open UI in Browser

- Local machine: open
  - `http://127.0.0.1:8001/`

- HAWCC / cloud editor:
  - Forward/expose port `8001`
  - Open the generated public URL in your browser

### 4.4 Open UI in Browser

- Local machine: open
  - `http://127.0.0.1:8001/`

- HAWCC / cloud editor:
  - Forward/expose port `8001`
  - Open the generated public URL in your browser

## 5) Windows Setup (No Docker)

If you are on Windows and want to run without Docker, use the provided batch scripts.

### 5.1 One-Time Setup

Run `setup_windows.bat` to create the virtual environment and install all dependencies.

```cmd
setup_windows.bat
```

_Note: You still need to edit the `.env` file with your API keys after running setup._

### 5.2 Running the Project

**Terminal 1 (Backend):**

```cmd
run_backend.bat
```

**Terminal 2 (Client):**

```cmd
run_client.bat
```

The client will automatically open `http://127.0.0.1:8001/` in your browser.

## 5) UI Mode Usage (Browser)

1. Open: `http://127.0.0.1:8001/`
2. Enter Issue Description
3. Select Industry (optional)
4. Select AI Provider (Groq or Gemini)
5. Upload files (optional)
6. Click `Process Issue`

The result page will show:

- classification
- severity
- routing decision
- SLA and escalation path

## 6) Terminal Mode Usage (JSON)

Use the JSON endpoint:

- `POST /api/submit`

### 6.1 Submit Text Only

```bash
curl -s -X POST http://127.0.0.1:8001/api/submit \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "issue_text=My banking app got hacked and money was withdrawn" \
  --data-urlencode "industry=banking" \
  --data-urlencode "llm_provider=groq" | python -m json.tool
```

### 6.2 Upload Image

```bash
curl -s -X POST http://127.0.0.1:8001/api/submit \
  -F "issue_text=Please analyze this screenshot." \
  -F "industry=banking" \
  -F "llm_provider=groq" \
  -F "files=@test_data/Bill.webp" | python -m json.tool
```

### 6.3 Upload PDF

```bash
curl -s -X POST http://127.0.0.1:8001/api/submit \
  -F "issue_text=Please analyze the attached PDF complaint." \
  -F "industry=banking" \
  -F "llm_provider=groq" \
  -F "files=@test_data/sample.pdf" | python -m json.tool
```

### 6.4 Upload DOC / DOCX

```bash
curl -s -X POST http://127.0.0.1:8001/api/submit \
  -F "issue_text=Please analyze the attached Word document." \
  -F "industry=banking" \
  -F "llm_provider=groq" \
  -F "files=@test_data/sample.doc" | python -m json.tool
```

### 6.5 Upload Multiple Files

```bash
curl -s -X POST http://127.0.0.1:8001/api/submit \
  -F "issue_text=Analyze all attachments and triage the case." \
  -F "industry=banking" \
  -F "llm_provider=groq" \
  -F "files=@test_data/sample.pdf" \
  -F "files=@test_data/Bill.webp" | python -m json.tool
```

## 6.1) Windows PowerShell Commands

The above curl commands use Linux-style line continuation (`\`). For **Windows PowerShell**, use `curl.exe` (not `curl`, which is an alias for `Invoke-WebRequest`):

### Submit Text Only (PowerShell)

```powershell
curl.exe -s -X POST http://127.0.0.1:8001/api/submit -H "Content-Type: application/x-www-form-urlencoded" --data-urlencode "issue_text=My banking app got hacked and money was withdrawn" --data-urlencode "industry=banking" --data-urlencode "llm_provider=groq" | python -m json.tool
```

### Upload Image (PowerShell)

```powershell
curl.exe -s -X POST http://127.0.0.1:8001/api/submit -F "issue_text=Please analyze this screenshot." -F "industry=banking" -F "llm_provider=groq" -F "files=@test_data/Bill.webp" | python -m json.tool
```

### Upload PDF (PowerShell)

```powershell
curl.exe -s -X POST http://127.0.0.1:8001/api/submit -F "issue_text=Please analyze the attached PDF complaint." -F "industry=banking" -F "llm_provider=groq" -F "files=@test_data/sample.pdf" | python -m json.tool
```

### Upload Multiple Files (PowerShell)

```powershell
curl.exe -s -X POST http://127.0.0.1:8001/api/submit -F "issue_text=Analyze all attachments and triage the case." -F "industry=banking" -F "llm_provider=groq" -F "files=@test_data/sample.pdf" -F "files=@test_data/Bill.webp" | python -m json.tool
```

## 7) Supported Values

### 7.1 Industries

- empty (auto-detect)
- `banking`
- `education`
- `healthcare`
- `it_services`
- `logistics`
- `restaurant`
- `retail`

### 7.2 LLM Providers

- `groq`
- `gemini`

### 7.3 Supported File Types

- `.pdf`
- `.docx`, `.doc`
- `.txt`
- `.xlsx`, `.xls`
- `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp`

## 8) Useful Commands

### List test files

```bash
ls -l test_data
```

### Check client docs

```bash
curl -i http://127.0.0.1:8001/docs
curl -i http://127.0.0.1:8001/openapi.json
```

## 9) Quick Start Summary

Terminal 1 (Backend):

```bash
docker build -t intake-triage-server .
docker run --rm -p 8000:8000 --env-file .env intake-triage-server
```

Terminal 2 (Frontend/UI Client):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r mcp_client/requirements.txt
pip install -r mcp_server/requirements.txt
python -m uvicorn mcp_client.app:app --host 0.0.0.0 --port 8001 --reload
```

Browser:

- `http://127.0.0.1:8001/`

MCP Server:

```bash
fastmcp run mcp_server/server.py --transport sse --port 8000
```

MCP Client:

```bash
python -m uvicorn mcp_client.app:app --host 0.0.0.0 --port 8001 --reload
```

## 10) LLM Models Used

This project uses the following LLM models via API:

| Provider   | Use Case      | Model ID                                    | Parameters / Context     |
| ---------- | ------------- | ------------------------------------------- | ------------------------ |
| **Groq**   | Text Analysis | `llama-3.3-70b-versatile`                   | 70B params, 128K context |
| **Groq**   | Vision/Images | `meta-llama/llama-4-scout-17b-16e-instruct` | 17B params, 128K context |
| **Gemini** | Text Analysis | `gemini-2.5-flash`                          | ~1M input tokens         |
| **Gemini** | Vision/Images | `gemini-2.5-flash`                          | ~1M input tokens         |

> **Note:** Vision models are automatically selected when images are uploaded.
