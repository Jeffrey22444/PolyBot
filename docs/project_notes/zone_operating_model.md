# Zone Operating Model

## Low-Overhead Defaults

- Use the shortest artifact that safely carries the work.
- Do not repeat stable project rules in every prompt; reference `AGENTS.md`, this file, product consensus docs, architecture docs, and the implementation plan.
- Start with 3-5 files to read, then expand only when needed.
- In task cards, keep `先读` to the minimum required set. Put other docs behind explicit on-demand triggers such as "如需确认策略边界，再读 ...".
- Prefer short task cards over full handoffs for small and medium work.
- Do not split work so finely that `执行区` loses momentum; prefer medium-sized coherent slices with clear gates.
- Do not read `issues.md` end to end by default; read `Current Summary` plus the latest log block for the current task ID.
- Use `/private/tmp` handoffs only for complex, risky, ambiguous, multi-stage, or failed-acceptance work.
- Use `docs/project_notes/current_task.md` as the only persistent current-task surface; overwrite it when the next task starts.
- Treat old task-card files as archives. Do not append detailed task cards there by default.
- Every execution task gets a short Acceptance Contract.
- A separate Acceptance pass is required only for risky, user-critical, or explicitly requested work.
- Every execution task card must be specific enough that `执行区` does not need to invent strategy, product behavior, runtime choice, storage design, or unresolved phase gates.
- Once local workflow docs have been synced from `zone-memory`, prefer those local docs over rereading the skill on normal tasks.
- Reopen `zone-memory` only for explicit workflow resyncs or when local rules appear stale, incomplete, or contradictory.

## Planning

Responsibilities:

- clarify goals, constraints, risks, assumptions, and acceptance criteria
- discuss options and recommendations before handing work to execution
- create short task cards for small and medium work
- lock down which decisions remain with `规划区` and must not be silently made by `执行区`

Boundaries:

- do not edit production code unless explicitly asked
- do not silently decide unclear product behavior

Preferred output:

- short discussion and recommendation first
- then either a short task card or a full handoff when complexity warrants it
- when pairing execution and acceptance, avoid duplicate reading and duplicate test instructions unless risk warrants it
- avoid sending unchanged docs back through every zone when the task can proceed from a smaller required set
- when sending work from `规划区` to another zone, keep everything that target zone needs inside one continuous copy block
- for paired execution and acceptance routing, the default is one copy block for `执行区` and one copy block for `验收区`
- default to a two-hop flow: `规划区 -> 执行区`, then `规划区 -> 验收区`; execution evidence should be written back into `issues.md` instead of manually relayed by the user
- write the active task card and acceptance contract to `current_task.md`; do not keep growing historical task-card files
- when `current_task.md` is the active task surface, the planning reply should not repeat the full task card; end with short copy-ready prompts that tell `执行区` or `验收区` to read `current_task.md` and name the task ID
- when using a `/private/tmp` handoff, include the absolute handoff path and direct paste targets for the next zone
- keep `issues.md` minimal: current recommended next task plus short evidence/decision summaries, not full paste-ready prompts

Verification defaults:

- For small doc-only planning updates, do not run `git diff --check` by default.
- Use `git status --short` or targeted file reads when the goal is only to confirm which files changed.
- Run `git diff --check` only after larger Markdown rewrites, complex fenced code blocks, `.gitignore` edits, or concrete whitespace/conflict-marker risk.
- Do not run full `git diff` as a routine planning check; use targeted diffs only when exact changed lines are needed.

## Execution

Responsibilities:

- read the relevant docs, task card, and memory files
- read `current_task.md` for the assigned task; do not scan historical task-card archives unless the current task explicitly says to
- implement the smallest working change
- reuse existing patterns
- run focused verification
- report evidence
- stop when the task depends on an undecided planning item

Boundaries:

- do not redesign scope
- do not change product behavior beyond the task
- stop if the task conflicts with safety rules, consensus docs, or code reality
- do not silently decide unresolved product, architecture, or phase-gate questions

Preferred output:

- short implementation summary
- required evidence report using the fixed template below

## Acceptance

Responsibilities:

