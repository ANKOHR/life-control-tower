import json
import subprocess
import sys
import time
from life_control_tower.cli import main


def run_fixture(tmp_path):
    directory, state = tmp_path/'input', tmp_path/'result.json'
    assert main(['fixtures','--out',str(directory)]) == 0
    assert main(['run','--input',str(directory),'--state',str(state)]) == 0
    return directory, state


def test_run_completes_on_fixture(tmp_path):
    start = time.perf_counter()
    _, state = run_fixture(tmp_path)
    assert main(['report','--state',str(state),'--out',str(tmp_path/'report.md')]) == 0
    assert time.perf_counter() - start < 5


def test_empty_input_renders_without_traceback(tmp_path, capsys):
    state = tmp_path/'result.json'
    assert main(['run','--input',str(tmp_path),'--state',str(state)]) == 0
    assert main(['report','--state',str(state),'--format','json']) == 0
    assert '"record_count": 0' in capsys.readouterr().out


def test_malformed_input_named_error(tmp_path, capsys):
    (tmp_path/'records.jsonl').write_text('# SYNTHETIC\n{bad}\n')
    assert main(['run','--input',str(tmp_path)]) == 2
    err = capsys.readouterr().err
    assert 'ParseError' in err and 'records.jsonl' in err and 'line 2' in err


def test_determinism_byte_identical(tmp_path):
    directory, state = run_fixture(tmp_path)
    before = state.read_bytes()
    assert main(['run','--input',str(directory),'--state',str(state)]) == 0
    assert state.read_bytes() == before
    for fmt in ('md','json'):
        a,b = tmp_path/f'a.{fmt}', tmp_path/f'b.{fmt}'
        for p in (a,b):
            assert main(['report','--state',str(state),'--format',fmt,'--out',str(p)]) == 0
        assert a.read_bytes() == b.read_bytes()


def test_cli_smoke_all_subcommands(tmp_path):
    _, state = run_fixture(tmp_path)
    for name in ('report','agenda','money'):
        for fmt in ('md','json'):
            assert main([name,'--state',str(state),'--format',fmt]) == 0
    for name in ('fixtures','run','report','agenda','money'):
        process = subprocess.run([sys.executable,'-m','life_control_tower.cli',name,'--help'], capture_output=True, text=True)
        assert process.returncode == 0 and 'Example:' in process.stdout


def test_missing_input_named_error(tmp_path, capsys):
    assert main(['run','--input',str(tmp_path/'missing')]) == 2
    assert 'MissingInput' in capsys.readouterr().err


def test_report_write_failure_no_partial_files(tmp_path, capsys):
    _, state = run_fixture(tmp_path)
    assert main(['report','--state',str(state),'--out',str(tmp_path)]) == 2
    assert 'ReportWriteError' in capsys.readouterr().err
    assert not list(tmp_path.glob('.lct-*'))


def test_schema_drift_named_error(tmp_path, capsys):
    (tmp_path/'records.jsonl').write_text('{"id":"a"}\n')
    assert main(['run','--input',str(tmp_path)]) == 2
    assert 'SchemaError' in capsys.readouterr().err


def test_unsupported_format_is_named(tmp_path, capsys):
    (tmp_path/'records.csv').write_text('bad,csv')
    assert main(['run','--input',str(tmp_path)]) == 2
    assert 'format' in capsys.readouterr().err


def test_duplicate_json_keys_named_error(tmp_path, capsys):
    (tmp_path/'records.jsonl').write_text('{"id":"a","id":"b"}\n')
    assert main(['run','--input',str(tmp_path)]) == 2
    error = capsys.readouterr().err
    assert 'ParseError' in error and 'line 1' in error and 'duplicate JSON field' in error


def test_invalid_state_collection_named_error(tmp_path, capsys):
    state = tmp_path/'result.json'
    state.write_text('{"records": null, "as_of": "2026-09-30"}')
    assert main(['report','--state',str(state)]) == 2
    assert 'SchemaError: records' in capsys.readouterr().err


def test_unicode_cli_roundtrip(tmp_path):
    from life_control_tower.fixtures import fixture_records
    record = fixture_records()[1]
    record['title'] = '学校 café C:\\Users\\henry ' + 'a'*9000 + chr(0x2014)
    (tmp_path/'records.jsonl').write_text(json.dumps(record, ensure_ascii=False), encoding='utf-8')
    state, report = tmp_path/'state.json', tmp_path/'report.json'
    assert main(['run','--input',str(tmp_path),'--state',str(state)]) == 0
    assert main(['report','--state',str(state),'--format','json','--out',str(report)]) == 0
    output = report.read_text(encoding='utf-8')
    assert json.loads(output)['records'][0] == record
    assert chr(0x2014) not in output


def test_failed_report_preserves_existing_file(tmp_path, monkeypatch, capsys):
    from life_control_tower import cli
    _, state = run_fixture(tmp_path)
    destination = tmp_path/'report.md'
    destination.write_text('original')
    def fail_replace(*args):
        raise OSError('simulated replacement failure')
    monkeypatch.setattr(cli.os, 'replace', fail_replace)
    assert main(['report','--state',str(state),'--out',str(destination)]) == 2
    assert 'ReportWriteError' in capsys.readouterr().err
    assert destination.read_text() == 'original'
    assert not list(tmp_path.glob('.lct-*'))


def test_tiny_input_end_to_end(tmp_path):
    from pathlib import Path
    state = tmp_path/'tiny.json'
    source = Path(__file__).resolve().parents[1]/'examples'/'tiny'
    assert main(['run','--input',str(source),'--state',str(state)]) == 0
    assert main(['report','--state',str(state),'--out',str(tmp_path/'tiny.md')]) == 0
    actual = json.loads(state.read_text(encoding='utf-8'))
    assert actual['record_count'] == 5
    assert actual['money']['net_pence'] == 100


def test_bad_schema_names_file_line_and_field(tmp_path, capsys):
    from life_control_tower.fixtures import fixture_records
    record = fixture_records()[0]
    record['amount_pence'] = -1
    (tmp_path/'records.jsonl').write_text('# SYNTHETIC\n' + json.dumps(record))
    assert main(['run','--input',str(tmp_path)]) == 2
    error = capsys.readouterr().err
    assert all(term in error for term in ('SchemaError', 'records.jsonl', 'line 2', 'amount_pence'))
