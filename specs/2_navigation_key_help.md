# Epic 2 — Navigation Key Help

PRD for Navigation Key Help. Requirements only — no technical or architectural decisions.

> **Confidence:** ~93% after Cycle 2 — all prior gaps resolved (overflow, toggling, priority order, wording, scope, contextual availability, coexistence, transient-state visibility); remaining risk is minor (exact truncation threshold is left to implementation, not specified as a character count)

## 1. Summary

Users navigating the application currently have no on-screen reminder of which keys move them around. This epic adds a one-line help summary of the available navigation keys, displayed at the bottom of the screen, so users can discover and recall how to navigate without leaving the application or consulting external documentation.

## 2. Goals

- Every screen that supports navigation shows a one-line summary of the keys available on that screen.
- The help line always reflects the keys that are actually usable on the current screen (not a static, generic list).
- Users can navigate confidently without needing to memorize keys in advance or look them up elsewhere.

## 3. Out of scope

- A dedicated, expandable, or multi-line help screen (this epic covers only the one-line summary).
- Customization of key bindings by the user.
- Localization/translation of the help text into languages other than the application's existing display language.

## 4. Personas

- **Operator** — a person browsing and inspecting database records through the TUI, who may be new to the tool or an infrequent user, and needs a fast in-context reminder of navigation controls.

## 5. Domain concepts

- **Screen** — a distinct view within the application (e.g. table view, record detail, entity list) that has its own set of applicable navigation keys.
- **Navigation key** — a keyboard key or key combination the user can press on the current screen to move, select, or otherwise navigate (e.g. move selection, go back, open a record, quit).
- **Help line** — the single line of text rendered at the bottom of the screen listing the navigation keys applicable to the current screen, along with a short label for what each key does. It occupies its own dedicated bottom line, separate from any other bottom-of-screen element such as a status bar.
- **Key label** — the text shown for a navigation key on the help line, formatted as the key followed by a short verb (e.g. "enter open", "esc back").
- **Key priority** — the relative importance of a navigation key on a given screen, ordered by how frequently the key is expected to be used (e.g. move/select keys before quit), used to decide which keys are dropped first when space is limited.

## 6. User journeys

### 6.1 Discovering navigation on first use

An operator opens the application for the first time and lands on a screen. Without any prior knowledge of the key bindings, they look at the bottom of the screen and see a one-line list of the keys they can press and what each does (e.g. "↑/↓ move · enter open · esc back · q quit"). They press one of the listed keys and the corresponding action occurs.

### 6.2 Moving between screens with different controls

An operator moves from the table view to a record detail screen, where a different set of navigation actions is available. The help line at the bottom updates to reflect only the keys applicable to the new screen.

### 6.3 Recalling a forgotten key

An operator has been using the application for a while and briefly forgets which key returns to the previous screen. They glance at the bottom of the screen, see the help line, find the "back" key, and press it.

### 6.4 Navigating on a narrow terminal

An operator resizes their terminal to a narrow width while viewing a screen with many navigation keys. The help line drops the lowest-priority keys (e.g. quit) first and keeps showing the higher-priority ones (e.g. move, open, back) so it still fits on one line.

### 6.5 Encountering a contextually unavailable action

An operator is on the last page of a paginated list, where "next page" is not currently a valid action. The help line does not list "next page" at all, since it omits keys that are not currently usable, so the operator is not misled into pressing a key that does nothing.

### 6.6 Navigating while data loads or an error is shown

An operator triggers an action that causes the screen to show a loading state, then an error. The help line remains visible throughout, showing keys such as "back" or "quit", so the operator can always leave the current state.

## 7. Functional requirements

### Display

- F1. The system displays a single line of help text at the bottom of the screen on every screen in the application, since every screen supports some form of navigation.
- F2. The help line lists each navigation key applicable to the current screen together with a short label describing its action, formatted as the key followed by a short verb (e.g. "enter open").
- F3. The system updates the help line whenever the user moves to a screen with a different set of applicable navigation keys, so the line always reflects the current screen's keys.
- F4. The system omits from the help line any navigation key that is not currently usable in the current context (e.g. "next page" when there is no next page).
- F5. When the full set of applicable navigation keys does not fit on one line, the system truncates the list by dropping the lowest-priority keys first, ordered by expected frequency of use, until the remaining keys fit.
- F6. The system displays the help line at all times, including while the screen is in a loading or error state.

## 8. Non-functional requirements

- N1. The help line must remain a single line regardless of terminal width; it must not wrap onto a second line.
- N2. The help line must fit within the terminal width or be truncated/abbreviated in a way that keeps it legible, since terminal widths vary.
- N3. The help line must occupy its own dedicated bottom line, separate from any other bottom-of-screen UI element (e.g. status bar, breadcrumb), so it never collides with or obscures them.
- N4. The help line is not user-toggleable; it is always visible on every screen, including during loading and error states, since there is no expert mode that hides it.

## 9. Acceptance criteria

### Display

- AC1. Given any screen that supports navigation, when the screen is rendered, then a one-line help summary is visible at the bottom of the screen.
- AC2. Given the help line is displayed, when the user reads it, then it lists only keys that are actually usable on the current screen.
- AC3. Given the user navigates from one screen to another with a different set of navigation keys, when the new screen renders, then the help line updates to reflect the new screen's keys.
- AC4. Given a narrow terminal window, when the help line is rendered, then it does not wrap to a second line.
- AC5. Given a screen with more navigation keys than fit on one line, when the help line is rendered, then the lowest-priority keys (e.g. quit) are dropped first and the higher-priority keys (e.g. move, open, back) remain visible.
- AC6. Given a screen with a navigation key that is not currently usable (e.g. "next page" on the last page), when the help line is rendered, then that key is not listed.
- AC7. Given a screen with another bottom-of-screen element such as a status bar, when the help line is rendered, then it appears on its own line, distinct from that element.
- AC8. Given a screen in a loading or error state, when the screen is rendered, then the help line is still visible.
- AC9. Given any screen, when the user looks for a way to hide the help line, then no such control exists — the help line is always shown.

## 10. Dependencies and assumptions

- Assumes each screen in the application has a well-defined, enumerable set of navigation keys that can be queried or listed.
- No dependency on other epics in the roadmap (EP-1, EP-3) — this epic can be delivered independently.

## 11. Open questions

## 12. Decision log

### Cycle 1 — answered

| #   | Question | Decision |
| --- | -------- | -------- |
| Q1  | Overflow handling when keys don't fit on one line | Truncate the list, dropping the lowest-priority keys, and show only what fits |
| Q2  | Should the help line ever be hidden or toggled off | No — it is always visible on every navigable screen |
| Q3  | Priority order of keys under limited space | Order by how frequently the key is expected to be used (e.g. move/select before quit) |
| Q4  | Key label wording | Key plus short verb, e.g. "enter open" |
| Q5  | What counts as "a screen that supports navigation" | Every screen in the application supports some navigation, so the help line appears everywhere |
| Q6  | Content for contextually unavailable keys | Unavailable keys are omitted from the line entirely |
| Q7  | Coexistence with other bottom-of-screen elements | The help line occupies its own dedicated bottom line, separate from any status bar |
| Q8  | Visibility during loading/error states | Yes — the help line remains visible at all times, including during loading and error states |