- inspect the diff, tests, and behavior against the task
- verify acceptance criteria, safety boundaries, and regression risk
- decide pass or fail
- use the Acceptance Contract plus execution evidence plus current diff as the default input set
- read the current Acceptance Contract from `current_task.md`
- read execution evidence from `docs/project_notes/issues.md` by task ID when available instead of requiring manual paste-through

Boundaries:

- do not modify code
- do not redesign the solution
- do not repeat the full execution task unless the handoff explicitly requires it

Preferred output:

- pass/fail first
- findings by severity with file and line references
- a minimal return task only when needed

## Maintenance

Responsibilities:

- inspect Git status, branches, diffs, remotes, and untracked files
- inspect environment, dependency, and runtime-state problems
- route product-code changes back to execution

Boundaries:

- do not design product behavior
- do not modify code or config unless explicitly asked
- do not merge, rebase, reset, push, or delete branches without explicit approval

Preferred output:

- current state summary
- key evidence
- safe next step

## Standard Cards

Execution task card:

```text
目标：
范围外：
先读：
交付物：
修改点：
执行区自测：
停止条件：
```

Acceptance Contract:

```text
任务ID：
目标：
必须不做：
必测：
重点风险：
验收输入：验收合同 + issues.md 中当前任务ID对应的最新执行证据块 + 当前 diff
```

Maintenance handoff:

```text
状态：
证据：
风险：
建议交给：
三行转交摘要：
```

Execution evidence report:

```text
任务ID：
改动文件：
范围边界：
运行命令：
结果：
手工检查：
范围外未做：
阻塞/待规划决定：
```

Issues log evidence block:

```text
### YYYY-MM-DD - <task summary>
任务ID：
改动文件：
范围边界：
运行命令：
结果：
手工检查：
范围外未做：
阻塞/待规划决定：
```

Acceptance review task:

```text
目标：
先读：
验收输入：
重点检查：
不要重复：
输出：
```

## Zone Thread Defaults

- Use these exact Chinese zone names by default: `规划区`, `执行区`, `验收区`, `维护区`.
- Do not create English-named duplicate zones unless the user explicitly asks.
- Opening replies for newly created zones should be one short acknowledgement or one short status line.
- Default model/thinking settings when creating zone threads:
  - `规划区`: `gpt-5.5`, high thinking
  - `执行区`: `gpt-5.5`, medium thinking
  - `验收区`: `gpt-5.4`, medium thinking
  - `维护区`: `gpt-5.4`, medium thinking

## Project Note File Rules

- `bugs.md`: only resolved or recurring bugs; record issue, root cause, fix, and prevention.
- `current_task.md`: the current active task card and/or acceptance task only; overwrite it for the next task instead of preserving detailed historical prompts.
- `decisions.md`: durable ADRs and workflow decisions; update an existing ADR when a decision changes instead of piling up contradictions.
- `key_facts.md`: stable non-secret facts first; drift-prone environment facts stay short and dated.
- `issues.md`: live summary first, chronological log below; read Current Summary plus the latest relevant task block by default.
- `issues.md`: execution evidence may use the standard detailed template or an equivalent compact `Changed / Verified / Manual / Scope skipped` shape when that is clearer for the current task.
- `zone_operating_model.md`: zone responsibilities, boundaries, and standard cards; keep it short enough to reread quickly.
- `docs/product_consensus/...`: confirmed behavior, locked non-goals, and unresolved product decisions that execution must not silently decide.
- `docs/architecture.md`: required module boundaries and dependency direction; keep the first version concrete.
- `docs/implementation-plan.md`: phase deliverables, verification, and gates so later slices do not start early.
- Historical task-card documents are archives only; keep future history in `issues.md` as concise summaries of task intent, changed files, evidence, and blockers.

## Anti-Patterns

- Do not make `issues.md` the only current truth without a summary block.
- Do not mix stable facts with progress logs in `key_facts.md`.
- Do not force a full Acceptance pass on trivial slices.
- Do not repeat stable rules in every task card.
- Do not keep appending full task cards to a growing archive when `current_task.md` is enough.
- Do not make execution invent runtime, storage, strategy rules, or phase gates.
- Do not send acceptance the full execution prompt when the contract plus evidence is enough.
- Do not add more zones, files, or roles before there is a real need.
