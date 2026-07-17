# Epic 1 — Schema Configuration — Technical Specification

Tech spec for `1_schema_configuration.md`. Implementation-level decisions live here; product requirements stay in the PRD.

> **Confidence:** ~94% after revision 2 — D1–D4 resolved and folded into §3's architecture decisions and §10's decision log, closing the last open-decision gap; remaining minor gap is that §6's refactor step (shared table/relation lookup helper) is left to implementer judgement on the "three or more repeats" threshold rather than named upfront.

## 1. Overview

This spec covers loading and validating dbbro's YAML schema configuration in Python: reading the file the operator points at, parsing it, running every structural/cross-referential check in one pass, and exposing the resulting searchable table/column pairs to the rest of the app. Out of scope: anything that *consumes* the exposed pairs (search UI, entry view), and the database connection itself. See `1_schema_configuration.md`.

## 2. Requirements coverage

| PRD ref | Summary | Covered by |
| ------- | ------- | ---------- |
| FR1     | Load config from operator-supplied location | §3, §6 T1 |
| FR2     | Table has name, columns, primary key, search columns | §4, §6 T2 |
| FR3     | Search columns may be empty | §4, §6 T2 |
| FR4     | Search columns must be declared columns | §6 T4 |
| FR5     | Exactly one primary key, must be declared column | §6 T4 |
| FR6     | Relations may target the declaring table (self-relation) | §6 T5 |
| FR7     | Relation has target table, local col, foreign col, label | §4, §6 T3 |
| FR8     | Local/foreign columns must be declared columns | §6 T5 |
| FR9     | Relation target table must be declared | §6 T5 |
| FR10    | Table names unique | §6 T4 |
| FR11    | Column names unique within a table | §6 T4 |
| FR12    | Relation labels unique across configuration | §6 T5 |
| FR13    | Report every violation in one pass | §3, §6 T6 |
| FR14    | Configuration immutable for session | §3, §6 T7 |
| FR15    | Expose searchable table/column pairs | §5, §6 T7 |
| NFR1    | Loading completes before any UI shown | §3, §6 T1 |
| NFR2    | Errors identify table/column/relation clearly | §6 T4, T5, T6 |
| AC1     | Valid config → starts, proceeds to UI | §6 T1 |
| AC2     | No config → error, no UI | §6 T1 |
| AC3     | Bad primary key → error naming table | §6 T4 |
| AC4     | Bad search column → error naming table+column | §6 T4 |
| AC5     | Bad relation target → error naming relation | §6 T5 |
| AC6     | Bad relation local/foreign column → error naming relation | §6 T5 |
| AC7     | Exposed pairs match declared search columns exactly | §6 T7 |
| AC8     | Zero-column table → error naming table | §6 T4 |
| AC9     | Duplicate table name → error naming name | §6 T4 |
| AC10    | Duplicate column name in a table → error naming table+column | §6 T4 |
| AC11    | Duplicate relation label → error naming both relations | §6 T5 |
| AC12    | Self-relation accepted | §6 T5 |
| AC13    | Relation local column = primary key accepted | §6 T5 |
| AC14    | Empty search-column list accepted, contributes nothing | §6 T7 |
| AC15    | Multiple violations → all reported together | §6 T6 |

## 3. Architecture

```
dbbro/
  config/
    __init__.py
    loader.py      # read + parse YAML from a file path
    models.py       # RawConfig / Table / Column / Relation dataclasses (post-validation, immutable)
    validate.py     # pure functions: raw dict -> (models | ConfigValidationError)
    errors.py       # ConfigValidationError, ConfigIssue
    api.py          # public entry point: load_config(path) -> Config
  cli.py            # argparse entry point, calls config.api.load_config before showing any UI
```

Flow: `cli.py` parses `--config <path>`, calls `config.api.load_config(path)`. `loader.py` reads the file and runs `yaml.safe_load`; a missing file or a YAML syntax error is wrapped into a single-issue `ConfigValidationError` immediately (nothing to cross-reference yet). On successful parse, `validate.py` runs every structural and cross-referential rule against the raw dict, accumulating an `errors: list[ConfigIssue]` — no rule short-circuits the rest. If `errors` is non-empty, `ConfigValidationError(errors)` is raised once, after all rules have run. If empty, `validate.py` builds the immutable `models.Config` object (frozen dataclasses) and returns it. `cli.py` catches `ConfigValidationError`, prints every issue, and exits before constructing any UI; on success it hands the `Config` to the rest of the app (`Config.searchable_pairs()` is what the Search epic consumes).

