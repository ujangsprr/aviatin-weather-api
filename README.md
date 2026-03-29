# Aviation Weather API — AIRMETs, SIGMETs, PIREPs & Winds Aloft

[![RapidAPI](https://img.shields.io/badge/RapidAPI-SkyLink%20API-blue)](https://rapidapi.com/skylink-api-skylink-api-default/api/skylink-api)
[![Free Tier](https://img.shields.io/badge/Free%20Tier-1%2C000%20req%2Fmo-green)](https://rapidapi.com/skylink-api-skylink-api-default/api/skylink-api)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![JavaScript](https://img.shields.io/badge/JavaScript-Node.js-yellow)](https://nodejs.org/)

> Beyond METAR: get real-time hazardous weather advisories and pilot reports. AIRMETs, SIGMETs, Convective SIGMETs, PIREPs, and Winds Aloft — all in one clean JSON API. Free tier available.

The **SkyLink Advanced Aviation Weather API** covers the weather data that matters most for flight planning: where the turbulence and icing are right now (PIREPs), which airspace is hazardous (AIRMET/SIGMET), and what the winds and temperatures look like at cruise altitude (Winds Aloft).

---

## Endpoints Covered

| Endpoint | Data | Coverage |
|---|---|---|
| `/v3/weather/pireps` | Pilot-reported turbulence, icing, sky conditions | USA (FAA) |
| `/v3/weather/airsigmet` | AIRMET and SIGMET hazardous weather advisories | Global |
| `/v3/weather/winds-aloft` | Winds and temperatures at 3,000–45,000 ft | USA (FAA FD) |

---

## Features

### PIREPs (Pilot Reports)
- **Real pilot-reported turbulence** — type (light/moderate/severe/extreme), altitude
- **Icing reports** — type (rime/clear/mixed), intensity, altitude range
- **Sky condition** — cloud bases and tops as observed by pilots in flight
- **Temperature and wind** at altitude
- **Both UA (routine) and UUA (urgent) PIREPs**
- Search within a **geographic bounding box** and **time window** (1–24 hours)

### AIRMETs & SIGMETs
- **AIRMETs** — advisories for IFR conditions, mountain obscuration, moderate turbulence, moderate icing, low-level wind shear
- **SIGMETs** — severe turbulence, severe icing, volcanic ash, tropical cyclones, sandstorms
- **Convective SIGMETs** — active thunderstorm areas
- Filter by type: `AIRMET`, `SIGMET`, or both
- Bounding box **intersection** filter — get only advisories that overlap your flight area
- Global coverage (SIGMET), US FAA (AIRMET)

### Winds Aloft
- **9 standard altitude levels** — 3,000, 6,000, 9,000, 12,000, 18,000, 24,000, 30,000, 34,000, 39,000 ft
- Wind direction and speed at each level
- Temperature at altitude
- **Forecast hours** — current or 6/12/24-hour forecast
- **Level filter** — `low` (3K–12K), `high` (18K–45K), or `all`
- Source: FAA FD (Winds and Temperatures Aloft) product
- Coverage: USA airports

---

## Endpoints

```
GET /v3/weather/pireps?bbox=39,-78,42,-71&hours=3
GET /v3/weather/pireps?bbox=30,-100,48,-80&hours=6&type=UUA

GET /v3/weather/airsigmet?bbox=38,-90,45,-80
GET /v3/weather/airsigmet?bbox=38,-90,45,-80&type=SIGMET
GET /v3/weather/airsigmet?bbox=38,-90,45,-80&type=AIRMET

GET /v3/weather/winds-aloft?bbox=40,-80,42,-73&forecast_hour=12&level=low
GET /v3/weather/winds-aloft?bbox=40,-80,42,-73&level=all
```

---

## Quick Start

### Get Your Free API Key
Sign up at [RapidAPI — SkyLink API](https://rapidapi.com/skylink-api-skylink-api-default/api/skylink-api) — 1,000 free requests/month, no credit card required.

### Python — Get PIREPs (Turbulence Reports)

```python
import requests

headers = {
    "x-rapidapi-key": "YOUR_API_KEY",
    "x-rapidapi-host": "skylink-api.p.rapidapi.com"
}

# Get all PIREPs from the last 3 hours over the NE United States
params = {
    "bbox": "39,-78,42,-71",  # lat_min,lon_min,lat_max,lon_max
    "hours": 3
}
r = requests.get(
    "https://skylink-api.p.rapidapi.com/v3/weather/pireps",
    headers=headers,
    params=params
)

reports = r.json()["reports"]
print(f"{len(reports)} PIREPs in the last 3 hours")

for rep in reports:
    turb = rep.get("turbulence") or "Smooth"
    icing = rep.get("icing") or "No icing"
    print(f"  {rep['location']} FL{rep['altitude']} — "
          f"Turb: {turb} | Icing: {icing}")
```

### Python — Get SIGMETs for a Region

```python
# Get all active SIGMETs intersecting the North Atlantic
params = {
    "bbox": "30,-70,60,-10",  # North Atlantic
    "type": "SIGMET"
}
r = requests.get(
    "https://skylink-api.p.rapidapi.com/v3/weather/airsigmet",
    headers=headers,
    params=params
)

for advisory in r.json()["reports"]:
    print(f"[{advisory['bulletin_type']}] {advisory['observation']['type']}")
    print(f"  Valid: {advisory['valid_from']} → {advisory['valid_to']}")
    print(f"  {advisory['raw_text'][:100]}...")
```

### Python — Winds Aloft for Flight Planning

```python
# Get winds at all altitudes over the NE corridor
params = {
    "bbox": "40,-80,42,-73",
    "forecast_hour": 12,
    "level": "all"
}
r = requests.get(
    "https://skylink-api.p.rapidapi.com/v3/weather/winds-aloft",
    headers=headers,
    params=params
)

for station in r.json()["stations"][:3]:
    print(f"\nStation: {station['station']}")
    for level in station["winds"]:
        print(f"  FL{level['altitude_ft']//100:03d}: "
              f"{level['wind_dir']}° @ {level['wind_speed_kt']}kt, "
              f"Temp: {level['temp_c']}°C")
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');

const headers = {
  'x-rapidapi-key': 'YOUR_API_KEY',
  'x-rapidapi-host': 'skylink-api.p.rapidapi.com'
};

// Check for urgent PIREPs (UUA) over the Rockies
const { data } = await axios.get(
  'https://skylink-api.p.rapidapi.com/v3/weather/pireps',
  { headers, params: { bbox: '35,-115,45,-100', hours: 6, type: 'UUA' } }
);

if (data.reports.length === 0) {
  console.log('No urgent PIREPs — skies are smooth');
} else {
  data.reports.forEach(r => {
    console.log(`URGENT: ${r.location} FL${r.altitude} — ${r.turbulence}`);
  });
}
```

### cURL

```bash
# PIREPs over the midwest
curl "https://skylink-api.p.rapidapi.com/v3/weather/pireps?bbox=35,-100,45,-80&hours=3" \
  -H "x-rapidapi-key: YOUR_API_KEY" \
  -H "x-rapidapi-host: skylink-api.p.rapidapi.com"

# Active AIRMETs/SIGMETs
curl "https://skylink-api.p.rapidapi.com/v3/weather/airsigmet?bbox=25,-130,50,-60" \
  -H "x-rapidapi-key: YOUR_API_KEY" \
  -H "x-rapidapi-host: skylink-api.p.rapidapi.com"
```

---

## Response Schema

### PIREP

```json
{
  "reports": [
    {
      "type": "UA",
      "location": "KJFK",
      "time": "2026-03-29T14:22:00Z",
      "altitude": 28000,
      "aircraft_type": "B738",
      "turbulence": "MOD",
      "turbulence_type": "CAT",
      "icing": null,
      "sky_condition": "BKN 260",
      "temperature_c": -42,
      "wind_dir": 280,
      "wind_speed_kt": 95,
      "raw": "UA /OV KJFK/TM 1422/FL280/TP B738/TB MOD CAT/RM ZBW"
    }
  ]
}
```

### AIRMET/SIGMET

```json
{
  "reports": [
    {
      "bulletin_type": "AIRMET",
      "observation": {
        "type": "IFR",
        "intensity": "MOD"
      },
      "valid_from": "2026-03-29T15:00:00Z",
      "valid_to": "2026-03-29T21:00:00Z",
      "raw_text": "AIRMET SIERRA FOR IFR AND MTN OBSCN...",
      "area": {
        "type": "Polygon",
        "coordinates": [...]
      }
    }
  ]
}
```

---

## Use Cases

- **Preflight go/no-go decision tools** — show pilots exactly where turbulence and icing are reported
- **EFB (Electronic Flight Bag) backends** — weather overlay layer with PIREPs and SIGMETs
- **Turbulence mapping overlays** — visualize on a map using bounding box queries
- **UAV/drone BVLOS weather checks** — ensure airspace is clear before approving a drone flight
- **Dispatch system weather integration** — alert dispatchers to active SIGMETs on planned routes
- **Flight briefing automation** — combine with METAR/TAF and NOTAMs for a full briefing

---

## Related Repositories

- [metar-api](https://github.com/skylink-api/metar-api) — METAR current conditions and TAF forecasts
- [notam-api](https://github.com/skylink-api/notam-api) — real-time NOTAMs and TFRs
- [aviation-utilities-api](https://github.com/skylink-api/aviation-utilities-api) — AI-powered flight briefing that aggregates all weather sources
- [flight-tracking-api](https://github.com/skylink-api/flight-tracking-api) — see which aircraft are actually flying through hazardous areas

---

## GitHub Topics

`aviation-weather` `sigmet` `airmet` `pirep` `winds-aloft` `turbulence` `icing` `aviation-api` `weather-api` `python` `faa` `rest-api`

---

## Part of SkyLink API — The All-In-One Aviation Data API

All features are included in a single SkyLink API subscription. No juggling 5 different providers. One key, one schema, one bill.

- **Website**: https://skylinkapi.com
- **Full Docs**: https://skylinkapi.com/docs
- **RapidAPI**: https://rapidapi.com/skylink-api-skylink-api-default/api/skylink-api
- **Free Tier**: 1,000 requests/month — no credit card required
- **Coverage**: PIREPs/Winds Aloft: USA (FAA) | AIRMETs: USA | SIGMETs: Global
