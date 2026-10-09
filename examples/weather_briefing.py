"""
SkyLink Direct API — Airport METAR and TAF

Usage:
  python3 examples/weather_briefing.py
  python3 examples/weather_briefing.py --icao WSSS
  python3 examples/weather_briefing.py --indonesia

Set SKYLINK_API_KEY in the project .env file.
"""

import argparse
import csv
import io
import json
import os
import time
from pathlib import Path
from typing import Any, List

import requests
from dotenv import load_dotenv


API_BASE_URL = "https://data.skylinkapi.com/v3.1"
AVIATION_WEATHER_API_URL = "https://aviationweather.gov/api/data"
AIRPORTS_CSV_URL = "https://ourairports.com/data/airports.csv"
INDONESIA_BBOX = "-11,95,6,141"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output"
DEFAULT_AIRPORT_LIST = Path(__file__).with_name("indonesia_airports.json")
DEFAULT_WEATHER_STATION_LIST = Path(__file__).with_name("indonesia_weather_stations.json")
MIN_REQUEST_INTERVAL_SECONDS = 1.2
MAX_RETRIES = 3
RETRYABLE_STATUS_CODES = {429, 500, 502, 504}
_last_request_started = None
load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def get_headers(api_key: str) -> dict:
    return {"x-api-key": api_key}


def write_json(output_path: Path, data: Any) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def fetch_weather(api_key: str, icao: str, product: str):
    global _last_request_started

    params = {"parsed": "true"} if product == "metar" else None
    url = f"{API_BASE_URL}/weather/{product}/{icao}"
    retry_delay = 1.0

    for attempt in range(MAX_RETRIES + 1):
        now = time.monotonic()
        if _last_request_started is not None:
            wait = MIN_REQUEST_INTERVAL_SECONDS - (now - _last_request_started)
            if wait > 0:
                time.sleep(wait)
        _last_request_started = time.monotonic()

        response = requests.get(
            url,
            headers=get_headers(api_key),
            params=params,
            timeout=30,
        )
        if response.status_code not in RETRYABLE_STATUS_CODES or attempt == MAX_RETRIES:
            try:
                response.raise_for_status()
            except requests.HTTPError as exc:
                details = response.text.strip() or "(API returned an empty error response)"
                raise requests.HTTPError(
                    f"{exc}\nAPI response: {details}",
                    response=response,
                ) from exc
            return response.json()

        retry_after = response.headers.get("Retry-After")
        try:
            delay = max(float(retry_after), retry_delay) if retry_after else retry_delay
        except ValueError:
            delay = retry_delay
        time.sleep(delay)
        retry_delay *= 2


def get_indonesian_airports() -> List[str]:
    response = requests.get(AIRPORTS_CSV_URL, timeout=60)
    response.raise_for_status()

    airports = set()
    for airport in csv.DictReader(io.StringIO(response.text)):
        icao = next(
            (
                candidate.strip().upper()
                for candidate in (airport.get("gps_code") or "", airport.get("ident") or "")
                if len(candidate.strip()) == 4
                and candidate.strip().upper().startswith("W")
                and candidate.strip().isalpha()
            ),
            None,
        )
        if airport.get("iso_country") == "ID" and icao:
            airports.add(icao)
    return sorted(airports)


def write_indonesian_airport_list(output_path: Path) -> None:
    airports = get_indonesian_airports()
    if not airports:
        raise RuntimeError("No ICAO-coded Indonesian airports were found in the airport dataset.")
    write_json(output_path, airports)
    print(f"Saved {len(airports)} ICAO codes to {output_path}")


