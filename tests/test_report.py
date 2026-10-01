import json
from life_control_tower.core import compute
from life_control_tower.fixtures import fixture_records, expectations, AS_OF
from life_control_tower.report import render


def test_report_matches_ground_truth_exact():
    result = json.loads(render(compute(fixture_records(), AS_OF), 'json'))
    for key, value in expectations().items():
        if key not in ('synthetic', 'label'):
            assert result[key] == value


def test_report_zero_false_positives():
    result = compute(fixture_records(), AS_OF)
    assert set(result['overdue_ids']) == {f'r{i:03}' for i in range(3,200,10)}
    assert set(result['upcoming_ids']) == set(expectations()['upcoming_ids'])


def test_report_carries_provenance_banner():
    records = fixture_records()[:2]
    records[0]['synthetic'] = False
    for fmt in ('md','json'):
        output = render(compute(records, AS_OF), fmt)
        assert '1 SYNTHETIC' in output and '1 real records' in output
        assert 'not independently verified' in output


def test_hypothetical_figures_labelled():
    for fmt in ('md','json'):
        output = render(compute([], AS_OF), fmt)
        assert 'Unmeasured' in output and 'measured baseline' in output


def test_no_em_dashes_in_outputs():
    records = fixture_records()[:1]
    records[0]['title'] += chr(0x2014)
    for fmt in ('md','json'):
        assert chr(0x2014) not in render(compute(records, AS_OF), fmt)
