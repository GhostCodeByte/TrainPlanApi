# Straßenbahn Tool

Eine modulare Transit-API für Freiburg, die die Daten von [db.transport.rest](https://db.transport.rest/) nutzt. Das Projekt bietet sowohl klassische REST-Endpunkte als auch einen MCP-Server für Agenten-Workflows. Zusätzlich gibt es Hinweise zur lokalen Nutzung, zum Testen und zur Containerisierung.

---

## 🚀 Übersicht

- **REST-API** mit Endpunkten für Stationen, Suche, nächste Station, Abfahrten, Ankünfte, Routenplanung und Health-Check.
- **Serviceschicht** (`services/db_rest_service.py`) kapselt alle Interaktionen mit der db.transport.rest-API.
- **MCP-Server** (`mcp_server.py`) stellt dieselbe Funktionalität agentengerecht über Tools zur Verfügung.
- **Test-CLI** (`testApi.py`) erlaubt das schnelle Durchtesten aller Endpunkte.
- **Dockerfile** zum Erstellen eines Containers, der den MCP-Server startet.

---

## 🧱 Architekturüberblick

- `app.py` startet eine Flask-App und nutzt `DBRestService`, um Daten von der externen API zu holen.
- `services/db_rest_service.py` implementiert Suche, Radius-Abfragen, Abfahrten, Ankünfte und Routen mit zusätzlichen Helfern wie Distanzberechnung.
- `config.py` enthält die zentrale Konfiguration mit der Basis-URL.
- `mcp_server.py` registriert MCP-Tools, die dieselbe Service-Logik wiederverwenden.
- `testApi.py` ist ein vollständiges CLI-Testtool mit Farbgebung, das alle Endpunkte gegen einen laufenden Server prüft.

---

## 🧪 REST-API verwenden

1. **Umgebung vorbereiten**

   - Erstelle ein virtuelles Environment: `python -m venv .venv`
   - Aktiviere es: auf Linux/macOS `source .venv/bin/activate`, auf Windows `.venv\Scripts\activate`
   - Installiere Abhängigkeiten: `pip install -r requirements.txt`

2. **Server starten**

   - Führe `python app.py` aus. Die Flask-App läuft standardmäßig auf `http://localhost:5000`.

3. **Verfügbare Endpunkte**

   | Pfad                     | Zweck                                  | Parameter (Query)                                         |
   |--------------------------|----------------------------------------|-----------------------------------------------------------|
   | `/api/health`            | Health-Check                            | keine                                                     |
   | `/api/stations`          | Stationen in einem Radius               | `lat`, `lon`, `[radius=1000]`, `[limit=50]`               |
   | `/api/stations/search`   | Stationssuche nach Namen                | `q`, `[limit=10]`                                         |
   | `/api/stations/nearest`  | Nächste Station                         | `lat`, `lon`                                               |
   | `/api/departures`        | Abfahrten einer Station                 | `station`, `[time (ISO)]`, `[limit=20]`, `[duration=60]`  |
   | `/api/arrivals`          | Ankünfte einer Station                  | `station`, `[time (ISO)]`, `[limit=20]`, `[duration=60]`  |
   | `/api/route`             | Routenplanung zwischen zwei Stationen  | `from`, `to`, `[time (ISO)]`, `[limit=5]`                 |

   Jeder Endpunkt gibt standardisierte JSON-Antworten zurück, die Felder wie `count`, `stations` oder `departures` enthalten.

---

## 🤖 MCP-Server nutzen

Der MCP-Server stellt dieselbe Funktionalität über Tools zur Verfügung. So können Agenten oder Automatisierungen auf Transitdaten zugreifen.

1. **Server starten**: `python mcp_server.py`, dann lauscht FastMCP auf Stdio.

2. **Verfügbare Tools**

   - `get_stations(lat, lon, radius=1000, limit=20)`
   - `search_stations(query, limit=10)`
   - `get_nearest_station(lat, lon)`
   - `get_departures(station_id, time_iso=None, limit=10)`
   - `get_route(origin_id, destination_id, time_iso=None)`

   Alle Tools nutzen dieselbe Service-Klasse wie die REST-API, sodass Ergebnisse konsistent sind.

3. **Agent-Beispiel**  
   Agenten können beispielsweise `get_departures("8000107", time_iso="2024-01-01T08:00:00+00:00")` aufrufen und erhalten eine Liste strukturierter Abfahrten.

---

## 🐳 Docker

1. **Image bauen**: `docker build -t strassenbahn-tool .`

2. **Container starten**: `docker run -p 5000:5000 strassenbahn-tool`

   Der Container führt standardmäßig `python mcp_server.py` aus. Wenn stattdessen die REST-API benötigt wird, ändere den ENTRYPOINT auf `python app.py` und baue das Image neu.

---

## 🧰 Test-CLI (`testApi.py`)

`testApi.py` bietet folgende Kommandos:

- `health`
- `stations` (mit `--lat`, `--lon`, optional `--radius`, `--limit`)
- `search` (mit `--query`, optional `--limit`)
- `nearest` (mit `--lat`, `--lon`)
- `departures` (mit `--station`, optional `--time`, `--limit`)
- `route` (mit `--from`, `--to`, optional `--time`, `--limit`)
- `all` (führt alle Tests nacheinander aus)

Das Tool nutzt `requests` gegen `http://localhost:5000` und gibt farbige Ausgaben sowie eine Zusammenfassung der Testergebnisse.

---

## 🏗️ Erweiterungsmöglichkeiten

- Caching-Layer (Redis oder In-Memory) für häufige Abfragen.
- Authentifizierung (API-Key, JWT) vor den REST-Endpunkten.
- Wechsel zu `httpx` oder `aiohttp` für asynchrone Requests.
- Zusätzliche MCP-Tools wie `get_arrivals` ergänzen.

---

## 🔧 Konfiguration

Die API-Basisadresse wird in `config.py` über `Config.DB_REST_BASE_URL` gesetzt (standardmäßig `https://v6.db.transport.rest`).

---

## 📦 Abhängigkeiten

- `flask`
- `requests`
- `geopy`
- `mcp`
- `python-dotenv` (optional für Umgebungsvariablen)

---

## 🗺️ Fazit

Das Projekt bündelt REST-API, MCP-Tools und Docker-Betrieb zu einer einheitlichen Transitoberfläche für Freiburg. Du kannst direkt HTTP-Endpunkte nutzen oder über MCP-Tools Agenten ansteuern – beide Kanäle greifen auf dieselbe Service-Schicht zu, sodass Daten und Verhalten immer konsistent bleiben.