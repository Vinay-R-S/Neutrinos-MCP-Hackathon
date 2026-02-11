# weather_mcp_server.py

from fastmcp import FastMCP
import httpx
from geopy.geocoders import Nominatim
import asyncio
from starlette.responses import PlainTextResponse

# Initialize the MCP server
mcp = FastMCP("weather")

# Custom route to validate MCP server is running
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    return PlainTextResponse("OK")

# Create the geolocator instance once
geolocator = Nominatim(user_agent="geocoding_app")


# Expose an async MCP tool that returns geocoded coordinates for a given city
@mcp.tool()
async def get_coordinates(city_name: str) -> dict:
    """
    Retrieve latitude and longitude for a city name using geopy.

    Args:
        city_name: The name of the city (e.g., "Tokyo" or "Paris")

    Returns:
        {"latitude": 35.6895, "longitude": 139.6917, "address": "Tokyo, Japan"}
        or {"error": "..."}
    """
    try:
        loop = asyncio.get_running_loop()

        location = await loop.run_in_executor(
            None,
            geolocator.geocode,
            city_name
        )

        if location:
            print(f"Coordinates for {city_name}: {location.latitude}, {location.longitude}")
            return {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "address": location.address
            }

        return {"error": f"Could not find coordinates for {city_name}"}

    except Exception as e:
        print(f"Geocoding Error: {e}")
        return {"error": f"Internal error during geocoding: {str(e)}"}


# Expose an async MCP tool that returns weather forecast for given coordinates
@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """
    Get current weather forecast using Open-Meteo API.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,wind_speed_10m",
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m"
    }

    timeout = httpx.Timeout(10.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            current = data.get("current", {})
            temp = current.get("temperature_2m")
            wind = current.get("wind_speed_10m")

            print(f"Current Weather at {latitude}, {longitude}: Temp={temp} C, Wind={wind} km/h")

            return (
                f"Current Weather at {latitude}, {longitude}:\n"
                f"Temperature: {temp} C\n"
                f"Wind Speed: {wind} km/h"
            )

        except Exception as e:
            return f"Error fetching weather data: {str(e)}"


# MCP resource: retrieve information about the given title
@mcp.resource("info://books/search/{title}")
async def search_book(title: str) -> str:
    """
    Fetch basic book information from Open Library based on title.
    """
    url = "https://openlibrary.org/search.json"
    params = {"q": title}

    timeout = httpx.Timeout(10.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            docs = data.get("docs", [])
            if not docs:
                return f"No books found for '{title}'."

            book = docs[0]  # Take first result
            book_title = book.get("title", "Unknown Title")
            author = ", ".join(book.get("author_name", ["Unknown Author"]))
            year = book.get("first_publish_year", "Unknown Year")

            return (
                "Book Found:\n"
                f"Title: {book_title}\n"
                f"Author(s): {author}\n"
                f"First Published: {year}"
            )

        except Exception as e:
            return f"Error fetching book data: {str(e)}"


if __name__ == "__main__":
    print("Starting the Weather MCP server...")
    mcp.run(transport="http", host="0.0.0.0", port=8000)
