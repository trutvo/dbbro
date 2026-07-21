# Epic 3 — Inline Multiple-Entity Relations

PRD for Inline Multiple-Entity Relations. Requirements only — no technical or architectural decisions.

> **Confidence:** ~93% after Cycle 3 — the identifying-value fallback for tables with no `search_columns` is now defined, closing the spec's previously-flagged risk; remaining minor risk is that non-functional concerns are limited to a single requirement (no stated performance expectation for very large in-table lists)

## 1. Summary

When a record has a configured relation to another entity, and that relation resolves to more than one related record, the table view currently requires the user to open a separate selection list to see the related entities. This epic changes that: related entities are listed directly beneath the relation's local column in the table view itself, so the user sees them immediately without extra navigation.

## 2. Goals

- All related entities for a relation are visible directly in the table view, beneath the relation's local column.
- The user never needs to open a separate selection list just to see which entities are related to the current record.
- The relation's configured label is used to identify what kind of relationship is being shown.

## 3. Out of scope

- Changing how relations are configured (columns, search_columns, primary_key, relations, label) — this epic only changes how already-configured relations are displayed.
- Editing or creating relations from the table view.
- Navigating from a listed related entity into that entity's own record (unless already supported elsewhere).

## 4. Personas

- **Operator** — a person browsing database records through the TUI, inspecting a record's relationships to other tables as part of understanding or debugging data.

## 5. Domain concepts

- **Table** — an entity type with configured `columns`, `search_columns`, `primary_key`, and zero or more `relations`.
- **Relation** — a configured link from a local table to a foreign table, defined by `table` (the related table's name), `local_column`, `foreign_column`, and a `label` describing the relationship (e.g. "has Shop").
- **Related entity** — a specific record in the foreign table whose `foreign_column` value matches the current record's `local_column` value.
- **Local column** — the column on the current record that a relation is anchored to (e.g. `id` in the Membership example). Its own value is always shown as the first line under that column, with related-entity lines listed beneath it.
- **Identifying value** — the text shown for a related entity, formed from the foreign table's configured `search_columns` values concatenated together. If the foreign table has no configured `search_columns`, the identifying value is formed from the first defined column instead.

## 6. User journeys

### 6.1 Viewing a record with multiple related entities

An operator opens the table view for a Membership record. Beneath the `id` column (the relation's local column), the local column's own value is shown first, followed by each related Shop listed on its own line, labeled with the relation's label ("has Shop") and an identifying value built from the Shop's configured `search_columns`. They can see all related Shops at a glance without opening any other screen, no matter how many there are — the list is never truncated.

### 6.2 Viewing a record with a single related entity

An operator opens the table view for a Membership record that has exactly one related Shop. That one Shop is listed beneath the local column in the same way multiple entities would be, so the display is consistent regardless of how many related entities exist.

### 6.3 Viewing a record with no related entities

An operator opens the table view for a Membership record that has zero related Shops for a configured relation. No related-entity lines are shown beneath the local column for that relation, and no separate selection list is offered or needed.

### 6.4 Viewing a record with multiple configured relations

An operator opens the table view for a record whose table has two configured relations to different foreign tables. Beneath the local column, the related entities for the first configured relation are listed together, followed by the related entities for the second configured relation, each group still showing its own relation's label.

## 7. Functional requirements

### Display

- F1. The system displays, beneath a relation's local column in the table view, one line per related entity found for that relation.
- F2. Each related-entity line includes the relation's configured label and an identifying value for that related entity, where the identifying value is formed from the foreign table's configured `search_columns` values concatenated together.
- F9. When the foreign table has no configured `search_columns`, the system forms the identifying value from the foreign table's first defined column instead.
- F3. The system does not require the user to open a separate selection list to view a relation's related entities in the table view.
- F4. The system displays related-entity lines for a relation regardless of whether there are zero, one, or multiple related entities, using the same in-table display.
- F5. The system displays all related entities for a relation with no upper limit on how many are listed.
- F6. The system displays the local column's own value as the first line beneath that column, followed by the related-entity lines.
- F7. When a table has more than one configured relation, the system groups each relation's related-entity lines together, in the order the relations are configured, all beneath the same local column.
- F8. The system applies this in-table display uniformly to every configured relation, regardless of how many related entities it typically has.

## 8. Non-functional requirements

- N1. The in-table display of related entities must not require the user to leave the table view to see which entities are related.

## 9. Acceptance criteria

### Display

- AC1. Given a table with a relation to another entity, when a record has more than one related entity, then each related entity is listed on its own line beneath the relation's local column.
- AC2. Given a listed related entity, when the user reads its line, then it shows the relation's configured label and an identifying value for that entity.
- AC3. Given a record with related entities for a configured relation, when the table view is rendered, then the user does not need to open any separate selection list to see them.
- AC4. Given a record with exactly one related entity for a relation, when the table view is rendered, then that one related entity is displayed using the same in-table listing as the multiple-entity case.
- AC5. Given a record with zero related entities for a configured relation, when the table view is rendered, then no related-entity lines are shown for that relation.
- AC6. Given a relation that resolves to a large number of related entities, when the table view is rendered, then all of them are listed with no truncation or cap.
- AC7. Given a related entity, when its identifying value is displayed, then it is formed from the foreign table's configured `search_columns` values.
- AC10. Given a foreign table with no configured `search_columns`, when a related entity's identifying value is displayed, then it is formed from the foreign table's first defined column instead.
- AC8. Given a relation's local column, when the table view is rendered, then the local column's own value appears as the first line, above any related-entity lines.
- AC9. Given a table with two or more configured relations, when the table view is rendered, then each relation's related entities are grouped together and appear in the order the relations are configured.

## 10. Dependencies and assumptions

- Assumes relations are already configured (table, local_column, foreign_column, label) as shown in the briefing's example, and that this configuration format is unchanged by this epic.
- Assumes the system can already resolve which foreign-table records match a given local record's relation (i.e., relation resolution itself is not new — only its display location changes).
- Assumes a related entity's identifying value is never empty or missing: a related entity is only listed when it was matched via a non-null foreign key value, and the identifying value falls back to the foreign table's first defined column when no `search_columns` are configured (F9/AC10).
- No dependency on other epics in the roadmap (EP-1, EP-2) — this epic can be delivered independently.

## 11. Open questions

## 12. Decision log

### Cycle 1 — answered

| #   | Question | Decision |
| --- | -------- | -------- |
| Q1  | Identifying value shown on each related-entity line | The foreign table's `search_columns` values concatenated together |
| Q2  | Display behavior for a large number of related entities | Show all related entities with no limit, letting the table view grow as tall as needed |
| Q3  | Visual distinction for related-entity lines beyond the briefing's example | Match the briefing's example exactly, with no additional styling specified |
| Q4  | Scope of the in-table listing across relation cardinalities | Applies to every configured relation uniformly, regardless of how many related entities typically exist |
| Q5  | Organization of related-entity lines when multiple relations are configured | Each relation's related entities are grouped together, in the order the relations are configured |
| Q6  | Whether the local column's own value still shows | Yes, shown as the first line, with related-entity lines beneath it |
| Q7  | Whether the identifying value can ever be empty/missing | Cannot happen — a related entity is only listed when matched via a non-null foreign key value |

### Cycle 3 — answered

| #   | Question | Decision |
| --- | -------- | -------- |
| Q8  | Identifying value fallback when the foreign table has no configured `search_columns` | Use the first defined column instead |
