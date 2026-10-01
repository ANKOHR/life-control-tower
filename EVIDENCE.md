# Local build evidence

Validation date: 2026-10-01. CPU-only Python 3.12 on Windows. No external
network calls, GPU workloads or language-model calls are part of this build.

## Measured acceptance results

- `python -m pytest -q`: 42 passed in 1.61 seconds on the first complete run.
- Installed `lct.exe` invoked in three fresh subprocesses: fixtures, run,
  report --format md. Full pipeline wall time: 0.728320 seconds, measured with
  Python `time.perf_counter`, including subprocess startup and captured output.
- Input size: exactly 200 synthetic records. All expected fields compared
  against `demo/expectations.json` and matched exactly. Markdown carried
  `200 SYNTHETIC` in its provenance banner. No tracebacks.
- Agenda: all 20 planted overdue and 90 planted upcoming IDs found; exact set
  equality establishes zero false positives and zero false negatives.
- Money: 17,000p income, 17,000p expense, 0p net, exact integer reconciliation.
- Same-path repeated runs and both report formats are byte-identical in tests.
- Five-record hand-written example passes end-to-end, with 100p synthetic net,
  overdue ID a and upcoming ID e.

These are measured local validation results on synthetic data. They are not
measurements of time saved, real financial outcomes, daily use or real-world
accuracy. The demo timing is a single local sample, not a performance guarantee.

## Independent hand arithmetic

200 records distribute cyclically across six domains: 33 each plus one extra
school and money item, giving 34, 34, 33, 33, 33, 33. Every fourth index is done:
50 done and 150 open. Money indices 1, 7, ..., 199 total 34 entries, alternating
17 income and 17 expense, each 1,000p. Indices ending in 3 are open and overdue:
3, 13, ..., 193, exactly 20. The normal upcoming residues 1 and 2 modulo 4
contain 100 items; ten ending-in-3 overrides remove ten of these, leaving 90.
Done residue-0 dates are excluded despite being before the reference date.

The oracle is arithmetic in fixtures.expectations, independent of core.compute.
Tests mutate income by 1p and change a done item to open; the computed net and
overdue list change. Expectations are never used by the production workflow.

## Adversarial evidence and improvement

Tests cover negative/boolean/oversized money, impossible dates, future dates,
duplicate IDs, duplicate JSON fields, schema drift, long Unicode titles and
Windows paths, malformed JSONL, empty input, missing paths, invalid saved
collections, and failed output replacement with original files preserved.

An evidence-based build improvement replaces reference-date addition with a
date-difference comparison. The regression test demonstrates correct upcoming
membership at 9999-12-31, where the former addition would overflow. This is a
build reliability improvement, not the deferred real-use improvement hook.

Real trial evidence and final verdict remain pending the two-week window.
