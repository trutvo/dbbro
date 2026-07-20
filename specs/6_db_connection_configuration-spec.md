# Epic 6 — Database Connection Configuration — Technical Specification

Tech spec for `6_db_connection_configuration.md`. Implementation-level decisions live here; product requirements stay in the PRD.

> **Confidence:** ~93% after revision 2 (implemented) — D1 is resolved (`PyMySQL`/MySQL) and implemented per §3–§7; all T1–T6 tasks are complete with passing tests. The remaining gap is a discovered-during-implementation risk, not a spec gap: `dbbro/db/queries.py` (EP-2/EP-3) is written against sqlite3's `?` paramstyle and `conn.execute()` shortcut, neither of which a raw PyMySQL connection supports — a follow-up fix to that query layer is needed before the app can actually browse a live MySQL database end-to-end.

## 1. Overview

This spec covers reading a required `database` section from the same YAML configuration file used for the schema (EP-1), resolving its password (file value, else `DBBRO_DB_PWD`, empty-string treated as absent), and establishing one database connection at startup — after schema configuration has already succeeded, and before any UI is shown. Out of scope: the schema/relations themselves (EP-1), and any UI/search/navigation behavior that consumes the resulting connection (EP-2 onward, already coded against a `conn` parameter). See `6_db_connection_configuration.md`.

**Assumption flagged for user sign-off:** the PRD's `database` section (host, port, name, user, password) reads as a networked-database shape, but no epic has yet added a network DB client library — the codebase's only DB dependency is stdlib `sqlite3`. Which driver `connect()` should actually use is left as an open decision (D1) rather than silently picked, per the architecture-advisor's explicit recommendation to surface this rather than paper over it.

## 2. Requirements coverage

| PRD ref | Summary | Covered by |
| ------- | ------- | ---------- |
| FR1  | Read host/name/user from `database` section | §4, §6 T1 |
| FR2  | `database` section may omit password | §6 T1 |
| FR3  | `database` section is required (absent = error) | §6 T1 |
| FR4  | Optional `port` field | §4, §6 T1 |
| FR5  | Malformed value treated same as missing | §6 T2 |
| FR6  | File password used, env var not consulted, if present | §6 T3 |
| FR7  | File omits password → read `DBBRO_DB_PWD` | §6 T3 |
| FR8  | Empty-string env var treated as unset | §6 T3 |
| FR9  | Schema (EP-1) validated before connection attempted | §3, §6 T4 |
| FR10 | Connection attempted once, at startup, before UI | §3, §6 T5 |
| FR11 | Success → proceed with no extra confirmation | §6 T5 |
| FR12 | Missing section/value → error, no start | §6 T1, T6 |
| FR13 | No resolvable password → error, no start | §6 T3, T6 |
| FR14 | Connection failure → error, no start | §6 T5, T6 |
| NFR1 | Env var is a complete substitute for file password | §6 T3 |
| NFR2 | Error reports never include the password value | §4, §6 T6 |
| AC1  | Valid full `database` section → connects using those values | §6 T1, T5 |
| AC2  | Omitted password is not itself invalid shape | §6 T1 |
| AC3  | Missing `database` section entirely → error, no start | §6 T1 |
| AC4  | Optional port used if given, absence not an error | §6 T1 |
| AC5  | Malformed value → same error path as missing | §6 T2 |
| AC6  | File password present → used, env var not consulted | §6 T3 |
| AC7  | File omits password, env var non-empty → env var used | §6 T3 |
| AC8  | File omits password, env var empty string → treated as absent | §6 T3 |
| AC9  | Connection attempted only after schema success; success → no extra confirmation | §6 T4, T5 |
| AC10 | Missing section/value → error naming it, no start | §6 T1, T6 |
| AC11 | No password resolvable → error, no start | §6 T3, T6 |
| AC12 | Connection failure despite valid config → error, no start | §6 T5, T6 |
| AC13 | No error report includes the password value | §6 T6 |

## 3. Architecture

