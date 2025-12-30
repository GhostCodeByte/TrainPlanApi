from datetime import datetime
from typing import Optional

import requests
from geopy.distance import geodesic


class DBRestService:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def _make_request(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Sendet eine API-Anfrage und gibt JSON zurück."""
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def search_stations(self, query: str, limit: int = 10) -> list[dict]:
        """
        Sucht Stationen nach Name.

        Args:
            query: Suchbegriff
            limit: Maximale Anzahl der Ergebnisse

        Returns:
            Liste von Stationen
        """
        params = {
            "query": query,
            "results": limit,
            "stops": "true",
            "addresses": "false",
            "poi": "false",
        }

        data = self._make_request("locations", params)
        stations = []

        for item in data or []:
            if not item or item.get("type") not in ["stop", "station"]:
                continue

            location = item.get("location") or {}
            stations.append(
                {
                    "id": item.get("id") or "",
                    "name": item.get("name") or "",
                    "lat": location.get("latitude") or 0,
                    "lon": location.get("longitude") or 0,
                }
            )

        return stations

    def get_nearby_stations(
        self,
        lat: float,
        lon: float,
        radius: int = 1000,
        limit: int = 50,
    ) -> list[dict]:
        """
        Holt alle Stationen in einem Radius um einen Punkt.

        Args:
            lat: Breitengrad
            lon: Längengrad
            radius: Radius in Metern
            limit: Maximale Anzahl der Ergebnisse

        Returns:
            Liste von Stationen mit ID, Name, Koordinaten und Distanz
        """
        params = {
            "latitude": lat,
            "longitude": lon,
            "results": limit,
            "distance": radius,
        }

        data = self._make_request("locations/nearby", params)
        stations = []

        for item in data or []:
            if not item or item.get("type") not in ["stop", "station"]:
                continue

            location = item.get("location") or {}
            station_lat = location.get("latitude") or 0
            station_lon = location.get("longitude") or 0

            distance = geodesic((lat, lon), (station_lat, station_lon)).meters

            stations.append(
                {
                    "id": item.get("id") or "",
                    "name": item.get("name") or "",
                    "lat": station_lat,
                    "lon": station_lon,
                    "distance_meters": round(distance, 1),
                }
            )

        stations.sort(key=lambda x: x["distance_meters"])
        return stations

    def get_nearest_station(self, lat: float, lon: float) -> Optional[dict]:
        """
        Findet die nächstgelegene Station zu einem Punkt.

        Args:
            lat: Breitengrad
            lon: Längengrad

        Returns:
            Die nächste Station oder None
        """
        stations = self.get_nearby_stations(lat, lon, radius=5000, limit=1)
        return stations[0] if stations else None

    def get_departures(
        self,
        station_id: str,
        departure_time: Optional[datetime] = None,
        num_results: int = 20,
        duration: int = 60,
    ) -> list[dict]:
        """
        Holt Abfahrten für eine Station (Robuste Version).
        """
        params = {
            "results": num_results,
            "duration": duration,
            "bus": "true",
            "ferry": "true",
            "subway": "true",
            "tram": "true",
            "taxi": "false",
        }

        if departure_time:
            params["when"] = departure_time.isoformat()

        data = self._make_request(f"stops/{station_id}/departures", params)
        departures = []

        # Sicherheitscheck: Falls data kein Dict ist oder 'departures' fehlt
        if isinstance(data, list):
            dep_list = data
        else:
            dep_list = data.get("departures", [])

        for dep in dep_list:
            # FIX: Nutze "or {}", falls die API 'null' zurückgibt
            line = dep.get("line") or {}
            destination = dep.get("destination") or {}

            scheduled = dep.get("plannedWhen", "")
            estimated = dep.get("when", "")

            delay_minutes = 0
            if dep.get("delay") is not None:
                delay_minutes = int(dep.get("delay")) // 60

            # Fallback für Produkt/Mode
            mode = line.get("product", "")
            if not mode and line.get("mode"):
                mode = line.get("mode")

            # Fallback für Namen
            line_name = line.get("name", "?")

            # Ziel-Bestimmung
            dest_name = destination.get("name")
            if not dest_name:
                dest_name = dep.get("direction", "?")

            departures.append(
                {
                    "line": line_name,
                    "direction": dep.get("direction", ""),
                    "destination": dest_name,
                    "mode": mode,
                    "scheduled_time": scheduled,
                    "estimated_time": estimated or scheduled,
                    "delay_minutes": delay_minutes,
                    "platform": dep.get("platform", ""),
                }
            )

        return departures

    def get_arrivals(
        self,
        station_id: str,
        arrival_time: Optional[datetime] = None,
        num_results: int = 20,
        duration: int = 60,
    ) -> list[dict]:
        """
        Holt Ankünfte für eine Station (Robuste Version).
        """
        params = {
            "results": num_results,
            "duration": duration,
        }

        if arrival_time:
            params["when"] = arrival_time.isoformat()

        data = self._make_request(f"stops/{station_id}/arrivals", params)
        arrivals = []

        if isinstance(data, list):
            arr_list = data
        else:
            arr_list = data.get("arrivals", [])

        for arr in arr_list:
            # FIX: Nutze "or {}", falls die API 'null' zurückgibt
            line = arr.get("line") or {}

            scheduled = arr.get("plannedWhen", "")
            estimated = arr.get("when", "")

            delay_minutes = 0
            if arr.get("delay") is not None:
                delay_minutes = int(arr.get("delay")) // 60

            arrivals.append(
                {
                    "line": line.get("name", "?"),
                    "origin": arr.get("provenance", "?"),
                    "mode": line.get("product", ""),
                    "scheduled_time": scheduled,
                    "estimated_time": estimated or scheduled,
                    "delay_minutes": delay_minutes,
                    "platform": arr.get("platform", ""),
                }
            )

        return arrivals

    def get_route(
        self,
        origin: str,
        destination: str,
        departure_time: Optional[datetime] = None,
        num_results: int = 5,
    ) -> list[dict]:
        """
        Plant eine Route zwischen zwei Stationen.

        Args:
            origin: ID oder Name der Startstation
            destination: ID oder Name der Zielstation
            departure_time: Abfahrtszeit (default: jetzt)
            num_results: Anzahl der Routenvorschläge

        Returns:
            Liste von Routen
        """
        params = {
            "from": origin,
            "to": destination,
            "results": num_results,
            "stopovers": "true",
            "bus": "true",
            "ferry": "true",
            "subway": "true",
            "tram": "true",
        }

        if departure_time:
            params["departure"] = departure_time.isoformat()

        data = self._make_request("journeys", params)
        routes = []

        journeys = data.get("journeys", [])

        for journey in journeys:
            legs = []

            for leg in journey.get("legs", []):
                leg_data = self._parse_leg(leg)
                if leg_data:
                    legs.append(leg_data)

            if legs:
                start_time = legs[0].get("departure_time", "")
                end_time = legs[-1].get("arrival_time", "")

                # Dauer berechnen
                duration = 0
                if start_time and end_time:
                    try:
                        start_dt = datetime.fromisoformat(
                            start_time.replace("Z", "+00:00")
                        )
                        end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                        duration = int((end_dt - start_dt).total_seconds() / 60)
                    except ValueError:
                        pass

                transit_legs = [l for l in legs if l["type"] == "transit"]

                routes.append(
                    {
                        "departure_time": start_time,
                        "arrival_time": end_time,
                        "duration_minutes": duration,
                        "num_transfers": max(0, len(transit_legs) - 1),
                        "legs": legs,
                    }
                )

        return routes

    def _parse_leg(self, leg: dict) -> Optional[dict]:
        """Parst ein Leg (Fahrtabschnitt oder Fußweg)."""
        origin = leg.get("origin") or {}
        destination = leg.get("destination") or {}

        origin_name = origin.get("name") or "?"
        dest_name = destination.get("name") or "?"

        dep_time = leg.get("departure") or ""
        arr_time = leg.get("arrival") or ""

        # Fußweg
        if leg.get("walking"):
            return {
                "type": "walk",
                "origin": origin_name,
                "destination": dest_name,
                "departure_time": dep_time,
                "arrival_time": arr_time,
                "distance": leg.get("distance") or 0,
            }

        # Öffentliches Verkehrsmittel
        line = leg.get("line") or {}

        # Fallback für Produkt/Mode
        mode = line.get("product") or ""
        if not mode and line.get("mode"):
            mode = line.get("mode")

        return {
            "type": "transit",
            "line": line.get("name") or "?",
            "direction": leg.get("direction") or "",
            "mode": mode,
            "origin": origin_name,
            "destination": dest_name,
            "departure_time": dep_time,
            "arrival_time": arr_time,
        }
