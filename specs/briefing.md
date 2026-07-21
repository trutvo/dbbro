# Tasks

## 1 Bug: breadcrumb

The breadcrumb is not visible. Please make it visible on the top of the screen. 


## 2 Feature: Help

Please display a one line help for all navigation keys at the bottom of the screen.


## 3 Feature: multiple entity list

Relations to multiple entities are displayed within the table view.
Instead of using the selection list, these relations are simply listed 
below the local column id.

*Example table Membership:*


```
  Membership:
    columns: [id, creationDate]
    search_columns: []
    primary_key: id
    relations:
      - table: Shop
        local_column: id
        foreign_column: primeMembership_id
        label: "has Shop"
  Shop:
    columns: [id, tsId, url, name, shopkeeper_id, primeMembership_id, creationDate]

```


```
┌───────────────┬──────────────────────────────────┐
│Membership     │                                  │
├───────────────┼──────────────────────────────────┤
│id             │                           123456 │
│               │                     Shop[543334] │
│               │                     Shop[543334] │
│               │                     Shop[543334] │
│creationDate   │              2025-11-05 00:39:34 │
└───────────────┴──────────────────────────────────┘

```
