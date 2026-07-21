# Roadmap: TUI Navigation and Relation Display Fixes

Restate the goal: make the breadcrumb visible, surface navigation help to the user, and render multi-entity relations inline within the table view. The target end-state is a terminal UI where users can always see their location, know which keys to press, and see all related entities directly in the record table without extra navigation.

---

## Dependency graph

| Epic | Depends on | Can start in parallel with |
| ---- | ---------- | --------------------------- |
| EP-1 | —          | EP-2, EP-3                  |
| EP-2 | —          | EP-1, EP-3                  |
| EP-3 | —          | EP-1, EP-2                  |

---

## EP-1 — Visible Breadcrumb

When viewing any screen in the application, the user can always see a breadcrumb at the top of the screen showing their current location within the navigation hierarchy. The breadcrumb is not hidden, clipped, or rendered invisibly under any terminal size or screen state.

**Acceptance criteria**

- The breadcrumb is displayed at the top of the screen at all times while navigating.
- The breadcrumb text is visually legible (not blank, not obscured by other UI elements).
- The breadcrumb reflects the user's current position and updates as the user navigates.

---

## EP-2 — Navigation Key Help

When viewing any screen in the application, the user can see a one-line summary of the available navigation keys at the bottom of the screen, so they always know how to move around without consulting external documentation.

**Acceptance criteria**

- A single line of help text listing the navigation keys is shown at the bottom of the screen.
- The help line reflects the keys applicable to the current screen.
- The help line is present on every screen that supports navigation.

---

## EP-3 — Inline Multiple-Entity Relations

When a record has a relation that points to multiple related entities, the user sees all of those related entities listed directly beneath the relation's local column in the table view, instead of having to open a separate selection list to see them.

**Acceptance criteria**

- Given a table with a relation to another entity, when a record has more than one related entity, each related entity is listed beneath the local column identified in the relation.
- Each listed related entity is shown using its configured label alongside an identifying value for that entity.
- The user does not need to open any separate selection list to see which entities are related to the current record.
- Records with only one or zero related entities are displayed without requiring a separate list either.
