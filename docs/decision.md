# Themis code decision log

A running log of every code change in this repo. An entry is appended **before** the change is made. No entry, no change.

## Rules
- Append only. Never edit or delete a past entry.
- If a change spans multiple sessions, each session gets its own dated entry.
- If a change is reverted, add a new entry explaining the revert rather than deleting the original.
- If you are unsure whether a change needs an entry, it does.

## Entry format
```markdown
## [short title of the change]
**Date**: YYYY-MM-DD
**File(s) affected**: list every file being created, edited, or deleted

### What I am changing
### Why I am making this change
### Alternatives I considered
### Reasons I rejected each alternative
### Trade-offs I am accepting
### What could go wrong
### How this affects other components
```

---

## Create the project knowledge vault and planning documents
**Date**: 2026-09-28
**File(s) affected**:
- `docs/vault/00 Index.md` (created)
- `docs/vault/01 Project/`: Vision, Scope, Non-Goals, Success Metrics, Glossary (created)
- `docs/vault/02 Architecture/`: Architecture Overview, Webhook Service, Job Queue, Context Builder, Review Graph, Finding Schema, Precision Filter, Guardrails, LLM Client, Storage (created)
- `docs/vault/03 Reliability/`: Tracing, Benchmark, Eval Harness, Metrics, CI Quality Gate, Drift Monitoring, Ablation Table (created)
- `docs/vault/04 Decisions/`: ADR-001 to ADR-008 (created)
- `docs/vault/05 Stack/`: one note per technology, 15 notes (created)
- `docs/vault/06 Risks/`: Eval Cost, Label Noise, Hosting, Scope Creep (created)
- `docs/vault/07 Progress/`: Current Status, Session Log, Open Questions (created)
- `docs/vault/08 Results/README.md` (created)
- `docs/decision.md` (created)
- `docs/flow.md` (created)
- `.gitignore` (created)

### What I am changing
Adding planning documentation only: an Obsidian vault holding the approved spec, this decision log, and an execution-flow document with every section marked `[NOT YET BUILT]`. `.gitignore` excludes Obsidian's local `.obsidian/` config folder. No application code is added.

### Why I am making this change
The spec requires the vault, decision log, and flow document to exist before any application code, so that every later change has a source of truth to follow and a place to be recorded.

### Alternatives I considered
1. Keep the notes in the existing standalone Obsidian vault outside the repo (`../Themis/Themis`).
2. Write the spec as a single long document instead of linked notes.
3. Commit the `.obsidian/` folder so vault settings are shared.

### Reasons I rejected each alternative
1. The spec places the vault at `docs/vault/`, versioned with the code it describes.
2. One document cannot show dependencies in Obsidian's graph view, which the spec requires.
3. `.obsidian/` holds per-machine state and plugin data (including a local REST API key), which must not be published.

### Trade-offs I am accepting
Fifty-four small notes must be kept in sync by hand; renaming a note can break wikilinks. Worth it because the notes are the source of truth and the graph makes dependencies visible.

### What could go wrong
- Notes drift from the code as it is built.
- Frontmatter conventions differ from the spec's literal examples (see Open Questions 2–6) and may need to be changed.
- Unresolved Open Questions may be filled in ad hoc during implementation instead of being decided.

### How this affects other components
No component behavior changes. Every component note (Webhook Service, Job Queue, Context Builder, Review Graph, Finding Schema, Precision Filter, Guardrails, LLM Client, Storage) is created with `status: planned`.

---

## Add architecture canvas, graph view colors, and prior-art note
**Date**: 2026-09-28
**File(s) affected**:
- `docs/vault/Themis Map.canvas` (created)
- `docs/vault/01 Project/Prior Art.md` (created)
- `docs/vault/00 Index.md` (edited: links to the canvas and Prior Art)
- `docs/vault/07 Progress/Open Questions.md` (edited: proposals from prior art)
- `docs/vault/07 Progress/Current Status.md` (edited)
- `docs/vault/07 Progress/Session Log.md` (edited)
- `docs/vault/.obsidian/graph.json` (edited, local only, gitignored)

### What I am changing
Adding a visual reference map of the system as an Obsidian Canvas, colour groups for the graph view (by folder), and a note comparing Themis to a published course project (an AI GitHub PR reviewer). Ideas taken from that project are recorded as proposals in Open Questions, not added to the spec.

### Why I am making this change
Requested: "make graph in obsidian vault for reference" and permission to take inspiration from the course project. Project rules forbid adding features or technologies without a proposal, so inspiration is captured as proposals.

### Alternatives I considered
1. Only configure the built-in graph view.
2. Draw a second Mermaid diagram inside a note.
3. Adopt the course project's ideas directly into the spec.

### Reasons I rejected each alternative
1. The graph view shows every link equally and has no data-flow direction; kept only as a complement.
2. Architecture Overview already has a Mermaid diagram; the canvas adds clickable nodes that open the real notes.
3. Project rules require proposing new features/technologies before adopting them.

### Trade-offs I am accepting
The canvas is a hand-placed layout that must be updated when components change. Graph colours live in `.obsidian/`, which is gitignored, so they are local to this machine.

### What could go wrong
- The canvas drifts from the component notes if one is updated without the other.
- Renaming a note breaks its canvas file node.

### How this affects other components
No component behaviour changes. No component note is edited.
