# Life Control Tower

A deterministic Python CLI for Henry's school, money, work, projects,
health/admin and commitments. It validates local records, counts each domain,
lists overdue and upcoming open items, and reconciles entered money in integer
GBP pennies. It makes no predictions or network calls. Python 3.10+ is required.

## Quickstart

Install with the existing local setuptools installation, without network access:

```powershell
python -m pip install --no-index --no-deps --no-build-isolation -e .
lct fixtures --out demo
lct run --input demo
lct report --format md
python -m pytest -q
```

If Python's Scripts directory is not on PATH, use
`python -m life_control_tower.cli` in place of `lct`, or invoke the installed
`lct.exe` by its full path. Fixture generation refuses to overwrite existing
fixture files. Use a new directory for a second demo.

The demo has 200 labelled synthetic records and an independent expectations
file. No random number generator or seed is needed. The fixed default reference
date is 2026-09-30. For real use explicitly pass `--as-of YYYY-MM-DD`; the tool
never uses the system clock. Results are saved to `.lct/result.json` by default.
Run before reporting changes to inputs. Report recomputes from the saved records
to detect schema errors and avoid trusting stale or manually altered totals.

## Input format

Only UTF-8 `records*.jsonl` files directly inside the input directory are read,
in sorted filename order. Blank lines and lines beginning with `#` are allowed.
Other `records*` file formats are rejected with the file and line; unrelated
files such as expectations are ignored. An existing empty directory is valid.
Each data line is one object with exactly these fields:

| Field | Contract |
| --- | --- |
| id | Unique across input files, nonblank string, at most 128 characters |
| title | Nonblank string, at most 10,000 characters |
| domain | school, money, work, projects, health/admin, commitments |
| status | open or done |
| due | Canonical YYYY-MM-DD or null |
| amount_pence | Integer 0 through 1,000,000,000,000; booleans rejected |
| direction | income, expense or none |
| synthetic | Boolean; true for fixtures, false for Henry's entered real data |

Money amounts belong only to the money domain. Other domains require zero and
direction none. Nonzero amounts require income or expense. No currency
conversion is attempted: enter only GBP pennies. Money totals include every
entered income/expense regardless of status; they do not assert payment,
account balance, profit or savings. Refunds can be positive income entries;
negative amounts are rejected. Future due dates are allowed, including dates
outside the agenda window. Unknown fields, duplicate IDs and duplicate JSON
keys are rejected. Errors never silently discard a record.

Overdue means open with due strictly before the reference date. Upcoming means
open with due from the reference date through seven days later, inclusive.
Done and undated entries never enter either list. Results are sorted by ID.
Counts cover all six domains, including zeros.

A five-record hand-written example lives in `examples/tiny/records.jsonl`.
It is synthetic, not Henry's real data. To use real data, enter your own records
in a private directory with `synthetic: false`, using JSON boolean syntax.
Keep real inputs and trial results out of git. The `.gitignore` reserves
`private/`, `.lct/` and `demo/` for this purpose.

## Subcommands and examples

Every command supports `--help` with an example.

```text
lct fixtures --out demo
lct run --input examples/tiny --as-of 2026-09-30 --state .lct/tiny.json
lct report --state .lct/tiny.json --format json --out .lct/tiny-report.json
lct agenda --state .lct/tiny.json --format md
lct money --state .lct/tiny.json --format md
```

`agenda` exposes overdue and upcoming IDs and their source records. `money`
exposes reconciled entered totals; its JSON view also includes money records.
JSON domain views retain overall counts as context and identify their `view`.
Reports include a provenance banner and the full report contains every source
record for tracing totals. Saved `inputs` identifies the input filenames.

## Architecture

```text
fixtures.py -> labelled JSONL + independent expectations.json
local records*.jsonl -> cli.read_records -> core.validate -> core.compute
core.compute -> atomic local state -> report.render -> stdout / atomic file
tests -> core boundaries + fixture oracle + reports + CLI + adversarial cases
```

Core functions do no I/O. CLI owns parsing and filesystem work. Rendering does
not invent facts. The same records, reference date and input paths produce
byte-identical saved state and reports. Unicode and Windows path strings are
preserved. Markdown substitutes a hyphen for the forbidden punctuation code
point U+2014; JSON escapes that code point to preserve the original data.

## Honesty boundary and fixture policy

All figures are computed from explicit inputs. Synthetic money figures are
synthetic entered amounts, never measured real finances. There are no invented
estimates, time saved claims or money saved claims. Savings remain explicitly
Unmeasured because there is no measured baseline. Provenance is the input
author's declaration, not independent authentication. Mixed input reports
show separate real and synthetic record counts. No real trial data ships.

Fixture JSONL has a SYNTHETIC header comment and `synthetic: true` on every
record. Expectations JSON carries a SYNTHETIC label and `synthetic: true`;
standard JSON does not allow header comments. Fixture Markdown is headed
SYNTHETIC. The five-record example follows the same policy.

## Acceptance evidence and failure modes

The hypothesis is that explicit inputs, deterministic computation and tests
against planted ground truth make this overview trustworthy. This proves
specified arithmetic and agenda rules, not usefulness in Henry's daily life.
See `EVIDENCE.md` for measured local validation and the fixture's independent
hand arithmetic. Tests deliberately change records and confirm figures change.

| Failure | Behavior |
| --- | --- |
| Missing input or state | MissingInput, usage hint, exit 2 |
| Malformed JSONL | ParseError, file and line, exit 2 |
| Unsupported records format | SchemaError, file, line and conversion hint |
| Schema drift or adversarial value | SchemaError identifying offending field |
| Unreadable file or encoding | Named FileError, exit 2 |
| Bad report destination | ReportWriteError, exit 2, no partial file |

Report and state writes use a temporary file and atomic replacement; existing
reports survive failed writes. Fixture generation is not a transactional batch:
an OS write failure can leave labelled fixture files; use a fresh directory to
retry. Inputs are local, untrusted declarations. There are no reminders,
calendar integrations, automatic discovery or hidden background processes.

## Two-week improvement hook and verdict

The real-use evidence window has not started. `VERDICT.md` records pending
status, not an invented final verdict. At the start of a private trial, record
the start date and intended daily use. For 14 days log actual runs and manually
check at least 20 entered records across domains against their computed domain,
status, agenda inclusion and money contribution. Primary metric: erroneous
record classifications/contributions divided by checked records. Keep a dated
private log of numerator, denominator, examples and actual run count.

After two weeks, if error rate exceeds 10 percent, fix the most frequent cause
and retest, or kill with the reason recorded. If unused, kill. Time saved can
only be reported after timing the same manually performed task as a baseline
and timing CLI use on the same data. No time saved is currently measured.

Record exactly one evidence-based improvement and a reasoned verdict:
expand for daily use or revenue; integrate for substantial sibling overlap;
commercialise for a buyer willing to pay as-is; maintain as portfolio evidence
otherwise; kill for non-use or unmet acceptance criteria. Do not skip the
evidence window by claiming a verdict now. `LESSONS.md` captures current lessons.

Publishing is a separate verification step. This build performs no network
calls and does not publish to GitHub.
