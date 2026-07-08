# Current Task

This file is the only persistent current-task surface for `执行区` and `验收区`.
Overwrite it when the next task starts. Do not preserve detailed historical task
cards here; keep history in `issues.md` as concise summaries and evidence.

## Active Task

Task ID: polybot-paper-minimal-trade-ledger-and-polymarket-open

Status: execution complete; ready for `验收区`.

## 给执行区的任务

目标：
- 将每一个 BTC 15m Polymarket market 视为一条独立 paper trade 记录，写入本地最小后台账本。
- 让后续复盘可以直接按账本统计整体胜率、累计 paper PnL、模拟本金权益/收益率、失败时的剩余时间/涨跌幅/阈值/原因。
- 支持一个配置化模拟初始本金，默认 `1000`，每次已结算 paper PnL 累加到这笔模拟本金上。
- 修正 open price 来源：优先对齐 Polymarket 公开同源 open/reference 口径；如果只能 fallback，必须明确记录 fallback 来源，不能伪装成 Polymarket open。
- 终端只打印极简、针对复盘目的的关键结果行。

范围外：
- 不做实盘、钱包、签名、账号 API、真实订单。
- 不做云数据库、ORM、迁移框架、后台服务、UI、通知系统。
- 不存 raw WebSocket tick、完整 orderbook、完整 public payload、逐秒浮盈浮亏或持仓 mark-to-market。
- 不新增止损、止盈、反手、加仓、网格、多次入场。
- 不训练、不推断、不回填 `p_hat` 模型。
- 模拟本金只用于统计展示；不改变 stake sizing 或交易决策。

先读：
- `AGENTS.md`
- `docs/project_notes/zone_operating_model.md`
- `docs/project_notes/key_facts.md`
- `docs/product_consensus/polymarket_paper_trader_logic_chain.md`
- `docs/project_notes/issues.md` 的 Current Summary 和最近相关执行证据
- `polybot/e2e_dry_run.py`
- `polybot/open_price.py`
- `polybot/market_discovery.py`
- `polybot/paper_runner.py`
- `polybot/result_closer.py`
- `polybot/supervisor_results.py`
- `configs/polymarket_paper_btc_15m.yaml`

交付物：
- 新增一个标准库 `sqlite3` 本地账本实现，例如 `polybot/trade_ledger.py`。
- 默认账本路径建议为 `data/paper_trades.sqlite3`；如仓库未忽略 `data/` 或 `*.sqlite3`，同步更新 `.gitignore`，避免提交本地运行数据。
- 在 `configs/polymarket_paper_btc_15m.yaml` 的 `paper` 小节加入 `initial_bankroll: 1000` 或等价字段。
- 在 paper run 中按 market upsert 一条最小记录：
  - market 被选中时创建/更新基础行。
  - 触发开仓时写入 decision/trade 字段。
  - 未触发或跳过时写入 skip 字段。
  - resolution 可得时写入 WIN/LOSS/PENDING/SKIPPED 和 paper PnL。
- 保留现有 JSON artifacts；账本是长期复盘来源，不替代 run artifacts。
- 更新 `docs/operator_runbook.md`，说明账本路径、最小记录内容、终端极简打印口径。
- 将执行证据写入 `docs/project_notes/issues.md`。

最小 schema 建议：
```text
paper_trades
- market_id TEXT PRIMARY KEY
- market_start_time TEXT
- market_end_time TEXT
- open_price REAL
- open_price_source TEXT
- threshold_pct REAL
- observe_start_remaining_seconds INTEGER
- decision_time TEXT
- decision_remaining_seconds INTEGER
- decision_move_pct REAL
- signal TEXT
- side TEXT
- stake REAL
- entry_avg_ask REAL
- shares REAL
- result TEXT              -- WIN | LOSS | PENDING | SKIPPED | NO_TRADE
- winning_side TEXT
- paper_pnl REAL
- cumulative_pnl REAL
- equity_after REAL
- return_pct REAL
- skip_reason TEXT
- created_at TEXT
- updated_at TEXT
```

不要加入无助于复盘目标的字段。尤其不要存：
- event slug/title/question
- full token ids
- raw book levels
- raw WebSocket payload
- 每秒行情
- 页面展示细节
- 资金流水明细表

