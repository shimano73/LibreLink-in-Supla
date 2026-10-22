import json
import os
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from pylibrelinkup import PyLibreLinkUp
from pylibrelinkup.api_url import APIUrl

EMAIL = os.environ["LIBRE_EMAIL"]
PASSWORD = os.environ["LIBRE_PASSWORD"]
OWNER_NAME = " ".join(os.environ.get("LIBRE_PATIENT_NAME", "").split()).casefold()
WIFE_NAME = " ".join(os.environ.get("LIBRE_WIFE_PATIENT_NAME", "").split()).casefold()
OWNER_OUTPUT = Path(os.getenv("JSON_OUTPUT_PATH", "/home/wyse/libre/state.json"))
WIFE_OUTPUT = Path(os.getenv("WIFE_JSON_OUTPUT_PATH", "/home/wyse/libre/wife_state.json"))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))

TREND_MAP = {
    1: "Szybko w górę",
    2: "W górę",
    3: "Stabilnie",
    4: "W dół",
    5: "Szybko w dół",
    0: "Nieznany",
}

if not OWNER_NAME:
    raise SystemExit(
        "Brak LIBRE_PATIENT_NAME. Ustaw lokalnie pełną nazwę własnego profilu "
        "zwracaną przez LibreLinkUp, aby po dodaniu żony nie pomylić odczytów."
    )


def normalized_patient_name(patient):
    first = getattr(patient, "first_name", "") or ""
    last = getattr(patient, "last_name", "") or ""
    return " ".join(f"{first} {last}".split()).casefold()


def write_json_atomically(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def read_profile(client, patients, target_name, output_path, label):
    if not target_name:
        return

    matches = [patient for patient in patients if normalized_patient_name(patient) == target_name]
    if not matches:
        print(f"Profil {label} nie jest jeszcze połączony z LibreLinkUp; pomijam go, JSON bez zmian.", flush=True)
        return
    if len(matches) > 1:
        print(f"Nazwa profilu {label} nie jest unikalna; pomijam zapis, JSON bez zmian.", flush=True)
        return

    measurement = client.latest(patient_identifier=matches[0])
    if measurement is None:
        print(f"Brak odczytu dla profilu {label}; JSON bez zmian.", flush=True)
        return

    trend = getattr(measurement, "trend", 0)
    trend_code = getattr(trend, "value", trend)
    data = {
        "timestamp": datetime.now(ZoneInfo("Europe/Warsaw")).isoformat(),
        "glucose": measurement.value,
        "trend_code": trend_code,
        "trend": TREND_MAP.get(trend_code, f"Kod: {trend_code}"),
    }
    write_json_atomically(output_path, data)
    print(f"{data['timestamp']} | {label}: {data['glucose']} | {data['trend']}", flush=True)


def fetch_data():
    client = PyLibreLinkUp(email=EMAIL, password=PASSWORD, api_url=APIUrl.EU)
    client.authenticate()
    patients = client.get_patients()

    read_profile(client, patients, OWNER_NAME, OWNER_OUTPUT, "własny profil")
    if WIFE_NAME:
        read_profile(client, patients, WIFE_NAME, WIFE_OUTPUT, "profil żony")
    else:
        print("Profil żony nie jest jeszcze skonfigurowany; własny odczyt działa normalnie.", flush=True)


def main():
    print(f"Odczyt własnego profilu do: {OWNER_OUTPUT}", flush=True)
    while True:
        try:
            fetch_data()
        except Exception as error:
            print(f"Błąd pobierania danych: {type(error).__name__}: {error}; zachowuję poprzednie pliki JSON.", flush=True)
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
