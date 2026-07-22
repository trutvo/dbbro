# Multiple named connections replace the singular `database:` config key

dbbro needs to browse the same schema against different physical databases (e.g. `prod`, `staging`). We replaced the single `database:` config section with a `connections:` mapping keyed by alias, each entry holding host/name/user/password/port as before, with one `tables:` schema shared across all connections. This is a breaking change — `database:` is no longer read — rather than kept as a legacy alias, since the tool has few config files in the wild and supporting both forms indefinitely would double the resolution/validation logic.

## Considered Options

- Keep `database:` as a permanent legacy alias, or deprecate-then-remove — rejected in favor of a clean breaking change (see above).
- `connections:` as a list of `{alias, host, ...}` objects instead of a mapping keyed by alias — rejected because the mapping form makes the alias the natural, enforced-unique key rather than an optional field.
- One global env var fallback (`DBBRO_DB_HOST`/`DBBRO_DB_PWD`) shared across all connections — rejected because it's ambiguous once more than one connection needs a fallback. Replaced with per-alias env vars: `DBBRO_DB_HOST_<ALIAS>` / `DBBRO_DB_PWD_<ALIAS>` (alias uppercased), which is why alias is constrained to `^[a-zA-Z0-9_]+$`.

## Consequences

Selecting a connection: an optional top-level `default: <alias>` key picks the connection used absent a flag; `--connection <alias>` overrides it; a config with exactly one connection auto-selects it. Existing config files must be migrated to the new `connections:` shape before upgrading.
