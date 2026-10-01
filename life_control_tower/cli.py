"""Local file CLI. Examples are included in each command's help."""
import argparse
import json
import os
from pathlib import Path
import tempfile
from .core import SchemaError, compute, validate
from .fixtures import AS_OF, generate
from .report import render


class InputError(ValueError):
    pass


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON field {key!r}')
        result[key] = value
    return result


def read_records(directory):
    path = Path(directory)
    if not path.is_dir():
        raise InputError(f'MissingInput: {path}: directory missing; use lct run --input <dir>')
    records = []
    unsupported = [p for p in path.glob('records*') if p.is_file() and p.suffix != '.jsonl']
    if unsupported:
        raise InputError(f'SchemaError: {unsupported[0]}: line 1: format: only records*.jsonl supported; convert to documented JSONL')
    for file in sorted(path.glob('records*.jsonl')):
        for line_no, line in enumerate(file.read_text(encoding='utf-8-sig').splitlines(), 1):
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            try:
                record = json.loads(line, object_pairs_hook=unique_object)
            except json.JSONDecodeError as exc:
                raise InputError(f'ParseError: {file}: line {line_no}, column {exc.colno}: {exc.msg}') from None
            except ValueError as exc:
                raise InputError(f'ParseError: {file}: line {line_no}: {exc}') from None
            try:
                validate(records + [record])
            except SchemaError as exc:
                raise InputError(f'SchemaError: {file}: line {line_no}: {exc}') from None
            records.append(record)
    return records


def atomic_write(path, text):
    target = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n', dir=target.parent,
                                         delete=False, prefix='.lct-') as handle:
            temporary = Path(handle.name)
            handle.write(text)
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(prog='lct', description='Deterministic local life overview. No estimated savings.')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('fixtures', help='Generate 200 labelled synthetic records', epilog='Example: lct fixtures --out demo')
    p.add_argument('--out', required=True)
    p = sub.add_parser('run', help='Validate and compute an overview', epilog='Example: lct run --input demo --as-of 2026-09-30')
    p.add_argument('--input', required=True)
    p.add_argument('--as-of', default=AS_OF, help='Explicit reference date; default 2026-09-30, never the system clock')
    p.add_argument('--state', default='.lct/result.json')
    for name, description in [('report', 'Render saved results with provenance'), ('agenda', 'List overdue and upcoming open commitments'), ('money', 'Show exact entered income and expense totals in pennies')]:
        p = sub.add_parser(name, help=description, epilog=f'Example: lct {name} --format md')
        p.add_argument('--format', choices=['md', 'json'], default='md')
        p.add_argument('--state', default='.lct/result.json')
        p.add_argument('--out', help='Atomically write report instead of standard output')
    args = parser.parse_args(argv)
    try:
        if args.command == 'fixtures':
            generate(args.out)
            print(f'SYNTHETIC: generated 200 records in {args.out}')
        elif args.command == 'run':
            result = compute(read_records(args.input), args.as_of)
            result['inputs'] = [str(p) for p in sorted(Path(args.input).glob('records*.jsonl'))]
            Path(args.state).parent.mkdir(parents=True, exist_ok=True)
            serialized = (json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + '\n').replace(chr(0x2014), '\\u2014')
            atomic_write(args.state, serialized)
            print(f"Computed {result['record_count']} records; synthetic={result['provenance']['synthetic_records']}; real={result['provenance']['real_records']}. Saved {args.state}")
        else:
            state = Path(args.state)
            if not state.is_file():
                raise InputError(f'MissingInput: {state}: run lct run --input <dir> first')
            try:
                saved = json.loads(state.read_text(encoding='utf-8'), object_pairs_hook=unique_object)
            except json.JSONDecodeError as exc:
                raise InputError(f'ParseError: {state}: line {exc.lineno}: {exc.msg}') from None
            except ValueError as exc:
                raise InputError(f'ParseError: {state}: {exc}') from None
            if not isinstance(saved, dict) or 'records' not in saved or 'as_of' not in saved:
                raise SchemaError('state: required fields records and as_of')
            result = compute(saved['records'], saved['as_of'])
            result['inputs'] = saved.get('inputs', [])
            if args.command != 'report':
                result['view'] = args.command
                if args.format == 'json':
                    result['records'] = [r for r in result['records'] if r['domain'] == 'money'] if args.command == 'money' else [r for r in result['records'] if r['id'] in result['overdue_ids'] + result['upcoming_ids']]
            output = render(result, args.format)
            if args.out:
                try:
                    atomic_write(args.out, output)
                except OSError as exc:
                    raise InputError(f'ReportWriteError: {args.out}: {exc}') from None
            else:
                print(output, end='')
    except (InputError, SchemaError, OSError, UnicodeError) as exc:
        label = 'SchemaError: ' if isinstance(exc, SchemaError) else 'FileError: ' if isinstance(exc, (OSError, UnicodeError)) else ''
        print((label + str(exc)).replace(chr(0x2014), '-'), file=__import__('sys').stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
