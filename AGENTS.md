# PolyBot Workspace AGENTS

## Project Memory And Zone Workflow

### Read Order

Use progressive disclosure. Read only what is needed for the current task.

Task cards should default to a minimum required read set. Do not force every zone
to reread unchanged product, architecture, or phase docs unless the current task
actually depends on them. Prefer "read this if you need to confirm X" over
listing every related doc as mandatory.

1. Read this file first.
2. Read `docs/project_notes/zone_operating_model.md`.
3. Read `docs/project_notes/key_facts.md` before assuming commands, paths, ports, or conventions.
4. Read `docs/product_consensus/polymarket_paper_trader_v1.md` before discussing or changing strategy behavior.
5. Read `docs/architecture.md` before changing module boundaries, data flow, or execution/reporting separation.
6. Read `docs/implementation-plan.md` before sequencing phases, choosing deliverables, or defining verification gates.
7. Search `docs/project_notes/bugs.md` before debugging familiar errors.
8. Read `docs/project_notes/decisions.md` before proposing workflow or architecture changes.
9. Scan the current summary and relevant latest entry in `docs/project_notes/issues.md` when starting or handing off work.

### Project Memory System

This project keeps institutional knowledge in `docs/project_notes/`.

- `bugs.md`: resolved or recurring bugs with causes and fixes
- `decisions.md`: durable architectural or workflow decisions
- `key_facts.md`: non-secret stable project facts plus a short last-verified environment section
- `issues.md`: current-state summary plus chronological work log
- `zone_operating_model.md`: zone responsibilities, boundaries, and standard card shapes

### Memory Protocol

- Before proposing architecture or workflow changes, check `docs/project_notes/decisions.md`.
- Before debugging an error, search `docs/project_notes/bugs.md`.
- Before assuming project configuration, check `docs/project_notes/key_facts.md`.
- Update `docs/project_notes/issues.md` with meaningful work progress and completion notes.
- Do not read `docs/project_notes/issues.md` end to end by default. Read the `Current Summary` first, then only the latest log block for the current task ID.
- When resolving a reusable bug, add or update `docs/project_notes/bugs.md`.
- When making or changing a durable decision, add or update `docs/project_notes/decisions.md`.
- Do not store secrets, tokens, passwords, private keys, credential JSON, or credential values in project notes.

### Zone Defaults

- `规划区`: discuss goals, constraints, risks, options, and acceptance criteria before execution.
- `执行区`: implement only clearly assigned work, use the smallest working change, and gather evidence.
- `验收区`: review only, return pass/fail plus findings, and do not modify code.
- `维护区`: inspect Git, environment, dependencies, runtime state, and workspace hygiene.

### Zone Identity And Boundaries

- Keep track of the active zone and stay inside that zone's responsibilities.
- If the active zone is unclear, stop and ask the user to confirm it before doing substantive work.
- A zone must not silently take over another zone's job.
- `规划区` must not perform `验收区` or `维护区` work unless explicitly reassigned.
- `执行区` must not redesign scope, perform final acceptance, or manage Git history unless explicitly assigned.
- `验收区` must not edit code or docs.
- `维护区` must not design product behavior or implement feature code.

### Acceptance Routing Rule

Every execution task gets a short Acceptance Contract. A separate Acceptance pass is required only for risky, user-critical, or explicitly requested work.

Execution evidence should default to a write-back flow:

- `执行区` writes its evidence report into the latest matching task block in `docs/project_notes/issues.md`.
- `验收区` reads the Acceptance Contract, the `Current Summary`, the latest matching task block in `docs/project_notes/issues.md`, and the current diff.
- Do not require the user to manually relay the execution evidence between zones unless the task explicitly calls for it.

Zone thread defaults:

- Use the exact Chinese names `规划区`, `执行区`, `验收区`, `维护区`.
- Do not create English-named duplicate zones unless explicitly requested.
- Newly created zone threads should start with a minimal acknowledgement or next-step status.
- Keep paste-ready task blocks outside `issues.md`; use `issues.md` for summaries, decisions, and execution evidence.

### Polymarket Strategy Rules

- The root signal logic is the source of truth and must stay separate from marketability, sizing, and paper execution.
- `执行区` must not invent new trading rules, new signal factors, or new phase deliverables when docs leave them undecided.
- When a task hits an undecided item, stop and route it back to `规划区` instead of filling the gap.
- `验收区` should review against the Acceptance Contract plus the execution evidence report; it should not repeat the full execution task unless the handoff explicitly says so.

### Editing Rules

- Keep changes small and localized.
- Prefer existing code, standard library, native platform features, and existing dependencies.
- Do not add abstractions, services, factories, dependencies, or broad refactors without a current concrete need.
- Do not revert user changes or unrelated workspace changes.
- Do not merge, rebase, reset, push, or delete branches without explicit approval.
