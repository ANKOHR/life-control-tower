import json
from life_control_tower.fixtures import generate, fixture_records, expectations, AS_OF
from life_control_tower.core import compute


def test_fixtures_labelled_synthetic(tmp_path):
    generate(tmp_path)
    assert (tmp_path/'records.jsonl').read_text().startswith('# SYNTHETIC')
    assert all(r['synthetic'] is True for r in fixture_records())
    assert json.loads((tmp_path/'expectations.json').read_text())['synthetic'] is True
    assert 'SYNTHETIC' in (tmp_path/'README.md').read_text()


def test_fixture_ground_truth_matches_hand_computed():
    actual = compute(fixture_records(), AS_OF)
    for key, value in expectations().items():
        if key not in ('synthetic', 'label'):
            assert actual[key] == value
    assert len(actual['overdue_ids']) == 20
    assert len(actual['upcoming_ids']) == 90