def read_airport_list(input_path: Path) -> List[str]:
    try:
        values = json.loads(input_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read ICAO list from {input_path}: {exc}") from exc

    if not isinstance(values, list) or not values:
        raise ValueError(f"{input_path} must contain a non-empty JSON array of ICAO codes.")

    airports = set()
    for value in values:
        if (
            not isinstance(value, str)
            or len(value.strip()) != 4
            or not value.strip().isalpha()
            or not value.strip().upper().startswith("W")
        ):
            raise ValueError(f"Invalid Indonesian ICAO code in {input_path}: {value!r}")
        airports.add(value.strip().upper())
    return sorted(airports)


def get_current_indonesian_weather_stations() -> dict:
    stations = {}
    for product in ("metar", "taf"):
        response = requests.get(
            f"{AVIATION_WEATHER_API_URL}/{product}",
            params={"bbox": INDONESIA_BBOX, "format": "json"},
            headers={"User-Agent": "aviation-weather-api weather-station discovery"},
            timeout=30,
        )
        response.raise_for_status()
        reports = response.json() if response.status_code != 204 else []
        if not isinstance(reports, list):
            raise ValueError(f"Unexpected {product.upper()} station-feed response.")

        stations[product] = sorted(
            {
                station
                for report in reports
                if isinstance(report, dict)
                for station in [str(report.get("icaoId", "")).strip().upper()]
                if len(station) == 4
                and station.isalpha()
                and station.startswith(("WA", "WI", "WR"))
            }
        )
        if not stations[product]:
            raise RuntimeError(f"No current Indonesian {product.upper()} stations found in weather feed.")
    return stations


def read_weather_station_list(input_path: Path) -> dict:
    try:
        stations = json.loads(input_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read weather station list from {input_path}: {exc}") from exc

    if not isinstance(stations, dict):
        raise ValueError(f"{input_path} must contain an object with METAR and TAF arrays.")
    for product in ("metar", "taf"):
        values = stations.get(product)
        if not isinstance(values, list) or not values:
            raise ValueError(f"{input_path} must contain a non-empty '{product}' array.")
        if any(
            not isinstance(value, str)
            or len(value.strip()) != 4
            or not value.strip().isalpha()
            or not value.strip().upper().startswith(("WA", "WI", "WR"))
            for value in values
        ):
            raise ValueError(f"{input_path} contains an invalid Indonesian {product.upper()} station code.")
        stations[product] = sorted({value.strip().upper() for value in values})
    return stations


def fetch_indonesia_weather(api_key: str, output_path: Path, station_list_path: Path) -> None:
    station_lists = get_current_indonesian_weather_stations()
    write_json(station_list_path, station_lists)
    station_lists = read_weather_station_list(station_list_path)
    airports = sorted(set(station_lists["metar"]) | set(station_lists["taf"]))

    results = []
    request_count = len(station_lists["metar"]) + len(station_lists["taf"])
    print(
        f"Fetching current reports for {len(airports)} Indonesian stations "
        f"({len(station_lists['metar'])} METAR, {len(station_lists['taf'])} TAF)."
    )
    print(
        f"Plan: {request_count} SkyLink requests, plus retries; "
        f"at least {MIN_REQUEST_INTERVAL_SECONDS:.1f}s between requests. "
        f"Estimated time: {request_count * MIN_REQUEST_INTERVAL_SECONDS / 60:.1f} minutes."
    )

    for index, icao in enumerate(airports, start=1):
        airport_result = {"icao": icao}
        print(f"[{index}/{len(airports)}] {icao}", flush=True)
        for product in ("metar", "taf"):
            if icao not in station_lists[product]:
                continue
            try:
                airport_result[product] = fetch_weather(api_key, icao, product)
            except requests.HTTPError as exc:
                if exc.response is None or exc.response.status_code != 404:
                    raise
                airport_result[product] = {"error": str(exc)}
                print(f"  {product.upper()} unavailable (404)", flush=True)
        results.append(airport_result)
        write_json(output_path, results)

    print(f"Saved weather data to {output_path}. Station list saved to {station_list_path}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch airport METAR and TAF from SkyLink Direct API")
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--icao", default="WIII", help="Airport ICAO code (default: WIII, Jakarta)")
    target.add_argument(
        "--indonesia",
        action="store_true",
        help="Fetch currently available METAR and TAF for Indonesian weather stations",
    )
    parser.add_argument(
        "--airport-list",
        type=Path,
        default=DEFAULT_AIRPORT_LIST,
        help=f"JSON array of ICAO codes (default: {DEFAULT_AIRPORT_LIST.name})",
    )
    parser.add_argument(
        "--refresh-airport-list",
        action="store_true",
        help="Download the current Indonesian ICAO airport list from OurAirports",
    )
    parser.add_argument(
        "--key",
        default=os.getenv("SKYLINK_API_KEY") or os.getenv("RAPIDAPI_KEY"),
        help="SkyLink API key (defaults to SKYLINK_API_KEY in .env)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output JSON file (default: output/weather_<ICAO>.json or output/weather_indonesia.json)",
    )
    args = parser.parse_args()

    if args.refresh_airport_list:
        write_indonesian_airport_list(args.airport_list)
        if not args.indonesia:
            raise SystemExit(0)

    if not args.key:
        parser.error("Set SKYLINK_API_KEY in the project .env file or provide --key")
    if args.indonesia:
        fetch_indonesia_weather(
            args.key,
            args.output or DEFAULT_OUTPUT_DIR / "weather_indonesia.json",
            DEFAULT_WEATHER_STATION_LIST,
        )
    else:
        icao = args.icao.upper()
        if not icao.isalnum() or not 3 <= len(icao) <= 4:
            parser.error("--icao must be a 3- or 4-character airport code")
        print(f"Weather briefing for {icao}")
        results = {"icao": icao}
        for product in ("metar", "taf"):
            print(f"\n{product.upper()}:")
            data = fetch_weather(args.key, icao, product)
            results[product] = data
            print(json.dumps(data, indent=2, ensure_ascii=False))
        output_path = args.output or DEFAULT_OUTPUT_DIR / f"weather_{icao}.json"
        write_json(output_path, results)
        print(f"\nSaved weather data to {output_path}")
