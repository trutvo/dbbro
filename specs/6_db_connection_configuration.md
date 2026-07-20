# Epic 6 — Database Connection Configuration

PRD for Database Connection Configuration. Requirements only — no technical or architectural decisions.

> **Confidence:** ~95% after Cycle 3 — re-read fresh with no changes since Cycle 2: all eight Cycle 1 ambiguities remain resolved and reconciled into §5–§10, §13 is empty, and no open questions remain. The only residual softness is unchanged from Cycle 2 — "malformed value" (FR5/AC5) is defined only by example (a non-string host) rather than an exhaustive list, which is appropriately left to the technical spec rather than the PRD.

## 1. Summary

Before dbbro can browse any records, an operator must tell it how to reach
the actual database — not just which tables/columns/relations exist
(covered by EP-1), but the connection details themselves: host, database
name, user, and password. The password may be omitted from the
configuration file and supplied instead via an environment variable, so it
does not need to live in a file on disk. dbbro establishes this connection
once at startup, using the same fail-fast, clearly-reported-error pattern
as schema configuration.

## 2. Goals

- Let an operator declare the database connection (host, database name,
  user, password) in the same configuration file used for the schema.
- Let an operator keep the password out of the configuration file by
  supplying it via an environment variable instead.
- Let dbbro establish the connection once at startup and refuse to proceed
  to the UI if the connection cannot be made.
- Give the operator a clear, specific error when connection details are
  missing or the connection itself cannot be established.

## 3. Out of scope

- Which database engine(s) dbbro supports, or how a connection is
  technically established (covered by the technical spec).
- Declaring or validating the browsable schema itself (tables, columns,
  relations, search columns) — covered by EP-1.
- Any UI, search, or navigation behaviour that uses this connection once
  established (covered by other epics).
- Encrypting, vaulting, or otherwise securing the password beyond letting
  it be supplied via an environment variable instead of the file.
- Reconnecting, retrying, or recovering from a connection that drops after
  a successful startup.
- How long dbbro waits before treating a connection attempt as failed
  (timeout duration/behavior) — left entirely to the technical spec; the
  briefing states no timing requirement.

## 4. Personas

- **Operator** — the same persona as EP-1: sets up dbbro for a particular
  database before anyone browses it, and now must also supply the
  connection details for that database.

## 5. Domain concepts

- **Database connection configuration** — a required `database` section in
  the same configuration file used for the schema (EP-1), declaring host,
  database name, user, and optionally a port and a password. If the section
  is absent entirely, that is itself a configuration error.
- **Password resolution** — the process of determining the password to
  use: the value from the configuration file's `database` section if
  present, otherwise the value of the `DBBRO_DB_PWD` environment variable.
  The file's value always takes precedence — the environment variable is
  consulted only when the file omits the password. An environment variable
  set to an empty string is treated the same as it being unset (no password
  available), not as a valid empty password.
- **Connection establishment** — the act of connecting to the database
  using the resolved host, port, database name, user, and password,
  performed once at startup, after schema configuration (EP-1) has already
  loaded successfully, and before any UI is shown.

## 6. User journeys

### 6.1 Operator configures the connection with the password in the file
The operator adds a `database` section to the configuration file including
host, database name, user, and password. dbbro reads this section at
startup, resolves the password directly from the file, and connects.

### 6.2 Operator configures the connection without a password in the file
The operator adds a `database` section with host, database name, and user,
but no password, and sets the `DBBRO_DB_PWD` environment variable before
running dbbro. dbbro resolves the password from that environment variable
and connects.

### 6.3 Operator's configuration is missing a required value
The operator's `database` section is missing the host, database name, or
user. dbbro reports an error identifying which value is missing, instead
of starting.

### 6.4 No password is available from either source
The operator's `database` section omits the password, and the
`DBBRO_DB_PWD` environment variable is not set. dbbro reports an error
identifying that no password could be resolved, instead of starting.

### 6.5 Connection cannot be established
The operator's `database` section has all required values, and a password
was resolved, but the database itself cannot be reached or rejects the
credentials. dbbro reports an error describing the connection failure,
instead of starting.

### 6.6 Configuration file has no `database` section at all
The operator's configuration file declares the schema (EP-1) but omits the
`database` section entirely. dbbro reports an error identifying that the
section is missing, instead of starting — the same as if the section were
present but missing a required value.

## 7. Functional requirements

### Declaring the connection
1. The system must read database connection details — host, database
   name, and user — from a `database` section of the same configuration
   file used for the schema (EP-1).
2. The system must allow the `database` section to omit the password.
3. The system must require the `database` section to be present; a
   configuration file that omits it entirely is a configuration error.
4. The system must allow the `database` section to optionally specify a
   port, in addition to host, database name, and user.
5. The system must treat a malformed value in the `database` section
   (e.g. a value of the wrong shape, such as host given as a non-string)
   the same as a missing required value — it is not a distinct error case.

### Resolving the password
6. If the `database` section includes a password, the system must use
   that value and must not consult the `DBBRO_DB_PWD` environment
   variable.
7. If the `database` section omits the password, the system must read the
   password from the `DBBRO_DB_PWD` environment variable instead.
