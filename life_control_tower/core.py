"""Pure validation and computations over explicitly supplied records."""
from datetime import date

DOMAINS = ("school", "money", "work", "projects", "health/admin", "commitments")
FIELDS = {"id", "title", "domain", "status", "due", "amount_pence", "direction", "synthetic"}


class SchemaError(ValueError):
    """An input does not match the documented contract."""


def parse_date(value, field):
    if not isinstance(value, str):
        raise SchemaError(f"{field}: expected ISO date YYYY-MM-DD")
    try:
        result = date.fromisoformat(value)
    except ValueError:
        raise SchemaError(f"{field}: expected ISO date YYYY-MM-DD") from None
    if result.isoformat() != value:
        raise SchemaError(f"{field}: expected ISO date YYYY-MM-DD")
    return result


def validate(records):
    if not isinstance(records, list):
        raise SchemaError('records: expected list of objects')
    seen = set()
    for r in records:
        if not isinstance(r, dict):
            raise SchemaError("record: expected object")
        missing, extra = FIELDS - r.keys(), r.keys() - FIELDS
        if missing or extra:
            raise SchemaError(f"fields: missing={sorted(missing)}, unknown={sorted(extra)}")
        for key, limit in (("id", 128), ("title", 10000)):
            if not isinstance(r[key], str) or not r[key].strip() or len(r[key]) > limit:
                raise SchemaError(f"{key}: nonempty string of at most {limit} characters required")
        if r['id'] in seen:
            raise SchemaError(f"id: duplicate {r['id']!r}")
        seen.add(r['id'])
        if r['domain'] not in DOMAINS:
            raise SchemaError("domain: unknown domain")
        if r['status'] not in ("open", "done"):
            raise SchemaError("status: expected open or done")
        if type(r['synthetic']) is not bool:
            raise SchemaError("synthetic: expected boolean")
        if r['due'] is not None:
            parse_date(r['due'], 'due')
        amount = r['amount_pence']
        if type(amount) is not int or not 0 <= amount <= 10**12:
            raise SchemaError("amount_pence: integer between 0 and 1000000000000 required")
        if r['direction'] not in ("income", "expense", "none"):
            raise SchemaError("direction: expected income, expense or none")
        if r['domain'] != 'money' and (amount or r['direction'] != 'none'):
            raise SchemaError("amount_pence/direction: monetary entries require domain money")
        if r['direction'] == 'none' and amount:
            raise SchemaError("direction: nonzero amount requires income or expense")
    return records


def compute(records, as_of):
    reference = parse_date(as_of, 'as_of')
    validate(records)
    ordered = sorted(records, key=lambda r: r['id'])
    overdue, upcoming = [], []
    for r in ordered:
        if r['status'] == 'open' and r['due'] is not None:
            due = parse_date(r['due'], 'due')
            if due < reference:
                overdue.append(r['id'])
            elif (due - reference).days <= 7:
                upcoming.append(r['id'])
    income = sum(r['amount_pence'] for r in ordered if r['direction'] == 'income')
    expense = sum(r['amount_pence'] for r in ordered if r['direction'] == 'expense')
    return {
        'as_of': as_of, 'record_count': len(ordered),
        'open_count': sum(r['status'] == 'open' for r in ordered),
        'done_count': sum(r['status'] == 'done' for r in ordered),
        'domain_counts': {d: sum(r['domain'] == d for r in ordered) for d in DOMAINS},
        'overdue_ids': overdue, 'upcoming_ids': upcoming,
        'money': {'income_pence': income, 'expense_pence': expense, 'net_pence': income - expense},
        'provenance': {'synthetic_records': sum(r['synthetic'] for r in ordered),
                       'real_records': sum(not r['synthetic'] for r in ordered)},
        'savings': 'Unmeasured: time saved and money saved are not computed without a measured baseline.',
        'records': ordered,
    }
