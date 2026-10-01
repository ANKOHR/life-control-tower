import copy
import pytest
from life_control_tower.core import compute, SchemaError
from life_control_tower.fixtures import fixture_records, AS_OF


@pytest.mark.parametrize('field,value', [('amount_pence', -1), ('amount_pence', True), ('amount_pence', 10**13), ('due', 'not-date'), ('due', '2026-02-30'), ('title', 'x'*10001), ('synthetic', 'true'), ('domain', 'unknown'), ('status', 'pending'), ('extra', 1)])
def test_rejects_adversarial_values(field, value):
    records = fixture_records()
    records[0][field] = value
    with pytest.raises(SchemaError):
        compute(records, AS_OF)


def test_duplicate_ids_rejected():
    records = fixture_records()
    records[1]['id'] = records[0]['id']
    with pytest.raises(SchemaError, match='duplicate'):
        compute(records, AS_OF)


def test_future_dates_explicitly_supported():
    r = fixture_records()[1]
    r['due'] = '2099-01-01'
    result = compute([r], AS_OF)
    assert result['open_count'] == 1
    assert result['upcoming_ids'] == result['overdue_ids'] == []


def test_handles_unicode_and_long_inputs():
    r = fixture_records()[1]
    r['title'] = 'Henry 学校 café C:\\Users\\henry ' + 'a'*9000
    original = copy.deepcopy(r)
    assert compute([r], AS_OF)['records'] == [original]
    assert r == original


def test_corrupted_fixture_changes_computation():
    records = fixture_records()
    records[1]['amount_pence'] = 1001
    records[0]['status'] = 'open'
    result = compute(records, AS_OF)
    assert result['money']['income_pence'] == 17001
    assert result['money']['net_pence'] == 1
    assert 'r000' in result['overdue_ids']


def test_tiny_hand_written_ground_truth():
    def r(id, domain, status, due, amount=0, direction='none'):
        return dict(id=id, title=id, domain=domain, status=status, due=due, amount_pence=amount, direction=direction, synthetic=True)
    records = [r('a','school','open','2026-09-29'), r('b','work','done','2026-09-29'),
               r('c','money','done',None,123,'income'), r('d','money','open',None,23,'expense'),
               r('e','commitments','open','2026-10-07')]
    result = compute(records, AS_OF)
    assert result['record_count'] == 5
    assert result['overdue_ids'] == ['a']
    assert result['upcoming_ids'] == ['e']
    assert result['money'] == dict(income_pence=123, expense_pence=23, net_pence=100)


def test_extreme_reference_date_no_overflow():
    r = fixture_records()[1]
    r['due'] = '9999-12-31'
    assert compute([r], '9999-12-31')['upcoming_ids'] == [r['id']]


@pytest.mark.parametrize('records', [None, {}, 'text', 12])
def test_rejects_non_list_records(records):
    with pytest.raises(SchemaError, match='records'):
        compute(records, AS_OF)
