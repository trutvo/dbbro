---
name: readme
description: >-
  Produces English arc42-style architecture documentation in a single repository-root
  README.md by reading the codebase. Renames an existing README.md to README.pre-arc42.md
  and merges its content into the new doc. Default depth is agile/lean; user may request
  thorough/audit depth. Uses Mermaid when helpful. Cites concrete repo evidence (paths,
  configs, entrypoints) and asks the user when evidence is missing. Use only when the user
  explicitly invokes this skill or names arc42 README-from-code documentation.
disable-model-invocation: true
---

# arc42 README from code

## When this applies

- User asked for this skill **explicitly** (by name or clear intent: e.g. “generate arc42 README from the code”).
- Target is **repository root** `README.md` only (not package subfolders unless the user says otherwise).

## Depth

| Mode                | Signals from user                             | Behavior                                                                                                 |
| ------------------- | --------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| **Agile (default)** | (none), “lean”, “lightweight”, “minimal”      | All 12 arc42 sections present; keep each short. Prefer bullets and one diagram if it clarifies a lot.    |
| **Thorough**        | “thorough”, “full arc42”, “audit”, “detailed” | Same structure; expand runtime/deployment/quality/risk with more scenarios, interfaces, and constraints. |

If unclear, assume agile and mention that assumption once in chat.

## Workflow

1. **Discover** — Scan the repo: entrypoints (`main`, CLI, handlers), build/deploy files, package manifests, infra (Docker, k8s, CI), configs, dominant languages/frameworks.
2. **Evidence** — Every non-trivial claim should tie to something inspectable (`path/to/file`, module, workflow name). If you cannot verify (e.g. business goals, SLAs), **ask the user in chat** and add an **Open points / Clarifications** subsection under the relevant arc42 section (or at the end if global).
3. **Existing README** — If `README.md` exists:
   - Rename it to **`README.pre-arc42.md`** in the same directory (do not delete).
   - Incorporate its content into the new `README.md` by **mapping** fragments into the appropriate arc42 sections (e.g. install/run → deployment or intro; features → goals/context). Preserve factual detail; drop pure duplication.
4. **Write** — Single `README.md` at repo root, English, following the section template below. Use **Mermaid** for context, deployment, or sequence sketches when grounded in what you saw.
5. **Verify** — Reread output: no invented components; placeholders only where flagged as open points.

## README structure (single file)

Use this order and headings (adapt title line 1 to the project name if known from evidence):

```markdown
# <Project name>

Brief elevator pitch grounded in repo evidence (one short paragraph).

## 1. Introduction and goals

- **Requirements / purpose** — from README.pre-arc42, product docs, or user; cite `[README.pre-arc42.md](README.pre-arc42.md)` if used.
- **Stakeholders** — only if known; otherwise open point.

## 2. Constraints

Technical and organizational constraints visible in repo (languages, CI, hosts, licences). Cite files.

## 3. Context and scope

**Scope:** in/out briefly.  
**External interfaces:** APIs, queues, DBs, third parties — only if evidenced in config or code; cite paths.

*(Optional Mermaid: context diagram — boxes only for verified dependencies.)*

## 4. Solution strategy

Key technical choices (framework, datastore, messaging) with rationale tied to codebase.

## 5. Building block view

Major modules/packages/services with responsibilities. Directory or package paths in backticks.

*(Optional Mermaid: component/containment diagram — must match repo structure.)*

## 6. Runtime view

1–3 scenarios (e.g. request path, job, CLI) as short numbered flows. Evidence-based.

*(Optional Mermaid: sequence diagram for the most important flow.)*

## 7. Deployment view

How/where it runs: containers, CI/CD, environments — from Dockerfiles, workflows, Helm, etc.

*(Optional Mermaid: deployment sketch if clear.)*

## 8. Cross-cutting concepts

Security, logging, error handling, configuration — only patterns you can point to in code or config.

## 9. Architecture decisions

Important decisions **inferred** from structure and dependencies. Prefer linking to real files; use “Decision / Rationale / Consequences” bullets. If the repo has an `adr` or decisions folder, reference it.

## 10. Quality

Quality goals that are visible (tests, linters, coverage config) or stated in docs. Otherwise brief + open points.

## 11. Risks and technical debt

Only from evidence (TODO/FIXME density, missing tests, deprecated deps, security notes). Do not invent risks.

## 12. Glossary

Terms and acronyms used in this README (and from prior README) that readers need.

---

## Open points / Clarifications needed

*(List questions for the user; remove this section once resolved in a follow-up if the user prefers.)*
```

**Agile:** many subsections can be 2–6 bullets. **Thorough:** add subsections, more runtime scenarios, richer quality tree, explicit interfaces and failure handling.

## Rules

- **One file:** all content in `README.md`; diagrams inline as Mermaid fenced blocks.
- **No silent overwrite** of an existing `README.md` — always rename to `README.pre-arc42.md` first.
- **Honesty:** if the repo is empty or opaque, say so, produce a skeleton, and list required clarifications.
- Do **not** paste large blocks of arc42.org text; structure is enough.

## After delivery

Tell the user briefly: (1) whether `README.pre-arc42.md` was created, (2) depth used, (3) any open points they should answer.
