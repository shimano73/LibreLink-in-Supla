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
OUTPUT = Path(os.getenv("JSON_OUTPUT_PATH", "/home/wyse/libre/state.json"))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))

TREND_MAP = {
    1: "Szybko w górę",
    2: "W górę",
    3: "Stabilnie",
    4: "W dół",
    5: "Szybko w dół",
    0: "Nieznany",
}


def normalized_patient_name(patient):
    first = getattr(patient, "first_name", "") or ""
    last = getattr(patient, "last_name", "") or ""
    return " ".join(f"{first} {last}".split())


def patient_key(patient, name):
    identifier = (
        getattr(patient, "id", None)
        or getattr(patient, "patient_id", None)
        or getattr(patient, "identifier", None)
    )
    return str(identifier or name.casefold())


def write_json_atomically(data):
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_name(OUTPUT.name + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(OUTPUT)


def read_previous_profiles():
    try:
        previous = json.loads(OUTPUT.read_text(encoding="utf-8"))
        return {item["id"]: item for item in previous.get("patients", []) if "id" in item}
    except (OSError, ValueError, TypeError):
        return {}


def fetch_data():
    client = PyLibreLinkUp(email=EMAIL, password=PASSWORD, api_url=APIUrl.EU)
    client.authenticate()
    patients = client.get_patients()
    if not patients:
        print("LibreLinkUp nie zwrócił profili; poprzedni JSON pozostaje bez zmian.", flush=True)
        return

    previous_list = list(read_previous_profiles().values())
    previous = {item["id"]: item for item in previous_list}
    current = {}
    for patient in sorted(patients, key=lambda item: normalized_patient_name(item).casefold()):
        name = normalized_patient_name(patient) or "Profil LibreLinkUp"
        key = patient_key(patient, name)
        current[key] = (patient, name)

    # Keep existing indexes stable as SUPLA channels read /patients/N/glucose.
    ordered_keys = [item["id"] for item in previous_list]
    ordered_keys.extend(key for key in current if key not in previous)
    # Keep slots for profiles no longer returned, so other channels never shift.

    readings = []
    for key in ordered_keys:
        if key not in current:
            old = previous[key]
            readings.append({**old, "glucose": None})
            print(f"Profil {old.get('name', key)} nie jest teraz udostępniony; kanał pozostaje pusty.", flush=True)
            continue

        patient, name = current[key]
        try:
            measurement = client.latest(patient_identifier=patient)
            if measurement is None:
                raise RuntimeError("brak najnowszego pomiaru")

            trend = getattr(measurement, "trend", 0)
            trend_code = getattr(trend, "value", trend)
            reading = {
                "id": key,
                "name": name,
                "glucose": measurement.value,
                "trend_code": trend_code,
                "trend": TREND_MAP.get(trend_code, f"Kod: {trend_code}"),
                "timestamp": datetime.now(ZoneInfo("Europe/Warsaw")).isoformat(),
            }
            print(f"{reading['timestamp']} | {name}: {reading['glucose']} | {reading['trend']}", flush=True)
        except Exception as error:
            reading = {**previous.get(key, {"id": key, "name": name}), "glucose": None}
            print(f"Brak aktualnego odczytu dla profilu {name}: {type(error).__name__}: {error}", flush=True)
        readings.append(reading)

    if not readings:
        print("Brak odczytów; poprzedni JSON pozostaje bez zmian.", flush=True)
        return

    write_json_atomically({
        "timestamp": datetime.now(ZoneInfo("Europe/Warsaw")).isoformat(),
        "patients": readings,
    })
    print(f"Zapisano {len(readings)} profili do: {OUTPUT}", flush=True)


def main():
    print(f"Odczyt wszystkich profili LibreLinkUp do jednego pliku: {OUTPUT}", flush=True)
    while True:
        try:
            fetch_data()
        except Exception as error:
            print(f"Błąd pobierania danych: {type(error).__name__}: {error}; zachowuję poprzedni JSON.", flush=True)
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()