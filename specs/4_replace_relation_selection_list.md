# Epic 4 — Replace Relation Selection List

PRD for Replace Relation Selection List. Requirements only — no technical or architectural decisions.

> **Confidence:** ~92% after Cycle 1 — the navigation model, selection-list retirement, zero/one/many cardinality, help bar, and breadcrumb/history behavior are all resolved; remaining minor risk is that F3's local-column no-op (pressing Enter on a multi-match relation's own row does nothing) is a subtle discoverability trade-off, not yet validated with a real user

## 1. Summary

Epic 3 made every related entity for a configured relation visible directly beneath its local column in the table view. However, following Enter still opens the old separate selection list (or jumps straight to the single match) instead of letting the user act on the specific related-entity line they can already see listed inline. This epic replaces that remaining indirection: the user navigates to and opens a specific listed related entity directly from the table view, without an intermediate selection-list screen, for relations that have more than one match.

## 2. Goals

- The user can navigate from a table view directly into a specific related entity's own record, using the same in-table listing introduced in Epic 3.
- The user never needs to open a separate selection list to choose which related entity to open, regardless of how many related entities a relation has.
- Existing navigation behavior for non-relation fields and single-match relations continues to work without disruption.

## 3. Out of scope

- Changing how relations are configured or resolved (unchanged from Epic 3).
- Changing the in-table display introduced in Epic 3 (labels, identifying values, grouping, ordering) — this epic only changes how the user navigates from that display into a related record.
- Editing or creating relations from the table view.

## 4. Personas

- **Operator** — a person browsing database records through the TUI, who now sees related entities listed inline (Epic 3) and wants to open one of them directly.

## 5. Domain concepts

- **Inline related-entity line** — a line beneath a relation's local column, introduced in Epic 3, showing the relation's label and an identifying value for one related entity. It is independently navigable and independently openable, the same as any other row in the table view.
- **Local column row** — the row showing a relation's own local value (e.g. the `id` row), as distinct from the related-entity lines listed beneath it.
- **Selection list** — the pre-Epic-3 separate screen that listed related entities for the user to choose from before opening one. This epic retires the selection list from the relation-following flow: it is no longer shown when the user opens a relation from the table view, since every case it handled (zero, one, or many matches) is now covered by the in-table listing and per-line navigation.

## 6. User journeys

### 6.1 Opening a specific related entity from several matches

An operator opens a Membership record and sees three related Shops listed beneath the `id` row. They move the selection down past the `id` row to the second Shop's line, then press Enter. The Shop's own record opens directly in the table view — no selection list appears at any point.

### 6.2 Opening a relation's single match via its local column

An operator opens a Membership record that has exactly one related Shop. Pressing Enter while the `id` row is highlighted opens that one Shop directly, exactly as it did before this epic — this shortcut is unchanged because a single match never needed a selection list.

### 6.3 Pressing Enter on a local column with multiple matches

An operator opens a Membership record with three related Shops and presses Enter while the `id` row itself (not one of the Shop lines) is highlighted. Nothing happens — no screen opens and no error appears. The operator has to move the selection down onto the specific Shop line they want before pressing Enter again.

### 6.4 A relation with no related entities

An operator opens a Membership record with zero related Shops for a configured relation. As in Epic 3, no related-entity lines appear beneath the local column, so there is nothing to navigate to or open for that relation.

## 7. Functional requirements

### Navigation

- F1. The system allows Up/Down navigation to reach every row in the table view, including each inline related-entity line beneath a relation's local column, not only the local column row itself.
- F2. When the highlighted row is an inline related-entity line, pressing Enter opens that specific related entity's own record in the table view.
- F3. When the highlighted row is a relation's local column and that relation has more than one related entity, pressing Enter has no effect.
- F4. When the highlighted row is a relation's local column and that relation has exactly one related entity, pressing Enter opens that one related entity directly, unchanged from existing single-match behavior.
- F5. The system never opens a separate selection list from the table view when following a relation; the selection list is retired from this flow for relations with zero, one, or many related entities.
- F6. When a relation has zero related entities, no related-entity line exists for that relation, so there is nothing for the user to navigate to or open for it, consistent with Epic 3's display behavior.

## 8. Non-functional requirements

- N1. Opening a related entity, from any related-entity line, must not require the user to leave the table view or pass through any additional screen before the target record's view is shown (extends Epic 3's N1 to cover navigation, not just display).
- N2. The table view's help bar must accurately reflect, for the currently highlighted row, whether pressing Enter will open something: it shows the existing "enter open" indicator whenever Enter would act (a related-entity line, or a local column with exactly one match), and omits it whenever Enter would no-op (a local column with more than one match).

## 9. Acceptance criteria

### Navigation

- AC1. Given the highlighted row is an inline related-entity line, when the user presses Enter, then that specific related entity's own record opens in the table view.
- AC2. Given a relation with more than one related entity, when the user highlights the relation's local column row and presses Enter, then nothing happens — no screen opens.
- AC3. Given a relation with exactly one related entity, when the user presses Enter on the local column row, then that one related entity opens directly.
- AC4. Given the user opens any related entity via the table view, when navigation completes, then no separate selection list screen was shown at any point.
- AC5. Given a relation with zero related entities, when the table view is rendered, then no related-entity line exists to navigate to or open for that relation.
- AC6. Given the highlighted row is a related-entity line or a local column with exactly one match, when the help bar renders, then it shows the "enter open" indicator.
- AC7. Given the highlighted row is a local column with more than one match, when the help bar renders, then the "enter open" indicator does not appear.
- AC8. Given the user opens a related-entity line, when the new table view is pushed, then the breadcrumb and navigation history update identically to the existing push-based navigation flow used elsewhere in the application.

## 10. Dependencies and assumptions

- Depends on Epic 3 (Inline Multiple-Entity Relations) — the in-table listing this epic navigates from must already exist.
- Assumes the underlying record-fetch/navigation mechanics (pushing a new table view, breadcrumb updates) already work as established by prior epics; this epic only changes which UI element triggers that navigation and for which related entity.

## 11. Open questions

## 12. Decision log

### Cycle 1 — answered

| #   | Question | Decision |
| --- | -------- | -------- |
| Q1  | How the user selects a specific inline related-entity line to open | Up/Down navigation reaches every row, including related-entity lines, each independently openable with Enter |
| Q2  | Behavior of Enter on the local column's own row for a relation with more than one match | No effect — the user must navigate to the specific related-entity line they want |
| Q3  | Whether the selection list screen still exists after this epic | Fully retired from the relation-following flow; every case it handled is now covered by in-table listing and per-line navigation |
| Q4  | Behavior when a relation resolves to zero matches | Unchanged from Epic 3 — no related-entity line exists, so there is nothing to select or open |
| Q5  | How the help bar communicates per-line navigation | The existing "enter open" indicator appears whenever Enter would act (a related-entity line or a single-match local column), and is omitted when Enter would no-op |
| Q6  | Whether breadcrumb/history differ from the old selection-list flow | No difference — pushing a new table view works identically to the existing push-based navigation flow |
