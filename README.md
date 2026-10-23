# LibreLinkUp → SUPLA (sd4linux)

Most of the LibreLinkUp data bridge and SUPLA Linux configuration used on the Wyse host. The bridge writes the current glucose value to JSON; `sd4linux` reads `/glucose` as a temperature channel for display.

## Files

- `src/libre_to_json.py` — polls one LibreLinkUp account and writes separate JSON files for the configured patient profiles.
- `config/supla-libre.example.yaml` and `config/supla-libre-wife.example.yaml` — separate SUPLA Linux thermometer channels reading the two profile JSON files.
- `systemd/` — service unit templates for the LibreLinkUp bridge and SUPLA device.
- `assets/` — transparent icon source and 210×156 PNG.

## Configuration

Copy `config/libre.env.example` to `/home/wyse/libre/libre.env`, then set these values locally. The local copy is ignored by Git:

```ini
LIBRE_EMAIL=your-librelinkup-account@example.com
LIBRE_PASSWORD=your-secret
LIBRE_PATIENT_NAME=Your Patient Name
LIBRE_WIFE_PATIENT_NAME=Second Patient Name
JSON_OUTPUT_PATH=/home/wyse/libre/state.json
WIFE_JSON_OUTPUT_PATH=/home/wyse/libre/wife_state.json
CHECK_INTERVAL=60
```

Set `LIBRE_WIFE_PATIENT_NAME` to the full name shown in LibreLinkUp after the share appears. The bridge selects patients by exact normalized first and last name. If the profile is not visible yet or its name is ambiguous, it skips that profile and leaves its previous JSON file untouched. Your own profile continues to update. Writes use an atomic file replacement.

To create the second SUPLA widget, copy `config/supla-libre-wife.example.yaml` to `/home/wyse/libre/supla-libre-wife.yaml`, fill in the SUPLA server and account email, and install `systemd/supla-libre-wife.service`. This instance uses its own state directory and reads `/home/wyse/libre/wife_state.json`.

Before running `sd4linux`, set the real SUPLA server and account email in the YAML. Give each instance its own `state_files_path`.

## Privacy

Never commit LibreLinkUp credentials, actual glucose JSON, personal patient names, or live service configuration. Review `git diff` before pushing. The `.gitignore` excludes common env and glucose-state files.

## Display note

The SUPLA thermometer channel displays glucose values with a temperature unit. This is a display workaround, not a medical monitoring or dosing interface.