8. If the `DBBRO_DB_PWD` environment variable is set to an empty string,
   the system must treat that the same as the variable being unset (no
   password available), not as a valid empty password.

### Establishing the connection
9. The system must validate the schema configuration (EP-1) before
   attempting to establish the database connection; the connection is
   only attempted once schema configuration has succeeded.
10. The system must attempt to establish the database connection once, at
    startup, before any UI is shown.
11. If the connection is established successfully, the system must
    proceed to the rest of startup (UI) as normal, with no additional
    confirmation beyond that — no explicit success message or connection
    details need to be surfaced.

### Handling failures
12. If the `database` section is missing entirely, or is missing a
    required value (host, database name, or user), the system must
    report an error identifying the missing section or value and must not
    start.
13. If no password can be resolved from either the configuration file or
    the `DBBRO_DB_PWD` environment variable, the system must report an
    error identifying that no password is available and must not start.
14. If the connection cannot be established despite having all required
    values and a resolved password (e.g. the database is unreachable or
    rejects the credentials), the system must report an error describing
    the connection failure and must not start.

## 8. Non-functional requirements

1. The password must never be required to appear in the configuration
   file — supplying it via the `DBBRO_DB_PWD` environment variable must
   always be a complete substitute.
2. An error report for a missing value or failed connection must not
   include the resolved password itself.

## 9. Acceptance criteria

### Declaring the connection
- AC1. Given a configuration file with a `database` section specifying
  host, database name, user, and password, dbbro connects using those
  values on startup.
- AC2. Given a `database` section omitting the password, dbbro does not
  treat the omission itself as invalid configuration shape.
- AC3. Given a configuration file whose schema (EP-1) section is otherwise
  valid but which omits the `database` section entirely, dbbro reports an
  error identifying that the section is missing and does not start.
- AC4. Given a `database` section that includes an optional port value,
  dbbro connects using that port; given one that omits it, omitting the
  port is not itself a configuration error.
- AC5. Given a `database` section with a malformed value (e.g. host given
  as a non-string), dbbro reports an error the same way it would for a
  missing required value, not as a separate error case.

### Resolving the password
- AC6. Given a `database` section that includes a password, dbbro uses
  that value and does not consult the `DBBRO_DB_PWD` environment variable.
- AC7. Given a `database` section that omits the password, and
  `DBBRO_DB_PWD` is set to a non-empty value, dbbro uses the environment
  variable's value.
- AC8. Given a `database` section that omits the password, and
  `DBBRO_DB_PWD` is set to an empty string, dbbro treats this the same as
  no password being available (see AC10), not as a valid empty password.

### Establishing the connection
- AC9. Given a valid schema configuration (EP-1) and a valid, connectable
  `database` section, dbbro attempts the database connection only after
  schema configuration has already succeeded, and proceeds to the UI with
  no separate success message or displayed connection details once
  connected.

### Handling failures
- AC10. Given a `database` section missing entirely, or missing the host,
  database name, or user, dbbro reports an error identifying the missing
  section or value and does not start.
- AC11. Given a `database` section omitting the password, and
  `DBBRO_DB_PWD` is not set (or set to an empty string), dbbro reports an
  error identifying that no password is available and does not start.
- AC12. Given all required values and a resolved password, but a database
  that cannot be reached or rejects the credentials, dbbro reports an
  error describing the connection failure and does not start.
- AC13. No error report produced by this epic includes the resolved
  password's value.

## 10. Dependencies and assumptions

- Depends on EP-1 (Schema Configuration) for the configuration file this
  epic's `database` section is added to; this epic does not introduce a
  second configuration file or mechanism.
- Assumes the connection is established once, eagerly, at startup — not
  lazily on first query — mirroring EP-1's fail-fast pattern, and only
  after schema configuration (EP-1) has already succeeded (FR9).
- Assumes every epic that queries the database (EP-2 Record Search, EP-3
  Entry Table View) depends on this epic's successful connection
  establishment, per `specs/roadmap.md`.

## 11. Open questions

_None outstanding — all Cycle 1 questions were resolved; see decision log._

## 12. Decision log

### Cycle 1 — answered
| #  | Question | Decision |
| -- | -------- | -------- |
| Q1 | Is the `database` section required, or can dbbro run without one? | Required: dbbro reports an error and refuses to start if the section is absent entirely |
| Q2 | Should the connection port be configurable? | Yes — an optional `port` field, defaulting to whatever is standard for the chosen database technology |
| Q3 | If both the file and `DBBRO_DB_PWD` supply a password, which wins? | The configuration file's password always wins; the environment variable is consulted only when the file omits it |
| Q4 | Should connection errors be combined with schema errors, or checked separately? | Separate, sequential checks: schema configuration is validated first; the connection is only attempted after schema configuration succeeds |
| Q5 | Should a malformed `database` value be a distinct error case from "missing"? | No — malformed values are reported the same way as missing ones |
| Q6 | Does an operator need explicit confirmation beyond proceeding to the UI? | No — proceeding to the UI is itself sufficient confirmation |
| Q7 | Should there be a connection-attempt timeout limit? | Not specified at the product level — left entirely to the technical spec |
| Q8 | Is an empty-string `DBBRO_DB_PWD` a resolved password or "no password available"? | Treated as "no password available", the same as the variable being unset |
