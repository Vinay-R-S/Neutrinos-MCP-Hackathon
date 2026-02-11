# Use a lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server code
COPY weather_mcp_server.py .

# Command to run the server
# -u ensures unbuffered output (crucial for MCP to work over pipes)
ENTRYPOINT ["python", "-u", "weather_mcp_server.py"]
