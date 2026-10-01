"""Render computed values and explicit data provenance."""
import json


def banner(result):
    p = result['provenance']
    return (f"Data provenance: {p['synthetic_records']} SYNTHETIC fixture records; "
            f"{p['real_records']} real records declared by the input author (Henry's manually entered data when supplied by him). "
            "Declarations are not independently verified. Figures are computed from supplied inputs only.")


def render(result, fmt):
    if fmt == 'json':
        # JSON escaping preserves the original title while avoiding literal forbidden punctuation.
        return (json.dumps({'banner': banner(result), **result}, ensure_ascii=False, sort_keys=True, indent=2) + '\n').replace(chr(0x2014), '\\u2014')
    if result.get('view') == 'agenda':
        selected = set(result['overdue_ids'] + result['upcoming_ids'])
        return ('# Agenda\n\n' + banner(result) + '\n\nAs of: ' + result['as_of'] +
                '\nOverdue IDs: ' + (', '.join(result['overdue_ids']) or 'none') +
                '\nUpcoming IDs: ' + (', '.join(result['upcoming_ids']) or 'none') + '\n\n' +
                result['savings'] + '\n\n' +
                '\n'.join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in result['records'] if r['id'] in selected) + '\n').replace(chr(0x2014), '-')
    if result.get('view') == 'money':
        return '# Money\n\n' + banner(result) + '\n\n' + '\n'.join(f'{k}: {v}' for k, v in result['money'].items()) + '\n\n' + result['savings'] + '\n'
    lines = ['# Life Control Tower', '', banner(result), '', f"As of: {result['as_of']}",
             f"Records: {result['record_count']}; open: {result['open_count']}; done: {result['done_count']}", '',
             '## Domains', '']
    lines.extend(f"- {d}: {n}" for d, n in result['domain_counts'].items())
    lines.extend(['', '## Agenda', '', 'Overdue IDs: ' + (', '.join(result['overdue_ids']) or 'none'),
                  'Upcoming IDs (today through 7 days inclusive): ' + (', '.join(result['upcoming_ids']) or 'none'),
                  '', '## Money', ''])
    lines.extend(f"- {key}: {value}" for key, value in result['money'].items())
    lines.extend(['', result['savings'], '', '## Input trace', '',
                  'All figures reconcile to the records below. Money totals include all statuses, with no claim of payment or savings.', ''])
    lines.append('Input files: ' + (', '.join(result.get('inputs', [])) or 'none supplied'))
    lines.append('')
    lines.extend('- ' + json.dumps(r, ensure_ascii=False, sort_keys=True) for r in result['records'])
    # Normalize the forbidden punctuation even when supplied inside a user title.
    return ('\n'.join(lines) + '\n').replace(chr(0x2014), '-')