```
dbbro/
  config/                    # unchanged (EP-1)
  db/
    __init__.py
    models.py                # new: DatabaseConfig (frozen dataclass)
    errors.py                # new: DatabaseConfigError, DatabaseConnectionError
    database_config.py       # new: resolve_database_config(raw, env) -> DatabaseConfig
    connection.py            # extended: connect(config: DatabaseConfig) -> Connection
    queries.py                # unchanged (EP-2/EP-3)
  cli.py                     # extended: sequential schema -> db-config -> connect flow
```

Flow: `cli.py::main` first calls `config.loader.read_yaml_file(args.config)` once to get the raw dict, then `config.validate.validate_config(raw)` (EP-1) — if that raises `ConfigValidationError`, the process reports it and exits exactly as today, *before* anything in this epic runs (FR9/AC9). Only if schema validation succeeds does `main` call `db.database_config.resolve_database_config(raw, env=os.environ)`, which reads `raw["database"]`, checks presence and shape of host/database name/user, resolves the password (file value if present; else `DBBRO_DB_PWD`, treating an empty string as unset), and returns a `DatabaseConfig` or raises `DatabaseConfigError` (missing section, missing/malformed required value, or no resolvable password — FR3/FR5/FR12/FR13). If that succeeds, `main` calls `db.connection.connect(db_config)`, which raises `DatabaseConnectionError` if the underlying driver cannot establish the connection (FR14) — that exception's message is built from a fixed template naming host/database name only, never the password (NFR2). On success, the resulting DB-API connection is passed into `run_ui(config, conn)` exactly where `dbbro/ui/app.py::run` already expects a `conn` parameter (previously always `None`), so no UI-layer code changes.

**Key architecture decisions:**

- **Password resolution is a pure function of `(raw dict, env mapping)`**, not a class with hidden global state — `resolve_database_config(raw, env=os.environ)` takes the environment as an explicit parameter (defaulting to `os.environ` in production) so tests can pass a plain dict instead of mutating real process environment variables.
- **Two distinct exception types, mirroring EP-1's `ConfigValidationError` convention but kept separate from it (per the PRD's Q4 decision)**: `DatabaseConfigError` for configuration-shape problems (missing section/value, unresolvable password) and `DatabaseConnectionError` for a live connection attempt that fails — `cli.py::main` catches each in its own sequential step, so a config problem is never confused with a network/credentials problem in the reported message.
- **`DatabaseConfigError` collects every issue found in the `database` section into one report**, mirroring EP-1's "report every violation in one pass" spirit for a single section's worth of problems (e.g. missing host *and* missing user reported together) — a low-risk stylistic choice, not a PRD-mandated behavior, so it does not appear in §9.
- **The DB driver `connect()` uses is `PyMySQL` (D1, resolved)** — `db/connection.py::connect` builds a `pymysql.connect(...)` call from the resolved `DatabaseConfig`, defaulting the port to MySQL's standard `3306` when none is given. Errors are reported via a fixed template naming only host/database name, with the underlying `pymysql.MySQLError` chained (`raise ... from exc`) rather than interpolated into the message, so a driver-side error string can never leak the password (NFR2).

## 4. Data model

`db/models.py`:

```python
@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    name: str
    user: str
    password: str
    port: int | None = None
```

`password` is always a resolved, non-empty string by the time a `DatabaseConfig` exists — `resolve_database_config` never returns one with an empty/missing password; that case always raises `DatabaseConfigError` instead (FR13/AC11). No `__repr__`/`__str__` override is added beyond the dataclass default, and no code path ever formats a `DatabaseConfig` directly into a user-facing error message (NFR2) — error messages are built from the *raw*, pre-resolution values (host/name/user only) or from a fixed template, never by stringifying the resolved config.

`db/errors.py`:

```python
class DatabaseConfigError(Exception):
    """One or more problems with the `database` config section itself
    (missing section, missing/malformed value, unresolvable password)."""
    def __init__(self, issues: list[str]):
        self.issues = issues
        super().__init__("\n".join(issues))

class DatabaseConnectionError(Exception):
    """The database could not be reached or rejected the credentials.
    Message never includes the password (NFR2)."""
```

