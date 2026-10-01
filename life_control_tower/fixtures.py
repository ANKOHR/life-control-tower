"""Synthetic ground truth, constructed without randomness or estimated figures."""
import json
from pathlib import Path
from .core import DOMAINS

AS_OF = '2026-09-30'


def fixture_records():
    records = []
    for i in range(200):
        domain = DOMAINS[i % 6]
        records.append(dict(id=f'r{i:03}', title=f'Synthetic {domain} item {i}',
                            domain=domain, status='done' if i % 4 == 0 else 'open',
                            due='2026-09-29' if i % 10 == 3 else ('2026-09-29', '2026-09-30', '2026-10-07', '2026-10-08')[i % 4],
                            amount_pence=1000 if domain == 'money' else 0,
                            direction=('income' if i % 12 == 1 else 'expense') if domain == 'money' else 'none',
                            synthetic=True))
    return records


def expectations():
    # Independent arithmetic: 200 = 33*6+2; 50 done; 150 open.
    # Money indices 1,7,...,199: 17 income and 17 expense entries of 1000p.
    # 20 indices ending in 3 are overdue; ten displace upcoming residue 1.
    return {'synthetic': True, 'label': 'SYNTHETIC hand-computed expectations',
            'as_of': AS_OF, 'record_count': 200, 'open_count': 150, 'done_count': 50,
            'domain_counts': dict(zip(DOMAINS, (34, 34, 33, 33, 33, 33))),
            'overdue_ids': [f'r{i:03}' for i in range(3, 200, 10)],
            'upcoming_ids': [f'r{i:03}' for i in range(200) if i % 4 in (1, 2) and i % 10 != 3],
            'money': {'income_pence': 17000, 'expense_pence': 17000, 'net_pence': 0},
            'provenance': {'synthetic_records': 200, 'real_records': 0}}


def generate(out):
    directory = Path(out)
    directory.mkdir(parents=True, exist_ok=True)
    if any((directory / name).exists() for name in ('records.jsonl', 'expectations.json', 'README.md')):
        raise FileExistsError('fixture destination already contains fixture files')
    lines = ['# SYNTHETIC fixtures. No real personal data.']
    lines.extend(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in fixture_records())
    (directory / 'records.jsonl').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    (directory / 'expectations.json').write_text(json.dumps(expectations(), indent=2, sort_keys=True) + '\n', encoding='utf-8')
    (directory / 'README.md').write_text('# SYNTHETIC fixture set\n\n200 synthetic records. Reference date: 2026-09-30. No randomness.\n', encoding='utf-8')
