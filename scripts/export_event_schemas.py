"""Export the shared event schemas as versioned JSON contracts."""
import json
from pathlib import Path

from cmms_common.events.schemas import SCHEMAS


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'contracts' / 'events'


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for event_type, schema in SCHEMAS.items():
        path = OUTPUT / f'{event_type}.v1.json'
        path.write_text(json.dumps(schema, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