## 5. API / interfaces

`db/database_config.py`:
```python
def resolve_database_config(raw: dict, env: Mapping[str, str]) -> DatabaseConfig:
    """Reads raw['database']. Raises DatabaseConfigError if:
    - the 'database' key is absent entirely (FR3/AC3),
    - host, name, or user is missing or not a string (FR1/FR5/AC5),
    - no password can be resolved from raw['database']['password'] or a
      non-empty env['DBBRO_DB_PWD'] (FR6-FR8/FR13/AC6-AC8/AC11).
    Otherwise returns a DatabaseConfig with 'port' set from raw['database']
    ['port'] if present, else None (FR4/AC4)."""
```

`db/connection.py`:
```python
def connect(config: DatabaseConfig) -> Connection:
    """Opens a DB-API 2.0 connection using config's resolved values.
    Raises DatabaseConnectionError (message naming host/database name only,
    never the password) if the connection cannot be established."""
```

`cli.py` (extends the existing `main`):
```python
def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    raw = read_yaml_file(args.config)
    try:
        config = validate_config(raw)          # EP-1, unchanged
    except ConfigValidationError as exc:
        ...  # unchanged
    try:
        db_config = resolve_database_config(raw, env=os.environ)
        conn = connect(db_config)
    except (DatabaseConfigError, DatabaseConnectionError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    run_ui(config, conn)                        # conn no longer hardcoded None
    return 0
```

## 6. Implementation plan (TDD)

### T1. `database` section presence, required values, optional port      (closes: FR1, FR2, FR3, FR4, FR12, AC1, AC2, AC3, AC4, AC10)
- Failing tests to write first:
  - `test_resolve_database_config_returns_config_for_full_valid_section`
  - `test_resolve_database_config_accepts_missing_password_in_shape`
  - `test_resolve_database_config_raises_when_database_section_absent`
  - `test_resolve_database_config_raises_when_host_missing`
  - `test_resolve_database_config_raises_when_name_missing`
  - `test_resolve_database_config_raises_when_user_missing`
  - `test_resolve_database_config_uses_given_port_when_present`
  - `test_resolve_database_config_port_is_none_when_absent`
- Production code to make them pass:
  - `db/models.py::DatabaseConfig`
  - `db/errors.py::DatabaseConfigError`
  - `db/database_config.py::resolve_database_config` (presence/shape checks only)

### T2. Malformed value treated as missing        (closes: FR5, AC5)
- Failing tests to write first:
  - `test_resolve_database_config_raises_when_host_is_not_a_string`
  - `test_resolve_database_config_malformed_and_missing_report_via_same_error_type`
- Production code to make them pass:
  - `db/database_config.py::resolve_database_config` (type checks alongside presence checks, same `DatabaseConfigError`)

### T3. Password resolution precedence and empty-env-var handling       (closes: FR6, FR7, FR8, FR13, NFR1, AC6, AC7, AC8, AC11)
- Failing tests to write first:
  - `test_resolve_database_config_uses_file_password_when_present`
  - `test_resolve_database_config_ignores_env_var_when_file_password_present`
  - `test_resolve_database_config_uses_env_var_when_file_password_absent`
  - `test_resolve_database_config_raises_when_no_password_anywhere`
  - `test_resolve_database_config_empty_string_env_var_treated_as_absent`
- Production code to make them pass:
  - `db/database_config.py::resolve_database_config` (password-resolution branch)

### T4. Sequencing: schema validated before connection attempted        (closes: FR9, AC9)
- Failing tests to write first:
  - `test_main_does_not_call_resolve_database_config_when_schema_validation_fails` (patch/spy on `resolve_database_config`, assert not called)
  - `test_main_calls_resolve_database_config_only_after_schema_validation_succeeds`
- Production code to make them pass:
  - `cli.py::main` — sequential try/except ordering (schema first, then database)

