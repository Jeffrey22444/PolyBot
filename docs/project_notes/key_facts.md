# Key Facts

## Stable Facts

- Workspace root: `/Users/jeffrey/Documents/PolyBot`
- Current strategy consensus: `docs/product_consensus/polymarket_paper_trader_logic_chain.md`
- Architecture doc: `docs/architecture.md`
- Implementation plan: `docs/implementation-plan.md`
- Project note directory: `docs/project_notes`
- Primary workflow file: `AGENTS.md`
- Zone model file: `docs/project_notes/zone_operating_model.md`
- Current task file: `docs/project_notes/current_task.md`
- Historical task-card archive: `docs/project_notes/polymarket_paper_execution_tasks.md` is retained for reference only; do not append new detailed task cards there by default
- Default zones: `规划区`, `执行区`, `验收区`, `维护区`
- Zone-memory sync status: synced into local workflow docs on 2026-07-06; normal future runs should read local docs first
- Default Git main branch: `main`
- Current product mode: paper trading only
- Current strategy split: `Signal`, `Market Data`, `Marketability`, `Paper Execution`, `Reporting`
- Phase 1 runtime: Python standard library, no third-party dependencies
- Current runner mode: single session-config paper runner, JSONL output, no live orders
- Current discovery mode: public metadata session config discovery exists
- Current open-price mode: automatic one-session open-price enrichment exists
- Current supervisor mode: bounded continuous supervisor exists
- Current result aggregation mode: supervisor result batch closing exists
- Current resolution mode: conservative automatic resolution ingestion exists
- Current local persistence mode: stable run artifacts and local index exist
- Current long-run mode: resumable long-run paper supervisor exists
- Current dry-run mode: public-data end-to-end dry run exists
- Current discovery hardening mode: public BTC 15m discovery hardening exists
- Current source calibration mode: BTC 15m public source calibration exists; use `--search-query "bitcoin up down 15m"` for current BTC 15m sessions
- Current open-price alignment mode: next-session wait-to-open with fresh WebSocket BTC open price exists
- Current entry-window proof mode: one real public BTC 15m session can reach tail signal and paper marketability output
- Current multi-session proof mode: one bounded public run can process two chronological BTC 15m sessions
- Current public closing mode: completed public sessions can be conservatively resolved and closed from unambiguous public metadata
- Current stability proof mode: Phase 21 public closed-loop proof passed with repeated close/resume/idempotence checks
- Current operator runbook mode: Phase 22 operator commands/status/runbook passed; see `docs/operator_runbook.md`
- Current local process supervision mode: Phase 23 local process supervision passed; see `docs/local_process_supervision.md`
- Fixed planned build track: complete through Phase 23
- Planning cap: continue with simulated operation and bug-driven fixes unless the user explicitly opens a new product decision
- Dependency file: `requirements.txt`

## Last Verified Environment

- Verified on: 2026-07-06
- Git repository: initialized locally with branch `main`
- Existing product docs: product consensus, architecture, and implementation plan now tracked under `docs/`
- Existing source files: `polybot/` package with signal, market data, marketability, paper records, and paper runner modules
- Existing workflow sync: local rulebook reflects the current `zone-memory` defaults that matter to this project
- Zone threads created: `规划区`, `执行区`, `验收区`, `维护区`
