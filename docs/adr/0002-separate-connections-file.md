# Connection credentials move to a separate --connections file

The `--config` schema file is meant to be shared or committed to version control, but it also held the `connections` mapping and `default` alias, which contain credentials. We split those out into a new required `--connections <path>` file, so the schema config can be freely shared while credentials stay in a separate file that can be kept out of version control and permissioned independently. `--config` no longer accepts an inline `connections` section or `default` key; both now belong exclusively to the `--connections` file.

## Considered Options

- Optional `--connections` flag falling back to a fixed path (e.g. next to `--config`, or a `~/.dbbro/` location) — rejected because an implicit fallback path is itself a place secrets can end up undetected (e.g. a stray `connections.yaml` picked up from the working directory), and a missing/misnamed connections file would fail confusingly late instead of with a clear "flag is required" error.
- Supporting both the old inline shape and the new split shape — rejected for the same reason ADR 0001 rejected dual-shape support: it doubles the resolution/validation logic for a form the project has few configs in the wild for.

## Consequences

Existing single-file configs must be split by hand: move `connections` and `default` out of the `--config` file into a new file passed via `--connections`. `dbbro` now requires both `--config` and `--connections` on every invocation; omitting either is an argument-parsing error. `resolve_database_config` is unchanged — it already only reads `connections`/`default` off whatever dict it's given, so pointing it at the `--connections` file's parsed contents instead of the schema config's required no changes there.