### T5. Connection establishment and success passthrough        (closes: FR10, FR11, AC1, AC9)
- Failing tests to write first:
  - `test_connect_returns_a_connection_for_valid_config` (against a real reachable target per D1's resolution — e.g. an in-memory/local instance in CI)
  - `test_main_calls_run_ui_with_the_established_connection_on_success`
  - `test_main_produces_no_extra_output_on_successful_connection` (stdout/stderr assertions)
- Production code to make them pass:
  - `db/connection.py::connect`
  - `cli.py::main` wiring `conn` into `run_ui`

### T6. Failure reporting: config errors, password errors, connection errors, no leak       (closes: FR12, FR13, FR14, NFR2, AC10, AC11, AC12, AC13)
- Failing tests to write first:
  - `test_main_reports_database_config_error_and_exits_nonzero`
  - `test_main_reports_database_connection_error_and_exits_nonzero`
  - `test_database_config_error_message_never_contains_the_password_value`
  - `test_database_connection_error_message_never_contains_the_password_value`
- Production code to make them pass:
  - `cli.py::main` (except-branch reporting)
  - `db/errors.py` message construction (host/name only, never password)

### Refactor step (after T6)
- Once T1–T6 are green, review `cli.py::main`'s two now-sequential try/except blocks (schema, then database) alongside EP-1's existing one for duplicated "print each issue, return 1" logic; extract a small `_report_and_exit(issues: list[str]) -> int` helper if the two blocks have converged to near-identical code.

## 7. Non-functional concerns

- **Env var as complete substitute (NFR1):** `resolve_database_config`'s password branch has no path where a file omission plus a set, non-empty env var still fails — T3's tests pin this as the only two ways to end up with an error (both absent, or explicitly empty).
- **No password leakage (NFR2):** `DatabaseConfigError` and `DatabaseConnectionError` are only ever constructed from fixed strings and the *unresolved* host/name/user values — never from a `DatabaseConfig` instance or the resolved password — enforced by T6's message-content assertions.
- **Fail-fast, sequential startup:** mirrors EP-1's pattern of refusing to proceed to the UI on any failure; this epic adds no new UI code, since `dbbro/ui/app.py::run` already accepts a `conn` parameter (previously always `None`).

## 8. Risks & mitigations

- Risk: `dbbro/db/queries.py` (EP-2/EP-3) was written against `sqlite3`'s `?` paramstyle and calls `conn.execute(...)` directly, a `sqlite3.Connection` convenience method that a raw `pymysql` connection does not have (PyMySQL requires `conn.cursor()` + `%s` placeholders). This is out of scope for this epic per §1, but is a real incompatibility discovered while implementing D1's resolution — EP-2/EP-3's query layer will need a follow-up fix before the app can actually query a live MySQL connection end-to-end. Mitigation: flagged here and in the implementation report; not silently left unmentioned.
- Risk (resolved): D1 originally left the DB driver undecided. Mitigation: resolved to `PyMySQL`/MySQL in Cycle 2, overriding this spec's original sqlite3-only recommendation.
- Risk: `DatabaseConfigError` collecting multiple issues (a stylistic choice made in §3, not PRD-mandated) could be read as implying EP-1-style "report every violation across the whole file in one pass" — it does not; schema and database issues remain sequential per the PRD's Q4 decision. Mitigation: called out explicitly in §3's architecture decisions to prevent conflation.

## 9. Open architecture decisions

_None — D1 was resolved in Cycle 2; see §10 Decision log. §3–§7 already reflect it._

**D1 (resolved):** Which DB driver should `db/connection.py::connect` actually use? → `PyMySQL`, committing dbbro to MySQL as its sole supported networked engine, per Cycle 2 — the user overrode this spec's original "stay on sqlite3 for now" recommendation, confirming MySQL as the actual target engine.

## 10. Decision log

### Cycle 2 — answered
| #  | Question | Decision |
| -- | -------- | -------- |
| D1 | Which DB driver should `connect` use? | `PyMySQL` (MySQL), overriding this spec's original sqlite3-only recommendation |
