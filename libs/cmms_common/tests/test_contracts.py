import json

import pytest

from cmms_common.contracts import assert_matches_contract, load_contract


@pytest.fixture
def contract_dir(tmp_path, monkeypatch):
    output_dir = tmp_path / 'contracts' / 'assets'
    output_dir.mkdir(parents=True)
    (output_dir / 'AssetSerializer.json').write_text(
        json.dumps({'fields': ['id', 'name'], 'read_only_fields': ['id']}),
        encoding='utf-8',
    )
    monkeypatch.setenv('CMMS_CONTRACTS_DIR', str(tmp_path / 'contracts'))
    return tmp_path / 'contracts'


def test_contract_loader_and_assertion(contract_dir):
    assert load_contract('assets', 'AssetSerializer')['fields'] == ['id', 'name']
    assert_matches_contract({'id': 1, 'name': 'Pump'}, 'assets', 'AssetSerializer')
    with pytest.raises(AssertionError):
        assert_matches_contract({'id': 1}, 'assets', 'AssetSerializer')
