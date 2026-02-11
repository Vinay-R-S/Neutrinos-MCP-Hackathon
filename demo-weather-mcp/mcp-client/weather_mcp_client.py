# weather_mcp_client.py

import asyncio
import os

from google import genai
from google.genai import types
from fastmcp import Client

REMOTE_SERVER_URL = "http://localhost:8000/mcp"


async def main():
    print("Starting MCP Client...")

    book_name = input("Enter book name: ").strip()
    city_name = input("Enter the name of city to know the weather (e.g., Tokyo): ").strip()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found.")
        print("Linux/macOS: export GEMINI_API_KEY='YOUR_KEY'")
        return

    gemini = genai.Client(api_key=api_key)
    mcp_client = Client(REMOTE_SERVER_URL)

    try:
        async with mcp_client:
            await mcp_client.initialize()

            # STEP 1: Read book info
            print("\nFetching book info from MCP resource...\n")
            result = await mcp_client.read_resource(f"info://books/search/{book_name}")
            book_details = result[0].text if result and result[0].text else "No book details found."
            print(book_details)

            # STEP 2: Call MCP tool -> get_coordinates(city)
            print("\nFetching coordinates...\n")
            coord_result = await mcp_client.call_tool("get_coordinates", {"city_name": city_name})
            coord_text = coord_result.content[0].text if coord_result and coord_result.content else ""

            if "error" in coord_text.lower():
                print("Error while fetching coordinates:")
                print(coord_text)
                return

            # coord_text is a string, but server returns dict -> FastMCP converts it to text
            # We'll ask Gemini to extract lat/long cleanly from it
            extract_prompt = f"""
Extract latitude and longitude from this tool output.
Return ONLY in this exact format:
LAT=<value>
LON=<value>

Tool output:
{coord_text}
"""

            extract_response = await gemini.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=[types.Content(role="user", parts=[types.Part(text=extract_prompt)])],
            )

            extracted = extract_response.text.strip()
            lines = extracted.splitlines()

            lat = None
            lon = None

            for line in lines:
                if line.startswith("LAT="):
                    lat = float(line.replace("LAT=", "").strip())
                if line.startswith("LON="):
                    lon = float(line.replace("LON=", "").strip())

            if lat is None or lon is None:
                print("Failed to extract latitude/longitude from tool output.")
                print("Raw tool output:")
                print(coord_text)
                return

            print(f"Coordinates found: {lat}, {lon}")

            # STEP 3: Call MCP tool -> get_forecast(lat, lon)
            print("\nFetching weather forecast...\n")
            forecast_result = await mcp_client.call_tool(
                "get_forecast",
                {"latitude": lat, "longitude": lon}
            )

            forecast_text = (
                forecast_result.content[0].text
                if forecast_result and forecast_result.content
                else "No forecast data returned."
            )

            print("Tool Forecast Output:")
            print(forecast_text)

            # STEP 4: Ask Gemini to format final answer nicely
            final_prompt = f"""
You are given book info and live weather data.
Write a clean final answer in 4-6 lines.

Book Info:
{book_details}

Weather Info:
{forecast_text}
"""

            final_response = await gemini.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=[types.Content(role="user", parts=[types.Part(text=final_prompt)])],
            )

            print("\nFinal Answer:")
            print(final_response.text)

    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    asyncio.run(main())
