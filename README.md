# LibreLinkUp → SUPLA (sd4linux)

The Python bridge reads all profiles visible to one LibreLinkUp account and writes them to one JSON file. One `sd4linux` device can expose a separate thermometer channel for each profile by reading its JSON path.

## Files

- `src/libre_to_json.py` — polls every patient profile returned by LibreLinkUp and writes the latest readings to one JSON file.
- `config/supla-libre.example.yaml` — one SUPLA Linux device with two thermometer channels reading `/patients/0/glucose` and `/patients/1/glucose`.
- `systemd/` — service unit templates for the bridge and SUPLA device.
- `assets/` — transparent icon source and 210×156 PNG.

## Configuration

Copy `config/libre.env.example` to `/home/wyse/libre/libre.env`, then fill in the LibreLinkUp credentials. The local copy is ignored by Git. Set `JSON_OUTPUT_PATH` if the JSON file should be stored elsewhere.

Copy `config/supla-libre.example.yaml` to `/home/wyse/libre/supla-libre.yaml` and set the SUPLA server and account email. The example defines two channels for two profiles. The bridge sorts profiles alphabetically by name, so channel 1 reads the first profile and channel 2 the second. Rename the captions in SUPLA to identify each person.

The JSON contains every profile returned by LibreLinkUp, even if there are more than two. To display additional profiles as widgets, add a `ThermometerParsed` channel with the corresponding `/patients/N/glucose` path to the YAML and restart the one SUPLA service. The channel definitions are static in sd4linux YAML.

If one profile has a temporary read error, its last successful value is retained for that run. Writes use an atomic file replacement. If LibreLinkUp returns no profiles or all reads fail, the existing JSON is left untouched.

## Privacy

Never commit LibreLinkUp credentials, actual glucose JSON, patient names, or live service configuration. The `.gitignore` excludes common env and glucose-state files.

## Display note

The SUPLA thermometer channel displays glucose values with a temperature unit. This is a display workaround, not a medical monitoring or dosing interface.