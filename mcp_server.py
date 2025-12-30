from datetime import datetime
from typing import Optional

from mcp.server.fastmcp import FastMCP

from config import Config
from services.db_rest_service import DBRestService

# Initialisierung des MCP Servers
mcp = FastMCP("Freiburg Transit API")

# Service Instanz (nutzt die existierende Logik)
# Wir nutzen die URL direkt oder aus Config
base_url = getattr(Config, "DB_REST_BASE_URL", "https://v6.db.transport.rest")
service = DBRestService(base_url)


@mcp.tool()
def get_stations(lat: float, lon: float, radius: int = 1000, limit: int = 20) -> str:
    """
    Sucht Haltestellen in einem Radius um eine Koordinate.
    Gibt eine Liste von Stationen mit ID, Name und Distanz zurück.
    """
    try:
        stations = service.get_nearby_stations(lat, lon, radius, limit)
        return str(stations)
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
def search_stations(query: str, limit: int = 10) -> str:
    """
    Sucht Haltestellen anhand eines Namens (z.B. 'Freiburg Hbf').
    Gibt eine Liste passender Stationen zurück.
    """
    try:
        stations = service.search_stations(query, limit)
        return str(stations)
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
def get_nearest_station(lat: float, lon: float) -> str:
    """
    Findet genau die eine, nächstgelegene Station zu den Koordinaten.
    """
    try:
        station = service.get_nearest_station(lat, lon)
        if station:
            return str(station)
        return "Keine Station gefunden."
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
def get_departures(
    station_id: str, time_iso: Optional[str] = None, limit: int = 10
) -> str:
    """
    Holt Abfahrten für eine Station-ID.
    Args:
        station_id: Die ID der Station (z.B. '8000107')
        time_iso: Optionaler Zeitstempel (ISO-Format), sonst 'jetzt'.
        limit: Anzahl der Ergebnisse.
    """
    try:
        dt = datetime.fromisoformat(time_iso) if time_iso else None
        departures = service.get_departures(station_id, dt, limit)
        return str(departures)
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
def get_route(
    origin_id: str, destination_id: str, time_iso: Optional[str] = None
) -> str:
    """
    Plant eine Route von A nach B.
    Args:
        origin_id: Start Station ID.
        destination_id: Ziel Station ID.
        time_iso: Abfahrtszeit (ISO), optional.
    """
    try:
        dt = datetime.fromisoformat(time_iso) if time_iso else None
        routes = service.get_route(origin_id, destination_id, dt)
        return str(routes)
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    # Startet den Server über Stdio (Standard Input/Output)
    mcp.run()
