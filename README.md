# LibreLink-in-Supla

A gateway that enables reading data from a LibreLink glucose sensor via LibreLinkUp and Supla Device for Linux. The sensor data is presented through a temperature channel, allowing it to be displayed as a widget on a smartphone.



## Files

- `src/libre_to_json.py` — polls one LibreLinkUp account and writes separate JSON files for the configured patient profiles.
- `config/supla-libre.example.yaml` — one SUPLA Linux thermometer channel reading `/glucose` from `/home/wyse/libre/state.json`.
- `systemd/` — service unit templates for the LibreLinkUp bridge and SUPLA device.
- `assets/` — transparent icon source and 210×156 PNG.

## Configuration

Copy `config/libre.env.example` to `/home/wyse/libre/libre.env`, then set these values locally. The local copy is ignored by Git:

```ini
LIBRE_EMAIL=your-librelinkup-account@example.com
LIBRE_PASSWORD=your-secret
LIBRE_PATIENT_NAME=Your Patient Name
# Add after the second patient accepts the share:
LIBRE_WIFE_PATIENT_NAME=Second Patient Name
JSON_OUTPUT_PATH=/home/wyse/libre/state.json
WIFE_JSON_OUTPUT_PATH=/home/wyse/libre/wife_state.json
CHECK_INTERVAL=60
```

The bridge selects patients by exact normalized first and last name. Missing or ambiguous profiles are skipped, and their previous JSON files are left untouched. Writes use an atomic file replacement.

Before running `sd4linux`, set the real SUPLA server and account email in the YAML. Give each instance its own `state_files_path`.

## Privacy

Never commit LibreLinkUp credentials, actual glucose JSON, personal patient names, or live service configuration. Review `git diff` before pushing. The `.gitignore` excludes common env and glucose-state files.

## Display note

The SUPLA thermometer channel displays glucose values with a temperature unit. This is a display workaround, not a medical monitoring or dosing interface.
