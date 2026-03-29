"""
SkyLink API — Aviation Weather Briefing (PIREPs + AIRMET/SIGMET)
Fetches hazardous weather data for a route bounding box.

Usage:
  python weather_briefing.py --key YOUR_KEY --bbox "39,-78,42,-71"
  python weather_briefing.py --key YOUR_KEY --bbox "35,-115,45,-100" --hours 6
  python weather_briefing.py --key YOUR_KEY --bbox "30,-100,45,-80" --sigmets-only

Get your free API key: https://rapidapi.com/skylink-api-skylink-api-default/api/skylink-api
"""

import requests
import argparse


API_HOST = "skylink-api.p.rapidapi.com"


def get_headers(api_key: str) -> dict:
    return {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": API_HOST,
    }


def fetch_pireps(api_key: str, bbox: str, hours: int = 3) -> list:
    r = requests.get(
        f"https://{API_HOST}/v3/weather/pireps",
        headers=get_headers(api_key),
        params={"bbox": bbox, "hours": hours},
    )
    r.raise_for_status()
    return r.json().get("reports", [])


def fetch_airsigmets(api_key: str, bbox: str, report_type: str = None) -> list:
    params = {"bbox": bbox}
    if report_type:
        params["type"] = report_type
    r = requests.get(
        f"https://{API_HOST}/v3/weather/airsigmet",
        headers=get_headers(api_key),
        params=params,
    )
    r.raise_for_status()
    return r.json().get("reports", [])


def fetch_winds_aloft(api_key: str, bbox: str, level: str = "all") -> list:
    r = requests.get(
        f"https://{API_HOST}/v3/weather/winds-aloft",
        headers=get_headers(api_key),
        params={"bbox": bbox, "level": level},
    )
    r.raise_for_status()
    return r.json().get("stations", [])


def print_briefing(bbox: str, hours: int, pireps: list, advisories: list, winds: list):
    print(f"\n{'=' * 65}")
    print(f"  AVIATION WEATHER BRIEFING — BBox: {bbox}")
    print(f"{'=' * 65}")

    # PIREPs
    urgent = [p for p in pireps if p.get("type") == "UUA"]
    routine = [p for p in pireps if p.get("type") == "UA"]

    print(f"\n  PILOT REPORTS (Last {hours}h): {len(pireps)} total")
    if urgent:
        print(f"  *** {len(urgent)} URGENT PIREP(S) ***")
        for p in urgent:
            print(f"    [UUA] {p.get('location', '?')} FL{p.get('altitude', '?')} — "
                  f"Turb: {p.get('turbulence', 'None')} | Icing: {p.get('icing', 'None')}")
    for p in routine[:5]:
        print(f"    [UA]  {p.get('location', '?')} FL{p.get('altitude', '?')} — "
              f"Turb: {p.get('turbulence', 'None')} | Icing: {p.get('icing', 'None')}")
    if not pireps:
        print("    No PIREPs — skies reported smooth in this area")

    # AIRMETs/SIGMETs
    sigmets = [a for a in advisories if "SIGMET" in a.get("bulletin_type", "")]
    airmets = [a for a in advisories if "AIRMET" in a.get("bulletin_type", "")]

    print(f"\n  ADVISORIES: {len(advisories)} active ({len(sigmets)} SIGMETs, {len(airmets)} AIRMETs)")
    for s in sigmets:
        obs = s.get("observation", {})
        print(f"    [SIGMET] {obs.get('type', '?')} — "
              f"{s.get('valid_from', '?')} → {s.get('valid_to', '?')}")
    for a in airmets[:5]:
        obs = a.get("observation", {})
        print(f"    [AIRMET] {obs.get('type', '?')} — "
              f"{a.get('valid_from', '?')} → {a.get('valid_to', '?')}")
    if not advisories:
        print("    No active advisories in this area")

    # Winds Aloft summary
    if winds:
        print(f"\n  WINDS ALOFT: {len(winds)} station(s) reporting")
        sample = winds[0]
        print(f"    Sample ({sample.get('station', '?')}):")
        for level in sample.get("winds", [])[:5]:
            print(f"      FL{level.get('altitude_ft', 0)//100:03d}: "
                  f"{level.get('wind_dir', '?')}°@{level.get('wind_speed_kt', '?')}kt  "
                  f"{level.get('temp_c', '?')}°C")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SkyLink Aviation Weather Briefing")
    parser.add_argument("--key", required=True, help="Your RapidAPI key")
    parser.add_argument("--bbox", required=True,
                        help="Bounding box: lat_min,lon_min,lat_max,lon_max (e.g. 39,-78,42,-71)")
    parser.add_argument("--hours", type=int, default=3, help="PIREP lookback hours (default: 3)")
    parser.add_argument("--sigmets-only", action="store_true", help="Only fetch SIGMETs")
    parser.add_argument("--winds", action="store_true", help="Include winds aloft data")
    args = parser.parse_args()

    adv_type = "SIGMET" if args.sigmets_only else None

    pireps = fetch_pireps(args.key, args.bbox, args.hours)
    advisories = fetch_airsigmets(args.key, args.bbox, adv_type)
    winds = fetch_winds_aloft(args.key, args.bbox) if args.winds else []

    print_briefing(args.bbox, args.hours, pireps, advisories, winds)