模拟本金要求：
- 默认 `initial_bankroll=1000`。
- `equity_after = initial_bankroll + 已结算累计 paper_pnl`。
- `return_pct = 已结算累计 paper_pnl / initial_bankroll * 100`。
- PENDING / SKIPPED / NO_TRADE 不应凭空改变已结算累计 PnL。
- 这只是复盘统计，不得影响每次 `stake` 或开仓判断。

open price 要求：
- 先检查 Polymarket public metadata / market payload 是否存在可用 open/reference/target price 字段。
- 如果存在，使用该字段并记录 `open_price_source` 为明确的 Polymarket 来源。
- 如果不存在，可以继续 fallback 到现有 Binance BTCUSDT open capture，但必须记录 `open_price_source=binance_btcusdt_fallback` 或等价明确名称。
- 终端和账本都不能把 fallback open 说成 Polymarket open。

终端极简打印要求：
```text
[TRADE] side=UP stake=9 ask=0.84 move=0.0539% rem=242
[SKIP] reason=observation_window_no_signal move=0.0305% rem=19
[RESULT] result=WIN side=UP pnl=+1.71 equity=1004.28 roi=0.43% win_rate=57.1% n=7
[RESULT] result=PENDING side=DOWN pnl=None equity=1004.28 roi=0.43% win_rate=57.1% n=7
```

打印边界：
- 每个 market 最多打印：开仓/跳过一行，结算/待结算一行。
- 不打印 raw orderbook、raw payload、token id、长 slug、逐秒 tick、完整 JSON。
- 北京时间前缀沿用已验收通过的 operator output 行为。

执行区自测：
- `python3 -m polybot.trade_ledger --self-check`
- `python3 -m polybot.e2e_dry_run --self-check`
- `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache python3 -m compileall -q polybot`
- `git diff --check`
- 补一个最小自检/样例，证明：
  - 同一个 `market_id` 重跑时是 upsert，不产生重复交易行。
  - WIN/LOSS/PENDING/SKIPPED/NO_TRADE 至少覆盖核心路径。
  - 可以从账本算出总交易数、已结算胜率、累计 paper PnL、当前模拟权益、收益率。
  - 账本没有存 raw orderbook/tick/payload。

停止条件：
- 如果 Polymarket public data 找不到 open/reference 字段，记录证据并使用明确 fallback；不要猜字段含义。
- 如果实现需要引入 ORM、迁移框架、云数据库、后台 service 或账号权限，停止并交回 `规划区`。
- 如果需要改变策略规则、止损/止盈、多次入场或实盘路径，停止并交回 `规划区`。

## Acceptance Contract

任务ID：
polybot-paper-minimal-trade-ledger-and-polymarket-open

目标：
- 验证每个 15m market 都会形成一条最小本地账本记录，能支持胜率、累计 PnL、模拟本金权益/收益率和失败条件复盘。
- 验证默认 `initial_bankroll=1000` 的收益率统计不影响交易决策。
- 验证 open price 来源不再被误称；Polymarket 同源优先，fallback 明确标记。
- 验证终端打印最小化且针对复盘目的。

必须不做：
- 不允许新增实盘、钱包/签名、账号 API、真实订单、云数据库、ORM、迁移框架、后台 service、UI、通知。
- 不允许存 raw tick、完整 orderbook、完整 public payload、逐秒浮盈浮亏。
- 不允许新增止损、止盈、反手、加仓、网格、多次入场或 `p_hat` 模型。

必测：
- 执行区列出的自测命令通过，或明确说明不可运行原因。
- 检查 SQLite schema 精简，只包含复盘所需字段。
- 检查同一 `market_id` upsert 不重复。
- 检查账本可计算：总市场数、已开仓数、已结算胜率、累计 paper PnL、当前模拟权益、收益率、失败/跳过原因分布。
- 检查 open_price_source 对 Polymarket/fallback 有明确区分。
- 检查终端输出每个 market 不刷屏，不打印 raw payload/orderbook/token id/长 slug。

重点风险：
- 把“复盘账本”做成过大的行情数据库。
- 继续把 Binance fallback open 叫成 Polymarket open。
- 为 SQLite 引入不必要依赖或迁移框架。
- 改动交易策略而不是记录层。

验收输入：
验收合同 + `issues.md` 中当前任务ID对应的最新执行证据块 + 当前 diff。