**Key architecture decisions:**

- **Validation collects rather than raises-per-check**, so cross-referential rules (relation target exists, duplicate labels) and per-field rules can all run to completion in one pass, satisfying FR13/AC15.
- **Loading and validation are pure functions returning data** (`Config` or a list of issues), not exceptions-as-control-flow for individual rules — only one exception is raised, at the very end, carrying the full list. This keeps each rule independently unit-testable.
- **Config objects are immutable (frozen dataclasses)** once validated, reflecting FR14 — nothing later in the session can mutate table/column/relation declarations.
- **Config models are plain dataclasses validated by a hand-written accumulating validator, not Pydantic/attrs (D1)** — Pydantic/attrs validators are designed around raising on first failure for a single field/model, which fights the AC15 requirement to collect every cross-referential error in one pass.
- **YAML is parsed with PyYAML's `yaml.safe_load` (D2)** — a one-shot config read at startup never needs comment preservation or round-tripping, so PyYAML is the simplest, most widely-understood, dependency-light choice.
- **The config path is supplied via a required `--config` CLI flag (D3)** — a named flag is self-documenting and keeps the door open to adding other positional arguments (e.g. a query or table name) in later epics without ambiguity.
- **Errors aggregate into a single `ConfigValidationError` (D4)**, raised once after all checks run, rather than per-rule exceptions or bare logging — keeps every validation rule a pure, independently unit-testable function.

(D1–D4 were open decisions as of revision 1; all four are now resolved — see the settled-decision lines below and the Decision log in §10.)

## 4. Data model

Post-validation, immutable (`frozen=True`) dataclasses in `config/models.py`:

- `Column`: `name: str`
- `Relation`: `target_table: str`, `local_column: str`, `foreign_column: str`, `label: str`
- `Table`: `name: str`, `columns: tuple[str, ...]`, `primary_key: str`, `search_columns: tuple[str, ...]`, `relations: tuple[Relation, ...]`
- `Config`: `tables: dict[str, Table]` (keyed by table name), plus `searchable_pairs() -> list[tuple[str, str]]` returning every `(table_name, column_name)` across all tables' `search_columns`.

`errors.py`:
- `ConfigIssue`: `table: str | None`, `column: str | None`, `relation_label: str | None`, `message: str` — enough structured context to satisfy NFR2 without forcing string-parsing by callers.
- `ConfigValidationError(Exception)`: wraps `issues: list[ConfigIssue]`; `__str__` renders one line per issue.

## 5. API / interfaces

`config/api.py`:
```python
def load_config(path: str) -> Config:
    """Read, parse, and validate the YAML config at `path`.

    Raises ConfigValidationError (single exception, .issues holds every
    violation found) if the file is missing, unreadable, malformed YAML,
    or fails any structural/cross-referential rule.
    """
```

`cli.py` argument: `--config PATH` (required, via `argparse`), consumed before any UI code runs.

`Config.searchable_pairs() -> list[tuple[str, str]]` — the interface the Search epic (EP-2) consumes.

## 6. Implementation plan (TDD)

### T1. Load and parse the YAML file            (closes: FR1, NFR1, AC1, AC2)
- Failing tests to write first:
  - `test_load_config_missing_file_raises_single_issue`
  - `test_load_config_malformed_yaml_raises_single_issue`
  - `test_load_config_valid_minimal_file_returns_config`
- Production code to make them pass:
  - `config/loader.py::read_yaml_file(path) -> dict`
  - `config/api.py::load_config(path)` wiring loader → validate

### T2. Table/column/search-column model & basic shape        (closes: FR2, FR3)
- Failing tests to write first:
  - `test_table_with_no_search_columns_is_valid`
  - `test_table_shape_fields_present`
- Production code to make them pass:
  - `config/models.py::Table`, `Column`

### T3. Relation model & shape                                 (closes: FR7)
- Failing tests to write first:
  - `test_relation_has_target_local_foreign_label`
- Production code to make them pass:
  - `config/models.py::Relation`

