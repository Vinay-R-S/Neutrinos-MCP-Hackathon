# Intelligent Intake and Triage System

An intelligent intake classification and routing system built on the Model Context Protocol (MCP). This system uses Large Language Models (LLMs) to analyze incoming requests, assess severity, and route them to the appropriate teams based on configurable rules.

## System Architecture

The project consists of two main components:

- **MCP Server**: The backend logic that provides tools for classification, severity scoring, and routing. It supports multiple LLM providers (Groq and Google Gemini).
- **Web Client**: A user-friendly web interface for submitting issues and viewing analysis results.

## Prerequisites

- Python 3.11 or higher
- Git

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Neutrinos-MCP-Hackathon
```

### 2. Set Up Virtual Environment

Create and activate a virtual environment to isolate dependencies:

**Windows:**

```bash
python -m venv .venv
.\.venv\Scripts\activate
```

**Linux/macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

Install the required packages for both the client and server:

```bash
pip install -r mcp_client/requirements.txt
pip install -r mcp_server/requirements.txt
```

## Configuration

### 1. Environment Variables

Create a `.env` file in the `mcp_server` directory to store your API keys. You can use the provided `.env.example` as a template.

```bash
cp mcp_server/.env.example mcp_server/.env
```

Edit `mcp_server/.env` and add your API keys:

```ini
# Groq API Key (Required for Groq provider)
GROQ_API_KEY=your_groq_api_key_here

# Google Gemini API Key (Required for Gemini provider)
GEMINI_API_KEY=your_gemini_api_key_here

# Optional Configuration
DEFAULT_INDUSTRY=banking
LOG_LEVEL=INFO
```

### 2. Obtaining API Keys

- **Groq API Key**: Sign up at [Groq Cloud Console](https://console.groq.com/) and create a new API key.
- **Google Gemini API Key**: Visit [Google AI Studio](https://aistudio.google.com/) and generate an API key.

### 3. Customizing Industry Rules

The system uses YAML configuration files to define valid categories, severity triggers, and routing rules for each industry. These are located in the `configs/` directory.

To add a new industry or modify an existing one:

1.  Create or edit a YAML file in the `configs/` directory (e.g., `configs/insurance.yaml`).
2.  Follow the structure of existing files (`banking.yaml`, `healthcare.yaml`) to define:
    - **Taxonomy**: Categories and subcategories.
    - **Severity Rules**: Keywords that modify severity scores.
    - **Risk Flags**: High-risk terms that trigger alerts.
    - **Routing Map**: Rules for assigning teams based on category and severity.

## Running the Application

To start the web application, run the following command from the project root:

```bash
python -m uvicorn mcp_client.app:app --reload --port 8000
```

The application will be available at: `http://localhost:8000`

## Usage Guide

1.  **Submit Issue**: Navigate to the home page. Enter the issue description and select the industry (optional).
2.  **Select AI Provider**: Choose your preferred AI provider (Groq or Gemini) from the dropdown.
3.  **Upload Files**: Optionally upload relevant documents or images.
4.  **View Results**: The system will display the classification, severity score, identified risk flags, and the assigned team.

## Project Structure

- `mcp_client/`: Web application frontend (HTML/CSS) and API routes.
- `mcp_server/`: Core logic, MCP tools, and LLM clients.
- `configs/`: YAML configuration files for different industries.

## Running Intake Triage MCP Server with Docker
This guide instructions on how to build and run the Intelligent Intake and Triage MCP Server in a Docker container.

## Prerequisites

- Docker
- Docker Compose (optional, for easier management)
- API Keys for Groq and/or Gemini

## Quick Start with Docker Compose

1.  **Environment Setup**: Ensure your `.env` file exists in the project root containing your API keys.

    ```bash
    cp mcp_server/.env.example .env
    # Edit .env and add GROQ_API_KEY and GEMINI_API_KEY
    ```

2.  **Build and Run**:

    ```bash
    docker-compose up --build
    ```

    > **Note:** If `docker-compose` is not found, try the modern command:
    >
    > ```bash
    > docker compose up --build
    > ```

    The MCP Server will start and listen on port **8000** for SSE connections.

## Manual Docker Build & Run

### 1. Build the Image

```bash
docker build -t intake-triage-server .
```

### 2. Run the Container

You can run the container with environment variables passed directly or via an env file.

```bash
docker run -p 8000:8000 \
  --env GROQ_API_KEY=your_key \
  --env GEMINI_API_KEY=your_key \
  intake-triage-server
```

or

```bash
docker run -p 8000:8000 --env-file .env intake-triage-server
```

## Configuration via Volume Mounts

To modify industry configurations without rebuilding the image, mount your local `configs/` directory to `/configs` in the container.

**Docker Run:**

```bash
docker run -p 8000:8000 \
  --env CONFIG_PATH=/configs \
  -v $(pwd)/configs:/configs \
  intake-triage-server
```

**Docker Compose:**
The provided `docker-compose.yml` already mounts `./configs` to `/configs` and sets `CONFIG_PATH`.

## Health Check

The container includes a health check running every 30 seconds. You can manually verify status:

```bash
curl http://localhost:8000/
```


## License

MIT License
