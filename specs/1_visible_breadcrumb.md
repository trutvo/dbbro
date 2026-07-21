# Epic 1 — Visible Breadcrumb

PRD for Visible Breadcrumb. Requirements only — no technical or architectural decisions.

> **Confidence:** ~91% after Cycle 2 — all prior display-behavior gaps resolved (root segment, overflow truncation, scope of path shown, record identification, separation, transient-state visibility); remaining minor risk is a mild internal tension between F2 (only current table/record shown, no multi-hop path) and F5 (truncate a long path's middle segments), which leaves F5 mostly vestigial in practice but not contradictory

## 1. Summary

The breadcrumb showing the user's current location within the navigation hierarchy is not currently visible. This epic fixes that: the breadcrumb is displayed at the top of the screen at all times, so users always know where they are as they navigate through tables, records, and relations.

## 2. Goals

- The breadcrumb is visible at the top of the screen on every screen where navigation location matters.
- The breadcrumb accurately reflects the user's current position in the navigation hierarchy at all times.
- Users never lose track of where they are while navigating between tables, records, and related entities.

## 3. Out of scope

- Changing what the breadcrumb's hierarchy model is or how navigation itself works (this epic is about visibility of the existing breadcrumb, not redesigning its content).
- Adding new navigation capabilities (e.g. clicking a breadcrumb segment to jump back).
- Any other bottom-of-screen or top-of-screen UI elements not related to the breadcrumb.

## 4. Personas

- **Operator** — a person browsing database records through the TUI, moving between tables, records, and related entities, who needs to know their current location without losing context.

## 5. Domain concepts

- **Screen** — a distinct view within the application (e.g. table view, record detail, entity list).
- **Breadcrumb** — a piece of UI displayed at the top of the screen that shows the user's current position within the navigation hierarchy (e.g. which table, which record, which relation they have drilled into).
- **Navigation hierarchy** — the sequence of screens/entities the user has navigated through to reach their current screen (e.g. Table → Record → Related Table).
- **Root segment** — the first segment of the breadcrumb, shown even when the user is at the top level of the hierarchy (e.g. a "Tables" segment before any table or record is selected).
- **Record segment** — a breadcrumb segment identifying a specific record, shown using that record's primary key value.

## 6. User journeys

### 6.1 Drilling into a related record

An operator starts at a table view, opens a record, then drills into one of its related entities. At each step, they glance at the top of the screen and see a breadcrumb, separated from the screen body by a blank line, reflecting only their current table and record context — for example "Shop > 543334" after drilling into a related Shop, without listing the intermediate relation hop. Record segments are identified by the record's primary key value.

### 6.2 Returning to a previous screen

An operator has drilled several levels deep and wants to confirm their current table and record context before navigating back. They look at the breadcrumb at the top of the screen and see the current table and record, separated from the screen body by a blank line.

### 6.3 Starting at the top of the hierarchy

An operator opens the application and lands on the list of tables, before selecting any record. They see a root breadcrumb segment naming this top-level view (e.g. "Tables"), so the breadcrumb is never blank even when nothing has been selected yet.

### 6.4 Navigating during a loading or error state

An operator triggers an action that causes the screen to show a loading state, then an error. The breadcrumb at the top of the screen remains visible throughout, so the operator never loses track of their current location even while something unexpected is happening.

## 7. Functional requirements

### Display

- F1. The system displays the breadcrumb at the top of the screen on every screen that has a navigation location to show.
- F2. The breadcrumb reflects the user's current table and record context, omitting intermediate relation hops.
- F3. The system updates the breadcrumb whenever the user navigates to a different screen, so it always reflects the current location.
- F4. When the user is at the very top of the hierarchy (no table or record selected yet), the system displays a root segment naming the top-level view (e.g. "Tables").
- F5. When the breadcrumb's segments would not fit on one line, the system truncates the middle segments and keeps the first and last segments visible.
- F6. A record segment in the breadcrumb is identified by the record's primary key value.
- F7. The system displays the breadcrumb at all times, including while the screen is in a loading or error state.

## 8. Non-functional requirements

- N1. The breadcrumb must be visually legible — not blank, not rendered with colors or styling that make it invisible against the background, and not obscured by other UI elements.
- N2. The breadcrumb must remain visible regardless of terminal size.
- N3. The breadcrumb must be separated from the screen body by a blank line.

## 9. Acceptance criteria

### Display

- AC1. Given any screen with a navigation location, when the screen is rendered, then the breadcrumb is visible at the top of the screen.
- AC2. Given the breadcrumb is displayed, when the user reads it, then its text is legible and not blank or obscured.
- AC3. Given the user navigates to a different screen, when the new screen renders, then the breadcrumb updates to reflect the new current position.
- AC4. Given a small terminal window, when the screen is rendered, then the breadcrumb remains visible at the top.
- AC5. Given the user has drilled from a table into a record's related entity, when the breadcrumb is rendered, then it shows the current table and record context without listing the intermediate relation hop.
- AC6. Given the user is at the top-level table list with no record selected, when the breadcrumb is rendered, then a root segment naming the top-level view is shown.
- AC7. Given a breadcrumb whose segments would not fit on one line, when it is rendered, then the middle segments are truncated while the first and last segments remain visible.
- AC8. Given a record segment in the breadcrumb, when it is rendered, then it shows the record's primary key value.
- AC9. Given the breadcrumb is rendered, when the user looks below it, then it is separated from the screen body by a blank line.
- AC10. Given a screen in a loading or error state, when the screen is rendered, then the breadcrumb is still visible.

## 10. Dependencies and assumptions

- Assumes the breadcrumb's underlying navigation-hierarchy data already exists and is already being computed correctly; this epic is specifically about the breadcrumb not being visible, not about incorrect hierarchy data.
- The root cause of the breadcrumb's current invisibility is not yet known; this epic includes diagnosing why it's invisible as part of delivering the fix, since the briefing only states the symptom.
- No dependency on other epics in the roadmap (EP-2, EP-3) — this epic can be delivered independently.

## 11. Open questions

## 12. Decision log

### Cycle 1 — answered

| #   | Question | Decision |
| --- | -------- | -------- |
| Q1  | Breadcrumb content at the top of the hierarchy | Show a single root segment naming the top-level view (e.g. "Tables") |
| Q2  | Overflow handling for a very long navigation path | Truncate the middle segments and keep the first and last few visible |
| Q3  | Whether the root cause of invisibility is known | Not yet known; this epic includes diagnosing why it's invisible as part of delivering the fix |
| Q4  | Visual separation from other top-of-screen content | The breadcrumb must be separated from the screen body by a blank line |
| Q5  | Scope of navigation steps reflected in the breadcrumb | Reflects only the current table and record, omitting intermediate relation hops |
| Q6  | What identifies a record segment | The record's primary key value |
| Q7  | Visibility during loading/error states | Yes — the breadcrumb remains visible at all times, including during loading and error states |