### T4. Per-table structural validation rules      (closes: FR4, FR5, FR10, FR11, NFR2, AC3, AC4, AC8, AC9, AC10)
- Failing tests to write first:
  - `test_validate_rejects_primary_key_not_in_columns`
  - `test_validate_rejects_search_column_not_in_columns`
  - `test_validate_rejects_empty_column_list`
  - `test_validate_rejects_duplicate_table_names`
  - `test_validate_rejects_duplicate_column_names_in_table`
  - each asserting the resulting `ConfigIssue` names the offending table/column
- Production code to make them pass:
  - `config/validate.py::validate_tables(raw) -> list[ConfigIssue]`

### T5. Relation validation rules       (closes: FR6, FR8, FR9, FR12, NFR2, AC5, AC6, AC11, AC12, AC13)
- Failing tests to write first:
  - `test_validate_rejects_relation_to_undeclared_table`
  - `test_validate_rejects_relation_with_undeclared_local_or_foreign_column`
  - `test_validate_accepts_self_relation`
  - `test_validate_accepts_local_column_equal_to_primary_key`
  - `test_validate_rejects_duplicate_relation_labels_across_tables`
- Production code to make them pass:
  - `config/validate.py::validate_relations(raw) -> list[ConfigIssue]`

### T6. Aggregate all rules into one pass, single exception     (closes: FR13, AC15)
- Failing tests to write first:
  - `test_validate_config_reports_all_violations_from_multiple_rules_in_one_exception`
    (e.g. a bad relation target *and* a duplicate table name together produce two issues in one `ConfigValidationError`)
- Production code to make them pass:
  - `config/validate.py::validate_config(raw) -> Config` — calls `validate_tables` + `validate_relations`, concatenates issues, raises `ConfigValidationError(issues)` if any, else builds and returns `Config`

### T7. Immutability & exposure of searchable pairs      (closes: FR14, FR15, AC7, AC14)
- Failing tests to write first:
  - `test_config_tables_are_immutable` (attempting to mutate raises)
  - `test_searchable_pairs_matches_declared_search_columns_exactly`
  - `test_table_with_empty_search_columns_contributes_nothing`
- Production code to make them pass:
  - `Config.searchable_pairs()` in `config/models.py`

### Refactor step (after T7)
- Once all rules are green, review `validate_tables`/`validate_relations` for duplicated lookup logic (e.g. building a `name -> Table` index) and extract a shared helper if genuinely repeated three or more times; do not pre-extract before that point.

## 7. Non-functional concerns

- **Startup ordering (NFR1):** `cli.py` must call `load_config` before constructing any UI component; enforced by an integration test that patches the UI entry point and asserts it is never called when `load_config` raises.
- **Error clarity (NFR2):** every `ConfigIssue` carries structured `table`/`column`/`relation_label` fields, not just a free-text message, so the CLI can render a consistent `"<table>.<column>: <message>"` or `"relation '<label>': <message>"` line per issue.
- **No security-sensitive surface:** config file path comes from a trusted operator-supplied CLI flag; no untrusted input is parsed as YAML (PyYAML's `safe_load` is used regardless, as defense in depth).

## 8. Risks & mitigations

- Risk: cross-referential rules (label uniqueness, relation targets) require a full pass over all tables before per-table errors are known, which could tempt a two-pass implementation that's harder to keep in sync with "one pass" wording in the PRD. Mitigation: "one pass" means "one validation run producing all issues," not "single loop iteration" — `validate.py` may internally loop over tables multiple times as long as it returns one aggregated result.
- Risk: large configs could make `ConfigValidationError` messages unwieldy. Mitigation: out of scope for this epic's console app scale; revisit only if it becomes a real pain point.

## 10. Decision log

### Cycle 1 — answered

| #  | Question | Decision |
| -- | -------- | -------- |
| D1 | Which validation approach/library for the config models? | Plain dataclasses + a hand-written validator function that accumulates a list of error strings across all checks. |
| D2 | Which YAML parsing library? | PyYAML (`yaml.safe_load`). |
| D3 | How does the operator supply the config file location? | A named CLI flag, `dbbro --config path/to/config.yaml`. |
| D4 | How is error aggregation/reporting structured? | A single custom `ConfigValidationError` carrying a list of structured error objects, raised once after all checks run. |
