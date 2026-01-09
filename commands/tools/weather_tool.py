"""Weather tool for the agent."""

import logging
import requests
from typing import Dict, Any, Optional
from core.tool import Tool

logger = logging.getLogger(__name__)


class WeatherTool(Tool):
    """Tool for getting weather information."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the weather tool.
        
        Args:
            api_key: OpenWeatherMap API key (if None, tool will return error when used)
        """
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
        # Default coordinates for Pennsylvania: 41.2033° N, 77.1945° W
        self.default_lat = 41.2033
        self.default_lon = -77.1945
    
    def name(self) -> str:
        """Get the tool name."""
        return "get_weather"
    
    def description(self) -> str:
        """Get the tool description."""
        return "Gets current weather information for a specified location using latitude and longitude. Returns temperature, conditions, humidity, wind speed, and other weather details. Default coordinates are for Pennsylvania (41.2033° N, 77.1945° W) if not specified."
    
    def parameters_schema(self) -> Dict[str, Any]:
        """Get the parameters schema."""
        return {
            "type": "object",
            "properties": {
                "latitude": {
                    "type": "number",
                    "description": "Latitude coordinate (e.g., 41.2033). Default is 41.2033 for Pennsylvania.",
                    "default": 40
                },
                "longitude": {
                    "type": "number",
                    "description": "Longitude coordinate (e.g., -77.1945). Default is -77.1945 for Pennsylvania. Note: West longitude is negative.",
                    "default": -75
                },
                "units": {
                    "type": "string",
                    "enum": ["metric", "imperial", "kelvin"],
                    "description": "Temperature units: 'metric' for Celsius, 'imperial' for Fahrenheit, 'kelvin' for Kelvin. Default is 'imperial'.",
                    "default": "imperial"
                }
            },
            "required": []
        }
    
    def execute(self, **kwargs) -> str:
        """Execute the weather query."""
        if not self.api_key:
            return "Error: Weather API key not configured. Please set WEATHER_API_KEY environment variable."
        
        lat = kwargs.get("latitude", self.default_lat)
        lon = kwargs.get("longitude", self.default_lon)
        units = kwargs.get("units", "imperial")
        
        try:
            # Build request parameters using lat/lon
            params = {
                "lat": lat,
                "lon": lon,
                "appid": self.api_key,
                "units": units
            }
            
            # Make API request
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract weather information
            city = data.get("name", f"{lat}, {lon}")
            country = data.get("sys", {}).get("country", "")
            temp = data.get("main", {}).get("temp", 0)
            feels_like = data.get("main", {}).get("feels_like", 0)
            humidity = data.get("main", {}).get("humidity", 0)
            pressure = data.get("main", {}).get("pressure", 0)
            description = data.get("weather", [{}])[0].get("description", "unknown")
            wind_speed = data.get("wind", {}).get("speed", 0)
            wind_deg = data.get("wind", {}).get("deg", 0)
            visibility = data.get("visibility", 0)
            
            # Determine temperature unit symbol
            if units == "metric":
                temp_unit = "°C"
                speed_unit = "m/s"
            elif units == "imperial":
                temp_unit = "°F"
                speed_unit = "mph"
            else:
                temp_unit = "K"
                speed_unit = "m/s"
            
            # Format visibility (convert from meters to miles for imperial)
            if units == "imperial" and visibility > 0:
                visibility_miles = visibility / 1609.34
                visibility_str = f"{visibility_miles:.1f} miles"
            elif visibility > 0:
                visibility_km = visibility / 1000
                visibility_str = f"{visibility_km:.1f} km"
            else:
                visibility_str = "unknown"
            
            # Format wind direction
            directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                         "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
            wind_direction = directions[int((wind_deg + 11.25) / 22.5) % 16] if wind_deg else "unknown"
            
            # Build response string
            result = f"Weather in {city}"
            if country:
                result += f", {country}"
            result += f": {description.capitalize()}. "
            result += f"Temperature: {temp:.1f}{temp_unit} (feels like {feels_like:.1f}{temp_unit}). "
            result += f"Humidity: {humidity}%. "
            result += f"Wind: {wind_speed:.1f} {speed_unit} {wind_direction}. "
            result += f"Pressure: {pressure} hPa. "
            result += f"Visibility: {visibility_str}."
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching weather data: {e}", exc_info=True)
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 401:
                    return "Error: Invalid weather API key"
                elif e.response.status_code == 404:
                    return f"Error: Weather data not found for coordinates {lat}, {lon}"
                else:
                    return f"Error: Weather API request failed with status {e.response.status_code}"
            return f"Error: Failed to fetch weather data - {str(e)}"
        except Exception as e:
            logger.error(f"Error in weather tool: {e}", exc_info=True)
            return f"Error getting weather: {str(e)}"

