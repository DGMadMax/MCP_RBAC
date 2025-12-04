"""
Weather MCP Server - Open-Meteo API (No API Key!)
Port: 8004
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
import httpx
import re

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)

# =============================================================================
# FastAPI App
# =============================================================================
app = FastAPI(
    title="Weather MCP Server",
    description="Weather data using Open-Meteo (no API key required)",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Indian City Coordinates
# =============================================================================
CITY_COORDS = {
    "bangalore": (12.9716, 77.5946),
    "bengaluru": (12.9716, 77.5946),
    "mumbai": (19.0760, 72.8777),
    "delhi": (28.7041, 77.1025),
    "new delhi": (28.7041, 77.1025),
    "chennai": (13.0827, 80.2707),
    "hyderabad": (17.3850, 78.4867),
    "pune": (18.5204, 73.8567),
    "kolkata": (22.5726, 88.3639),
    "ahmedabad": (23.0225, 72.5714),
    "jaipur": (26.9124, 75.7873),
    "lucknow": (26.8467, 80.9462),
    "kanpur": (26.4499, 80.3319),
    "nagpur": (21.1458, 79.0882),
    "indore": (22.7196, 75.8577),
    "thane": (19.2183, 72.9781),
    "bhopal": (23.2599, 77.4126),
    "visakhapatnam": (17.6868, 83.2185),
    "pimpri": (18.6298, 73.7997),
    "patna": (25.5941, 85.1376),
}


def extract_city_from_query(query: str) -> Optional[str]:
    """
    Extract Indian city name from query
    
    Args:
        query: User query
    
    Returns:
        City name if found, else None
    """
    query_lower = query.lower()
    
    # Direct city name match
    for city in CITY_COORDS.keys():
        if city in query_lower:
            return city
    
    return None


# =============================================================================
# Schemas
# =============================================================================
class WeatherRequest(BaseModel):
    query: str
    user_id: int


class WeatherResponse(BaseModel):
    success: bool
    city: Optional[str] = None
    temperature: Optional[float] = None
    windspeed: Optional[float] = None
    weathercode: Optional[int] = None
    formatted: Optional[str] = None
    error: Optional[str] = None


# =============================================================================
# Endpoints
# =============================================================================
@app.post("/weather", response_model=WeatherResponse)
async def get_weather(request: WeatherRequest):
    """
    Get weather using Open-Meteo API (NO API KEY!)
    
    Example query format:
    - "What's the weather in Bangalore?"
    - "Weather in Mumbai"
    - "Temperature in Delhi"
    """
    try:
        logger.info(f"Weather request from user {request.user_id}: {request.query}")
        
        # Extract city from query
        city = extract_city_from_query(request.query)
        
        if not city:
            return WeatherResponse(
                success=False,
                error="Could not identify city. Please mention an Indian city name."
            )
        
        # Get coordinates
        lat, lon = CITY_COORDS[city]
        
        # Call Open-Meteo API (NO API KEY!)
        async with httpx.AsyncClient() as client:
            response = await client.get(
                settings.open_meteo_url,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current_weather": True
                },
                timeout=10.0
            )
            
            response.raise_for_status()
            data = response.json()
        
        # Extract weather data
        weather = data.get("current_weather", {})
        temp = weather.get("temperature")
        windspeed = weather.get("windspeed")
        weathercode = weather.get("weathercode")
        
        # Format response
        formatted = (
            f"Weather in {city.title()}: "
            f"{temp}°C, Wind: {windspeed} km/h"
        )
        
        logger.info(f"Weather data retrieved for {city}: {temp}°C")
        
        return WeatherResponse(
            success=True,
            city=city.title(),
            temperature=temp,
            windspeed=windspeed,
            weathercode=weathercode,
            formatted=formatted
        )
        
    except Exception as e:
        logger.error(f"Weather request failed: {str(e)}")
        return WeatherResponse(
            success=False,
            error=str(e)
        )


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "Weather MCP Server",
        "port": 8004,
        "supported_cities": len(CITY_COORDS),
        "api_key_required": False
    }


# =============================================================================
# Main
# =============================================================================
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004, log_level="info")
