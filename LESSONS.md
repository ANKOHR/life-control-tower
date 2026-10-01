# Lessons for KOML

- Domain lesson: a due item and a money entry have different semantics. A done
  money entry still contributes to entered totals, while a done commitment
  must leave the actionable agenda. Counts alone do not imply completion value.
- Validated assumption: the planted 200-record oracle and mutation test show
  that integer money totals and agenda membership can be computed exactly
  without estimates or model calls. This is synthetic evidence only.
- Unvalidated assumption: a unified overview earns Henry's daily use. No real
  trial or time-saving baseline has been measured; the two-week hook decides.
- Evidence-based build improvement: inspection found that a valid reference
  date at the calendar limit could overflow when adding seven days. Compare
  the date difference instead. A regression test covers 9999-12-31.
- Operating rule: define the date window, money units and provenance contract
  before building UI; reject invalid entries visibly rather than dropping them.
