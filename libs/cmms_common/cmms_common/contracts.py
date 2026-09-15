import json
import os
from pathlib import Path


def _contracts_dir() -> Path:
    repo_root = Path(__file__).resolve().parents[3]
    return Path(
        os.environ.get('CMMS_CONTRACTS_DIR')
        or repo_root / 'contracts' / 'api'
    )


def load_contract(app: str, serializer_name: str) -> dict:
    path = _contracts_dir() / app / f'{serializer_name}.json'
    with path.open(encoding='utf-8') as contract_file:
        return json.load(contract_file)


def assert_matches_contract(data: dict, app: str, serializer_name: str) -> None:
    contract = load_contract(app, serializer_name)
    assert set(contract['fields']) <= set(data.keys())
