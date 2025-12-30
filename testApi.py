#!/usr/bin/env python3
"""
CLI Test-Script für die Transit API (db.transport.rest Version).

Usage:
    python test_api.py stations --lat 47.999 --lon 7.842 --radius 500
    python test_api.py search --query "Freiburg"
    python test_api.py nearest --lat 47.999 --lon 7.842
    python test_api.py departures --station 8000107
    python test_api.py route --from 8000107 --to 8000105
    python test_api.py all
"""

import argparse
import sys
from datetime import datetime
from typing import Optional

import requests


class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    END = "\033[0m"


class TransitAPITester:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip("/")

    def _print_header(self, text: str):
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * 60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.HEADER}{text.center(60)}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 60}{Colors.END}\n")

    def _print_success(self, text: str):
        print(f"{Colors.GREEN}✓ {text}{Colors.END}")

    def _print_error(self, text: str):
        print(f"{Colors.RED}✗ {text}{Colors.END}")

    def _print_info(self, label: str, value: str):
        print(f"  {Colors.CYAN}{label}:{Colors.END} {value}")

    def _make_request(
        self, endpoint: str, params: Optional[dict] = None
    ) -> tuple[bool, dict]:
        url = f"{self.base_url}{endpoint}"
        try:
            print(f"{Colors.BLUE}→ GET {url}{Colors.END}")
            if params:
                print(f"  Params: {params}")

            response = requests.get(url, params=params, timeout=30)
            data = response.json()
            return response.status_code == 200, data

        except requests.exceptions.ConnectionError:
            return False, {"error": "Keine Verbindung zum Server"}
        except Exception as e:
            return False, {"error": str(e)}

    def test_health(self) -> bool:
        self._print_header("Health Check")
        success, data = self._make_request("/api/health")

        if success:
            self._print_success("API ist erreichbar")
            self._print_info("Service", data.get("service", "unknown"))
            return True
        else:
            self._print_error(f"API nicht erreichbar: {data.get('error')}")
            return False

    def test_stations(
        self, lat: float, lon: float, radius: int = 1000, limit: int = 10
    ) -> bool:
        self._print_header("Test: Stationen im Radius")

        params = {"lat": lat, "lon": lon, "radius": radius, "limit": limit}
        success, data = self._make_request("/api/stations", params)

        if success:
            self._print_success(f"{data.get('count', 0)} Stationen gefunden")
            self._print_info("Zentrum", f"{lat}, {lon}")
            self._print_info("Radius", f"{radius}m")

            print(f"\n{Colors.BOLD}Stationen:{Colors.END}")
            for station in data.get("stations", [])[:10]:
                print(
                    f"  • {station['name']} (ID: {station['id']}) - "
                    f"{station['distance_meters']}m"
                )
            return True
        else:
            self._print_error(f"Fehler: {data.get('error')}")
            return False

    def test_search(self, query: str, limit: int = 10) -> bool:
        self._print_header("Test: Stationssuche")

        params = {"q": query, "limit": limit}
        success, data = self._make_request("/api/stations/search", params)

        if success:
            self._print_success(f"{data.get('count', 0)} Stationen gefunden")
            self._print_info("Suche", query)

            print(f"\n{Colors.BOLD}Ergebnisse:{Colors.END}")
            for station in data.get("stations", []):
                print(f"  • {station['name']} (ID: {station['id']})")
            return True
        else:
            self._print_error(f"Fehler: {data.get('error')}")
            return False

    def test_nearest_station(self, lat: float, lon: float) -> bool:
        self._print_header("Test: Nächste Station")

        params = {"lat": lat, "lon": lon}
        success, data = self._make_request("/api/stations/nearest", params)

        if success:
            station = data.get("station", {})
            self._print_success("Nächste Station gefunden")
            self._print_info("Name", station.get("name", ""))
            self._print_info("ID", station.get("id", ""))
            self._print_info("Distanz", f"{station.get('distance_meters', 0)}m")
            return True
        else:
            self._print_error(f"Fehler: {data.get('error')}")
            return False

    def test_departures(
        self, station: str, time: Optional[str] = None, limit: int = 10
    ) -> bool:
        self._print_header("Test: Abfahrten")

        params = {"station": station, "limit": limit}
        if time:
            params["time"] = time

        success, data = self._make_request("/api/departures", params)

        if success:
            self._print_success(f"{data.get('count', 0)} Abfahrten gefunden")
            self._print_info("Station-ID", station)

            print(f"\n{Colors.BOLD}Abfahrten:{Colors.END}")
            for dep in data.get("departures", [])[:10]:
                delay_str = ""
                if dep.get("delay_minutes", 0) > 0:
                    delay_str = f" {Colors.RED}(+{dep['delay_minutes']}){Colors.END}"

                scheduled = dep.get("scheduled_time", "")
                try:
                    dt = datetime.fromisoformat(scheduled.replace("Z", "+00:00"))
                    time_str = dt.strftime("%H:%M")
                except ValueError:
                    time_str = scheduled[:5] if scheduled else "?"

                print(
                    f"  • {time_str} {Colors.CYAN}{dep.get('line', '?'):>8}{Colors.END} "
                    f"→ {dep.get('direction', '?')}{delay_str}"
                )
            return True
        else:
            self._print_error(f"Fehler: {data.get('error')}")
            return False

    def test_route(
        self,
        origin: str,
        destination: str,
        time: Optional[str] = None,
        limit: int = 3,
    ) -> bool:
        self._print_header("Test: Routenplanung")

        params = {"from": origin, "to": destination, "limit": limit}
        if time:
            params["time"] = time

        success, data = self._make_request("/api/route", params)

        if success:
            self._print_success(f"{data.get('count', 0)} Routen gefunden")
            self._print_info("Von", origin)
            self._print_info("Nach", destination)

            print(f"\n{Colors.BOLD}Routen:{Colors.END}")
            for i, route in enumerate(data.get("routes", []), 1):
                dep = route.get("departure_time", "")
                arr = route.get("arrival_time", "")
                duration = route.get("duration_minutes", 0)
                transfers = route.get("num_transfers", 0)

                try:
                    dep_str = datetime.fromisoformat(
                        dep.replace("Z", "+00:00")
                    ).strftime("%H:%M")
                    arr_str = datetime.fromisoformat(
                        arr.replace("Z", "+00:00")
                    ).strftime("%H:%M")
                except ValueError:
                    dep_str, arr_str = dep[:5] if dep else "?", arr[:5] if arr else "?"

                print(
                    f"\n  {Colors.BOLD}Route {i}:{Colors.END} "
                    f"{dep_str} → {arr_str} ({duration} min, {transfers} Umstieg(e))"
                )

                for leg in route.get("legs", []):
                    if leg.get("type") == "transit":
                        print(
                            f"    🚌 {Colors.CYAN}{leg.get('line', '?')}{Colors.END} "
                            f"{leg.get('origin', '?')} → {leg.get('destination', '?')}"
                        )
                    elif leg.get("type") == "walk":
                        print(
                            f"    🚶 {leg.get('origin', '?')} → {leg.get('destination', '?')}"
                        )
            return True
        else:
            self._print_error(f"Fehler: {data.get('error')}")
            return False

    def run_all_tests(self) -> bool:
        self._print_header("ALLE TESTS AUSFÜHREN")

        # Testdaten für Freiburg
        lat, lon = 47.9990, 7.8421
        station_id = "8000107"  # Freiburg Hbf
        destination_id = "8000105"  # Freiburg-Wiehre oder andere Station

        results = [
            ("Health Check", self.test_health()),
            ("Stationssuche", self.test_search("Freiburg", limit=5)),
            ("Stationen im Radius", self.test_stations(lat, lon, radius=1000)),
            ("Nächste Station", self.test_nearest_station(lat, lon)),
            ("Abfahrten", self.test_departures(station_id, limit=5)),
            ("Route", self.test_route(station_id, destination_id, limit=2)),
        ]

        # Zusammenfassung
        self._print_header("ZUSAMMENFASSUNG")

        passed = sum(1 for _, success in results if success)
        total = len(results)

        for name, success in results:
            if success:
                self._print_success(name)
            else:
                self._print_error(name)

        print(f"\n{Colors.BOLD}Ergebnis: {passed}/{total} Tests bestanden{Colors.END}")
        return passed == total


