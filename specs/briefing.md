# Goal

Project name: dbbro

We want to create a console app to browse trough a relational database.
This will not be a generic database tool. To work with dbbro you have to
define the tables and how they related with each other. Also you have to
define the columns to search a entry.
Dbbr will the create a UI to search and browse trough the entries.

## Configuration

Tables, their columns, searchable columns, and relations between tables are
defined in a config file. Example shape (YAML):

```yaml
tables:
  Company:
    columns: [id, name, customerNumber, creationDate, uuid]
    search_columns: [customerNumber, uuid]
    primary_key: id
  Membership:
    columns: [id, member_id, creationDate ]
    search_columns: []
    primary_key: id
    relations:
      - table: Company
        local_column: member_id
        foreign_column: id
        label: "belongs to company"
```

Each table entry specifies its columns, which of those columns are
searchable, its primary key, and optionally a list of relations to other
tables (local/foreign column pair plus a human-readable label used when
navigating to related entries in the UI).

### DB connection

There is also a config file `database` that has the database connection.

```
database:
  host:
  name:
  user:
  password:
```

If the password is not set, dbbro will look for the env var `DBBRO_DB_PWD`

## UI

### Start

When starting the dbbro, it first reads the configuration and collects all searchable table names and their search columns.
*Search dialog*: Then it will show a modal dialog to select what to search:

```
╔══════════════════════════════════════════════════╗
║                                                  ║
║ Please select the table search colum:            ║
║                                                  ║
║ - Company.customerNumber                         ║
║ - Company.uuid                                   ║
║                                                  ║
║                                                  ║
╚══════════════════════════════════════════════════╝
```

By moving the Up and Down key the user can select one table column pair.
After selecting one combination the user can enter the search string:

```
╔══════════════════════════════════════════════════╗
║                                                  ║
║ Company.customerNumber: ________________________ ║
║                                                  ║
╚══════════════════════════════════════════════════╝
```

The search dialog can be opened at anytime by hitting the `s` key.

*Table view*: If an entry was found, the user will see the result table:

```
┌───────────────┬──────────────────────────────────┐
│Company        │                                  │
├───────────────┼──────────────────────────────────┤
│id             │               Membership[879874] │
│customerNumber │                           999998 │
│name           │                      Foo Company │
│uuid           │ 000110475385e3a9755c548ef0491bd7 │
│creationDate   │              2025-11-05 00:39:34 │
└───────────────┴──────────────────────────────────┘
```

The `id` is special because it is a relation to the table Membership. This value has a special format
`<table name>[FK id]`. The user can select such a relation entry by moving the Up and Down key.
By hitting Return the table Membership will be displayed the same way.

Table Membership
```
┌───────────────┬──────────────────────────────────┐
│Membership     │                                  │
├───────────────┼──────────────────────────────────┤
│id             │                           123456 │
│customerNumber │                           999998 │
│member_id      │                  Company[879874] │
│name           │                      Foo Company │
│uuid           │ 000110475385e3a9755c548ef0491bd7 │
│creationDate   │              2025-11-05 00:39:34 │
└───────────────┴──────────────────────────────────┘

```

The `member_id` is the relation to the table Company. This value has a special format
`<table name>[FK id]`. The user can select such a relation entry by moving the Up and Down key.

*History navigation*: Like a web browser, dbbro has a back and forth navigation by using the Left and Right keys. 
Only the Table views are part of the History.

*Error pop up*: Errors will be displayed as modal dialog which can be closed by hitting Return. 

### Characters

The UI is running within a terminal.

Chars to create panels:
```
┌─┬─┐
├─┼─┤
│ │ │
└─┴─┘

```

Chars to create modal windows
```

╔═╦═╗
╠═╬═╣
║ ║ ║
╚═╩═╝

```

