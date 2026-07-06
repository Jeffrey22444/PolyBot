# Key Facts

## Stable Facts

- Workspace root: `/Users/jeffrey/Documents/PolyBot`
- Product consensus: `docs/product_consensus/polymarket_paper_trader_v1.md`
- Architecture doc: `docs/architecture.md`
- Implementation plan: `docs/implementation-plan.md`
- Project note directory: `docs/project_notes`
- Primary workflow file: `AGENTS.md`
- Zone model file: `docs/project_notes/zone_operating_model.md`
- Default zones: `规划区`, `执行区`, `验收区`, `维护区`
- Default Git main branch: `main`
- Current product mode: paper trading only
- Current strategy split: `Signal`, `Market Data`, `Marketability`, `Paper Execution`, `Reporting`
- Phase 1 runtime: Python standard library, no third-party dependencies
- Current runner mode: single explicit market/session paper runner, JSONL output, no live orders
- Dependency file: `requirements.txt`

## Last Verified Environment

- Verified on: 2026-07-06
- Git repository: initialized locally with branch `main`
- Existing product docs: product consensus, architecture, and implementation plan now tracked under `docs/`
- Existing source files: `polybot/` package with signal, market data, marketability, paper records, and paper runner modules
- Zone threads created: `规划区`, `执行区`, `验收区`, `维护区`
