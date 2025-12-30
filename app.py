from datetime import datetime

from flask import Flask, jsonify, request

from config import Config
from services.db_rest_service import DBRestService

app = Flask(__name__)
app.config.from_object(Config)

db_rest = DBRestService(Config.DB_REST_BASE_URL)


@app.route("/api/stations", methods=["GET"])
def get_stations():
    """
    Holt alle Stationen in einem Radius.

    Query-Parameter:
        lat (float): Breitengrad (required)
        lon (float): Längengrad (required)
        radius (int): Radius in Metern (default: 1000)
        limit (int): Max. Anzahl Ergebnisse (default: 50)

    Beispiel: /api/stations?lat=47.9990&lon=7.8421&radius=500
    """
    try:
        lat = request.args.get("lat", type=float)
        lon = request.args.get("lon", type=float)
        radius = request.args.get("radius", default=1000, type=int)
        limit = request.args.get("limit", default=50, type=int)

        if lat is None or lon is None:
            return jsonify({"error": "lat und lon sind erforderlich"}), 400

        stations = db_rest.get_nearby_stations(lat, lon, radius, limit)
        return jsonify(
            {
                "count": len(stations),
                "radius_meters": radius,
                "center": {"lat": lat, "lon": lon},
                "stations": stations,
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/stations/search", methods=["GET"])
def search_stations():
    """
    Sucht Stationen nach Name.

    Query-Parameter:
        q (str): Suchbegriff (required)
        limit (int): Max. Anzahl Ergebnisse (default: 10)

    Beispiel: /api/stations/search?q=Freiburg Hauptbahnhof
    """
    try:
        query = request.args.get("q")
        limit = request.args.get("limit", default=10, type=int)

        if not query:
            return jsonify({"error": "q (Suchbegriff) ist erforderlich"}), 400

        stations = db_rest.search_stations(query, limit)
        return jsonify(
            {
                "query": query,
                "count": len(stations),
                "stations": stations,
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/stations/nearest", methods=["GET"])
def get_nearest_station():
    """
    Findet die nächstgelegene Station.

    Query-Parameter:
        lat (float): Breitengrad (required)
        lon (float): Längengrad (required)

    Beispiel: /api/stations/nearest?lat=47.9990&lon=7.8421
    """
    try:
        lat = request.args.get("lat", type=float)
        lon = request.args.get("lon", type=float)

        if lat is None or lon is None:
            return jsonify({"error": "lat und lon sind erforderlich"}), 400

        station = db_rest.get_nearest_station(lat, lon)
        if station is None:
            return jsonify({"error": "Keine Station gefunden"}), 404

        return jsonify({"station": station})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/departures", methods=["GET"])
def get_departures():
    """
    Holt Abfahrten für eine Station.

    Query-Parameter:
        station (str): Station-ID (required), z.B. "8000107"
        time (str): Abfahrtszeit ISO-Format (default: jetzt)
        limit (int): Max. Anzahl Ergebnisse (default: 20)
        duration (int): Zeitfenster in Minuten (default: 60)

    Beispiel: /api/departures?station=8000107&limit=10
    """
    try:
        station = request.args.get("station")
        time_str = request.args.get("time")
        limit = request.args.get("limit", default=20, type=int)
        duration = request.args.get("duration", default=60, type=int)

        if not station:
            return jsonify({"error": "station ist erforderlich"}), 400

        departure_time = None
        if time_str:
            departure_time = datetime.fromisoformat(time_str)

        departures = db_rest.get_departures(station, departure_time, limit, duration)
        return jsonify(
            {
                "station_id": station,
                "count": len(departures),
                "departures": departures,
            }
        )

    except ValueError as e:
        return jsonify({"error": f"Ungültiges Zeitformat: {e}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/arrivals", methods=["GET"])
def get_arrivals():
    """
    Holt Ankünfte für eine Station.

    Query-Parameter:
        station (str): Station-ID (required)
        time (str): Ankunftszeit ISO-Format (default: jetzt)
        limit (int): Max. Anzahl Ergebnisse (default: 20)

    Beispiel: /api/arrivals?station=8000107&limit=10
    """
    try:
        station = request.args.get("station")
        time_str = request.args.get("time")
        limit = request.args.get("limit", default=20, type=int)
        duration = request.args.get("duration", default=60, type=int)

        if not station:
            return jsonify({"error": "station ist erforderlich"}), 400

        arrival_time = None
        if time_str:
            arrival_time = datetime.fromisoformat(time_str)

        arrivals = db_rest.get_arrivals(station, arrival_time, limit, duration)
        return jsonify(
            {
                "station_id": station,
                "count": len(arrivals),
                "arrivals": arrivals,
            }
        )

    except ValueError as e:
        return jsonify({"error": f"Ungültiges Zeitformat: {e}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/route", methods=["GET"])
def get_route():
    """
    Plant eine Route zwischen zwei Stationen.

    Query-Parameter:
        from (str): Startstation ID (required), z.B. "8000107"
        to (str): Zielstation ID (required)
        time (str): Abfahrtszeit ISO-Format (default: jetzt)
        limit (int): Max. Anzahl Routen (default: 5)

    Beispiel: /api/route?from=8000107&to=8000105
    """
    try:
        origin = request.args.get("from")
        destination = request.args.get("to")
        time_str = request.args.get("time")
        limit = request.args.get("limit", default=5, type=int)

        if not origin or not destination:
            return jsonify({"error": "from und to sind erforderlich"}), 400

        departure_time = None
        if time_str:
            departure_time = datetime.fromisoformat(time_str)

        routes = db_rest.get_route(origin, destination, departure_time, limit)
        return jsonify(
            {
                "origin": origin,
                "destination": destination,
                "count": len(routes),
                "routes": routes,
            }
        )

    except ValueError as e:
        return jsonify({"error": f"Ungültiges Zeitformat: {e}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health-Check Endpunkt."""
    return jsonify(
        {"status": "ok", "service": "Freiburg Transit API (db.transport.rest)"}
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
