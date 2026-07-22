# dbbro

A terminal UI for browsing database connections, schemas, and table contents.

## Language

**Padding row**:
A blank row appended to the bottom of the table panel, purely to stretch the panel to fill unused vertical screen space when there are fewer real rows than fit on screen. Not selectable via Up/Down navigation.
_Avoid_: Filler row, empty row, ghost row

**Connection**:
One named set of physical database credentials (host, database name, user, password, port) that dbbro can open a session against. Declared as an entry in the config's `connections` mapping, keyed by its **Alias**. Distinct from the **Schema**, which is not part of a Connection — every Connection is used against the same, single Schema.
_Avoid_: Database config, datasource

**Alias**:
The key identifying a Connection within `connections` (e.g. `prod`, `staging`). Must match `^[a-zA-Z0-9_]+$` so it can be uppercased into a per-connection environment variable suffix (e.g. alias `prod` → `DBBRO_DB_HOST_PROD`, `DBBRO_DB_PWD_PROD`).

**Default connection**:
The Connection used when the user doesn't name one explicitly. Set via the config's top-level `default` key (an Alias); the `--connection` CLI flag overrides it for a single run.

**Schema**:
The set of Table and Relation definitions describing what's browsable — independent of any physical database. Exactly one Schema exists per config and is shared by every Connection. Not to be confused with a Connection's `name` field, which is the physical MySQL database/schema name on the server side.
_Avoid_: Using "schema" to mean a Connection's database name