def main():
    parser = argparse.ArgumentParser(
        description="CLI Test-Tool für die Transit API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python test_api.py health
  python test_api.py stations --lat 47.999 --lon 7.842 --radius 500
  python test_api.py search --query "Freiburg"
  python test_api.py nearest --lat 47.999 --lon 7.842
  python test_api.py departures --station 8000107
  python test_api.py route --from 8000107 --to 8000105
  python test_api.py all

Wichtige Station-IDs für Freiburg:
  Freiburg(Breisgau) Hbf:  8000107
        """,
    )

    parser.add_argument("--url", default="http://localhost:5000")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("health")

    p = subparsers.add_parser("stations")
    p.add_argument("--lat", type=float, required=True)
    p.add_argument("--lon", type=float, required=True)
    p.add_argument("--radius", type=int, default=1000)
    p.add_argument("--limit", type=int, default=20)

    p = subparsers.add_parser("search")
    p.add_argument("--query", required=True)
    p.add_argument("--limit", type=int, default=10)

    p = subparsers.add_parser("nearest")
    p.add_argument("--lat", type=float, required=True)
    p.add_argument("--lon", type=float, required=True)

    p = subparsers.add_parser("departures")
    p.add_argument("--station", required=True)
    p.add_argument("--time")
    p.add_argument("--limit", type=int, default=10)

    p = subparsers.add_parser("route")
    p.add_argument("--from", dest="origin", required=True)
    p.add_argument("--to", dest="destination", required=True)
    p.add_argument("--time")
    p.add_argument("--limit", type=int, default=3)

    subparsers.add_parser("all")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    tester = TransitAPITester(args.url)

    commands = {
        "health": lambda: tester.test_health(),
        "stations": lambda: tester.test_stations(
            args.lat, args.lon, args.radius, args.limit
        ),
        "search": lambda: tester.test_search(args.query, args.limit),
        "nearest": lambda: tester.test_nearest_station(args.lat, args.lon),
        "departures": lambda: tester.test_departures(
            args.station, args.time, args.limit
        ),
        "route": lambda: tester.test_route(
            args.origin, args.destination, args.time, args.limit
        ),
        "all": lambda: tester.run_all_tests(),
    }

    success = commands[args.command]()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
