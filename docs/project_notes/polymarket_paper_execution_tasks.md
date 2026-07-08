# Polymarket Paper Trading Task Plan

Archive status: historical reference only.

Do not append new detailed task cards here by default. Use
`docs/project_notes/current_task.md` as the active task surface and overwrite it
for each new phase. Preserve history in `docs/project_notes/issues.md` as concise
summaries and execution evidence, not full prompts.

Historical note:

This file used to be the copy-ready source for `执行区` and `验收区`.

Copy rule:

- everything for `执行区` stays in one continuous block so the user needs one copy action for that zone
- everything for `验收区` stays in one continuous block so the user needs one copy action for that zone

Stable context lives in:

- `AGENTS.md`
- `docs/project_notes/zone_operating_model.md`
- `docs/project_notes/key_facts.md`
- `docs/product_consensus/polymarket_paper_trader_v1.md`
- `docs/architecture.md`
- `docs/implementation-plan.md`

Do not restate those rules in every task unless a phase needs an exception.

## Phase Sequence

1. Phase 1: Root signal and paper skeleton
2. Phase 2: WebSocket-first market capture
3. Phase 3: Marketability and paper fill

Later phases are out of scope until these gates pass.

## Phase 1 Summary

Intent:

- build only the root signal module and the smallest paper-trading skeleton

Locked decisions:

- paper trading only
- Phase 1 runtime is Python standard library only
- no WebSocket yet
- no live trading
- no `p_hat` model yet
- no optimizer
- no new trading rules

Not for `执行区` to decide:

- storage design beyond the smallest assigned need
- any additional signal factors

If one of these is required, stop and route back to `规划区`.

## 给执行区的任务

```text
你现在是 PolyBot 的执行区。请使用 goal 模式执行下面任务。

目标：
建立 Polymarket 15m BTC 模拟盘的第一阶段骨架，只实现并隔离根本策略信号：
在 15 分钟市场还剩 3 或 4 分钟时，如果 BTC 相对本段开盘价的涨跌幅超过配置阈值，则按涨跌方向产生 UP / DOWN 信号。

范围外：
- 不接 WebSocket。
- 不做实盘。
- 不下单。
- 不添加第三方依赖。
- 不实现 p_hat 学习或估计。
- 不做参数优化。
- 不加入新的交易规则。
- 不让 ask、orderbook depth、spread、Kelly、账户余额影响 signal。
- 不自行决定未在 docs 中确认的存储或额外模块设计。

先读：
- AGENTS.md
- docs/project_notes/zone_operating_model.md
- docs/project_notes/key_facts.md
- docs/product_consensus/polymarket_paper_trader_v1.md
- docs/architecture.md
- docs/implementation-plan.md
- docs/project_notes/polymarket_paper_execution_tasks.md

交付物：
- 一个独立 signal 模块
- 一个最小 signal / paper record 数据结构
- 一个最小可运行的 signal 自测路径，例如 `python -m polybot.signal`

修改点：
- 使用 Python 标准库；如果需要包结构，只创建最小 `polybot/` package
- 只创建完成本 phase 所需的最小项目骨架
- signal 只接收 open price、current price、market end time、now、entry remain seconds、move threshold
- signal 只返回 UP / DOWN / NO_SIGNAL
- ENTRY_REMAIN_SECONDS 使用配置列表，默认 `[180, 240]`
- remaining_seconds 必须精确等于配置值才触发；不要自行发明时间窗口或容忍区间
- ret_pct = `(current_price - open_price) / open_price * 100`
- `abs(ret_pct) >= MOVE_THRESHOLD_PCT` 才触发信号
- open_price <= 0 或 current_price <= 0 时必须返回 NO_SIGNAL 或明确错误；不要继续计算
- Phase 1 只允许本地样例/测试数据，不允许接真实 WebSocket、REST、市场发现或盘口数据
- 将未来 marketability / execution 需要的数据结构留在边界之外，不提前混入 signal

执行区自测：
- 剩余时间命中且涨幅超过阈值时返回 UP
- 剩余时间命中且跌幅超过阈值时返回 DOWN
- 涨跌幅未超过阈值时返回 NO_SIGNAL
- signal 模块不依赖 ask、depth、spread、Kelly、p_hat、账户余额

停止条件：
- 需要决定存储方案、外部依赖或超出 Python 标准库的框架
- signal 模块开始依赖 marketability、paper execution 或其他未批准模块
- 发现 docs 之间存在冲突，无法确定 phase 交付边界
```

## 执行区证据报告模板

`执行区` 完成后必须按这个模板回报，并把同样内容写入 `docs/project_notes/issues.md` 的当前任务日志块，避免用户手动转发给 `验收区`：

```text
任务ID：
polybot-paper-phase-1-signal-core

改动文件：

范围边界：

运行命令：

结果：

手工检查：

范围外未做：

阻塞/待规划决定：
```

## 验收合同

```text
任务ID：
polybot-paper-phase-1-signal-core

目标：
根本策略信号模块存在，并且和 marketability、仓位、paper execution 隔离。

必须不做：
- 不接 WebSocket
- 不做实盘
- 不下单
- 不添加第三方依赖
- 不加新交易规则
- 不让 ask、depth、spread、Kelly、p_hat、账户余额进入 signal

必测：
- signal 测试或 self-check 通过
- Phase 1 使用 Python 标准库，且有 `python -m polybot.signal` 或等价小型自测路径
- signal 代码不依赖 ask、depth、spread、Kelly、p_hat、账户余额
- phase 交付物只覆盖 implementation plan 里定义的 Phase 1

重点风险：
- 把执行过滤条件污染进根本策略
- 在 signal 可测试前搭太多基础设施
- `执行区` 自行填补未决 storage / architecture 决策

验收输入：验收合同 + 执行区证据报告 + 当前 diff
```

## 给验收区的任务

```text
你现在是 PolyBot 的验收区。

目标：
只判断 Phase 1 是否通过，不改代码；重点检查 signal 是否被盘口、仓位、执行逻辑污染。

先读：
- AGENTS.md
- docs/project_notes/zone_operating_model.md
- docs/product_consensus/polymarket_paper_trader_v1.md
- docs/architecture.md
- docs/implementation-plan.md
- 上面的验收合同

验收输入：
- 验收合同
- `docs/project_notes/issues.md` 中 `polybot-paper-phase-1-signal-core` 的最新执行证据块
- 当前 diff

重点检查：
- signal 是否仍然是独立纯逻辑
- phase 交付物是否超出 Phase 1 gate
- 自测是否真的覆盖 UP / DOWN / NO_SIGNAL 三种结果
- 是否偷偷引入了 WebSocket、marketability、Kelly、p_hat、账户余额依赖

不要重复：
- 不要复述完整执行任务卡
- 不要把执行区证据报告再重写一遍
- 不要无差别重跑所有命令；只重跑最高信号检查

输出：
- 先给通过 / 不通过
- 若不通过，列问题、证据、文件行号、最小返工任务
```

## Phase 2 And Phase 3

## Phase 2 Summary

Intent:

- capture real-time Polymarket market data and BTC reference prices
- keep capture separate from signal, marketability, and paper execution

Locked decisions:

- continue using Python
- WebSocket first
- REST only for startup snapshot, reconnect recovery, or API verification
- no live trading
- no paper fill or PnL calculation yet

Not for `执行区` to decide:

- live order path
- wallet or credential setup
- paper fill rules
- final storage schema beyond the smallest capture records
- replacing WebSocket-first design with polling

If one of these is required, stop and route back to `规划区`.

## 给执行区的 Phase 2 任务

```text
你现在是 PolyBot 的执行区。请使用 goal 模式执行下面任务。

目标：
建立 Polymarket 15m BTC 模拟盘的 Phase 2 数据捕获层：用 WebSocket 优先捕获 Polymarket orderbook / best bid ask / market events，以及 BTC 参考价格数据；只记录数据，不做模拟成交和收益计算。

范围外：
- 不做实盘。
- 不下单。
- 不做 wallet、签名、credential、order placement。
- 不实现 marketability。
- 不实现 paper fill。
- 不计算 PnL。
- 不修改 Phase 1 signal 规则。
- 不加入新的交易规则。
- 不用低频轮询替代 WebSocket。

先读：
- AGENTS.md
- docs/project_notes/zone_operating_model.md
- docs/project_notes/key_facts.md
- docs/project_notes/polymarket_paper_execution_tasks.md
- polybot/signal.py
- polybot/paper.py

如需确认策略边界，再读：
- docs/product_consensus/polymarket_paper_trader_v1.md

如需确认模块边界，再读：
- docs/architecture.md

如需确认当前 phase gate，再读：
- docs/implementation-plan.md

交付物：
- 一个 market data capture 模块
- 一个 BTC reference price capture 模块，或明确记录为什么当前 phase 只能先接一个来源
- 一个最小 capture record 数据结构
- 一个短时运行的 capture 自测或 demo 命令
- API mismatch notes，如果官方文档与实际返回不同

修改点：
- 继续使用 Python。
- WebSocket 是主路径。
- REST 只能用于启动快照、重连恢复、或验证 token/orderbook 状态。
- 如果当前环境没有可用 WebSocket client，允许新增一个 WebSocket client 依赖；不要新增交易 SDK、钱包 SDK 或下单依赖。
- Polymarket 订阅应优先覆盖 orderbook、price_change、best_bid_ask、new_market、market_resolved 中 Phase 2 能安全记录的事件。
- 记录 source timestamp 和 local receive timestamp，用于后续 data age 判断。
- 捕获数据只写入最小本地记录；不要设计长期存储 schema。

执行区自测：
- 能运行一个短时 demo，证明 Polymarket WebSocket 连接或明确记录阻塞原因。
- 能记录至少一种 Polymarket market data 事件或 API mismatch。
- 能记录 BTC 参考价格，或明确记录当前来源阻塞原因。
- 代码中不存在下单、签名、wallet、credential、live order path。
- Phase 1 signal 代码未被 market data 捕获逻辑污染。

停止条件：
- 需要真实资金、wallet、私钥、credential 或交易权限。
- WebSocket API 行为与官方文档不一致且无法安全记录。
- 需要决定长期存储 schema。
- 需要把 market data 捕获逻辑写进 signal。
- 需要用轮询替代 WebSocket 作为主路径。
```

## Phase 2 执行区证据报告模板

`执行区` 完成后必须把这份证据写入 `docs/project_notes/issues.md` 的当前任务日志块，不要只停留在聊天回复里。

```text
任务ID：
polybot-paper-phase-2-market-capture

改动文件：

范围边界：

运行命令：

结果：

捕获到的数据类型：

API mismatch notes：

手工检查：

范围外未做：

阻塞/待规划决定：
```

## Phase 2 验收合同

```text
任务ID：
polybot-paper-phase-2-market-capture

目标：
WebSocket-first market data capture exists and remains separate from signal, marketability, paper fill, and live trading.

必须不做：
- 不下单
- 不接 wallet / signing / credentials
- 不实现 paper fill
- 不计算 PnL
- 不修改 Phase 1 signal 规则
- 不用轮询替代 WebSocket 主路径

必测：
- 短时 demo 或 self-check 能运行，或给出明确外部阻塞证据
- Polymarket market data 记录包含 source timestamp 和 local receive timestamp
- BTC reference price capture 有记录或明确阻塞说明
- 代码中无 live order / wallet / signing 路径
- signal 模块未依赖 market data capture

重点风险：
- 过早引入交易 SDK 或下单路径
- 用 REST 轮询绕过 WebSocket-first 约束
- 把 market data 捕获和 signal 逻辑混在一起
- 在 Phase 2 设计长期存储或收益计算

验收输入：验收合同 + issues.md 中当前任务ID对应的最新执行证据块 + 当前 diff
```

## 给验收区的 Phase 2 任务

```text
你现在是 PolyBot 的验收区。

目标：
只判断 Phase 2 是否通过，不改代码；重点检查 market data capture 是否 WebSocket-first，且没有引入下单、paper fill、PnL 或 signal 污染。

先读：
- AGENTS.md
- docs/project_notes/zone_operating_model.md
- 上面的 Phase 2 验收合同

如需确认策略边界，再读：
- docs/product_consensus/polymarket_paper_trader_v1.md

如需确认模块边界，再读：
- docs/architecture.md

如需确认当前 phase gate，再读：
- docs/implementation-plan.md

验收输入：
- Phase 2 验收合同
- `docs/project_notes/issues.md` 中 `polybot-paper-phase-2-market-capture` 的最新执行证据块
- 当前 diff

重点检查：
- WebSocket 是否是主路径
- REST 是否只用于启动、重连或验证
- 是否存在 wallet、signing、credential、order placement
- 是否偷偷实现了 paper fill 或 PnL
- signal 模块是否仍然独立
- 捕获记录是否有 source timestamp 和 local receive timestamp

不要重复：
- 不要复述完整执行任务卡
- 不要重写执行区证据报告
- 不要无差别重跑所有命令；只重跑最高信号检查

输出：
- 先给通过 / 不通过
- 若不通过，列问题、证据、文件行号、最小返工任务
```

## Phase 3 Summary

Intent:

- consume valid Phase 1 signals and Phase 2 market data records
- decide whether the signal is tradable at real ask-side depth
- simulate a paper fill without placing an order
- report signal-only and tradable-signal outcomes separately

Locked decisions:

- no live trading
- no wallet/signing/credentials
- no order placement
- no final `p_hat` model
- `p_hat` is caller-supplied only
- fixed small paper stake by default
- Kelly is only a cap/reference when enough inputs are supplied

Not for `执行区` to decide:

- final `p_hat` estimation method
- optimizer or parameter sweep
- stop-loss, take-profit, averaging, reverse, or multi-entry rules
- long-term storage schema
- live trading path

If one of these is required, stop and route back to `规划区`.

## 给执行区的 Phase 3 任务

```text
你现在是 PolyBot 的执行区。请使用 goal 模式执行下面任务。

目标：
建立 Phase 3 marketability + paper fill 层：给定一个有效 signal、当前 ask-side orderbook depth、固定小额 paper stake、以及外部传入的 p_hat，判断是否可交易，模拟 ask-depth 成交，并分别记录 signal-only 与 tradable-signal 结果。

范围外：
- 不做实盘。
- 不下单。
- 不做 wallet、签名、credential、order placement。
- 不实现或训练 p_hat 模型。
- 不从历史结果推断 p_hat。
- 不做参数优化。
- 不加入 stop-loss、take-profit、averaging、reverse、multi-entry。
- 不修改 Phase 1 signal 规则。
- 不修改 Phase 2 WebSocket capture 主路径。
- 不设计长期存储 schema。

先读：
- AGENTS.md
- docs/project_notes/zone_operating_model.md
- docs/project_notes/key_facts.md
- docs/project_notes/polymarket_paper_execution_tasks.md
- docs/project_notes/issues.md 的 Current Summary 和最新 Phase 2 相关日志块
- polybot/signal.py
- polybot/paper.py
- polybot/market_data.py

如需确认策略边界，再读：
- docs/product_consensus/polymarket_paper_trader_v1.md

如需确认模块边界，再读：
- docs/architecture.md

如需确认当前 phase gate，再读：
- docs/implementation-plan.md

交付物：
- 一个 marketability 模块
- 一个 ask-side depth fill simulation 函数
- 一个 paper trade / skipped trade record 数据结构
- 一个 signal-only 与 tradable-signal 分离的最小报告函数或 demo
- 一个最小自测或 demo 命令

修改点：
- Marketability 必须消费 Signal 和 Market Data；不能创建或修改 Signal。
- Paper fill 只能模拟，不能下单。
- Fill price 必须 walk ask-side depth，不能用 midpoint、last trade、best ask 代替整笔成交均价。
- trade_edge = caller_supplied_p_hat - executable_avg_ask。
- 如果 p_hat 缺失，只能记录无法计算 trade_edge；不要自行估算 p_hat。
- 默认 stake 使用固定小额输入。
- Kelly 只在 p_hat 和 executable_avg_ask 都明确传入时作为 cap/reference；不要让 Kelly 决定 signal。
- 每个 rejected signal 必须有 skip reason。
- 报告必须分开：
  - signal-only：根本策略方向是否正确
  - tradable-signal：经过 ask/depth/trade_edge 后的纸面交易结果

执行区自测：
- ask-depth fill 会逐档吃 ask，计算 executable_avg_ask。
- depth 不足时返回 rejected / skip reason。
- p_hat 缺失时不计算 trade_edge，也不估算 p_hat。
- marketability 可以拒绝一个 valid signal，但不能改变 signal。
- signal-only 和 tradable-signal 报告是分开的。
- 代码中不存在下单、签名、wallet、credential、live order path。
- Phase 1 signal 规则未被修改。

停止条件：
- 需要决定 p_hat 估计方法。
- 需要真实资金、wallet、私钥、credential 或交易权限。
- 需要添加实盘 order placement 或交易 SDK。
- 需要设计长期存储 schema。
- 需要新增未确认交易规则。
- 需要把 marketability 或 paper fill 逻辑写进 signal。

执行区证据报告模板：
任务ID：
polybot-paper-phase-3-marketability-paper-fill

改动文件：

范围边界：

运行命令：

结果：

fill simulation 证据：

skip reason 证据：

report separation 证据：

手工检查：

范围外未做：

阻塞/待规划决定：
```

## Phase 3 验收合同

```text
任务ID：
polybot-paper-phase-3-marketability-paper-fill

目标：
Marketability and paper fill exist, use ask-side depth for simulated fills, and keep signal-only results separate from tradable-signal results.

必须不做：
- 不下单
- 不接 wallet / signing / credentials
- 不实现或估算 p_hat 模型
- 不修改 Phase 1 signal 规则
- 不修改 Phase 2 WebSocket capture 主路径
- 不用 midpoint / last trade / best ask 代替整笔 ask-depth fill
- 不加入新交易规则

必测：
- ask-depth fill self-check 通过
- depth 不足会产生 skip reason
- p_hat 缺失不会被自动估算
- trade_edge 只用 caller-supplied p_hat 计算
- valid signal 可以被 marketability 拒绝，但 signal 本身不变
- signal-only 和 tradable-signal 报告分离
- 代码中无 live order / wallet / signing 路径

重点风险：
- 把 p_hat 猜测变成隐藏策略规则
- 用不真实成交价模拟收益
- marketability 反向污染 signal
- paper execution 偷偷变成 live execution

验收输入：验收合同 + issues.md 中当前任务ID对应的最新执行证据块 + 当前 diff
```

## 给验收区的 Phase 3 任务

```text
你现在是 PolyBot 的验收区。

目标：
只判断 Phase 3 是否通过，不改代码；重点检查 ask-depth fill、skip reason、p_hat 边界、signal/report 分离，以及无 live order path。

先读：
- AGENTS.md
- docs/project_notes/zone_operating_model.md
- 上面的 Phase 3 验收合同

如需确认策略边界，再读：
- docs/product_consensus/polymarket_paper_trader_v1.md

如需确认模块边界，再读：
- docs/architecture.md

如需确认当前 phase gate，再读：
- docs/implementation-plan.md

验收输入：
- Phase 3 验收合同
- `docs/project_notes/issues.md` 中 `polybot-paper-phase-3-marketability-paper-fill` 的最新执行证据块
- 当前 diff

重点检查：
- fill simulation 是否 walk ask-side depth
- 是否用 midpoint、last trade、best ask 冒充整笔成交均价
- p_hat 是否只作为 caller-supplied input
- 是否存在 p_hat 估计、训练、bucket、平滑或历史推断
- marketability 是否只消费 signal，不创建或修改 signal
- signal-only 与 tradable-signal 报告是否分离
- 是否存在 wallet、signing、credential、order placement、live order path

不要重复：
- 不要复述完整执行任务卡
- 不要重写执行区证据报告
- 不要无差别重跑所有命令；只重跑最高信号检查

输出：
- 先给通过 / 不通过
- 若不通过，列问题、证据、文件行号、最小返工任务
```

## Later Phases

## Phase 4 Summary

Intent:

- wire the existing modules into a short live paper simulation loop
- support one explicitly configured market/session
- produce JSONL records that later settlement/result phases can close

Locked decisions:

- no live trading
- no wallet/signing/credentials
- no market discovery or rotation yet
- no final `p_hat` model
- `p_hat` is CLI/config supplied only
- no settlement PnL yet

Not for `执行区` to decide:

- automatic 15-minute market discovery
- final `p_hat` estimation method
- long-term storage schema
- live trading path
- settlement source rules

If one of these is required, stop and route back to `规划区`.

## 给执行区的 Phase 4 任务

```text
你现在是 PolyBot 的执行区。请使用 goal 模式执行下面任务。

目标：
建立 Phase 4 single-market paper runner：把现有 Signal、Market Data、Marketability/Paper Fill 串成一个短时 live simulation loop。它只跑一个显式配置的市场/session，记录 signal、filled/skipped paper decision、runtime notes 到 JSONL，不做最终结算 PnL。

范围外：
- 不做实盘。
- 不下单。
- 不做 wallet、签名、credential、order placement。
- 不自动发现或轮换 15 分钟市场。
- 不实现或估算 p_hat 模型。
- 不做 settlement / final PnL。
- 不修改 Phase 1 signal 规则。
- 不修改 Phase 2 market capture 主路径。
- 不修改 Phase 3 ask-depth fill 规则。
- 不设计长期数据库 schema。

先读：
- AGENTS.md
- docs/project_notes/zone_operating_model.md
- docs/project_notes/key_facts.md
- docs/project_notes/issues.md 的 Current Summary 和 `polybot-paper-phase-3-marketability-paper-fill` 最新证据块
- polybot/signal.py
- polybot/market_data.py
- polybot/marketability.py
- polybot/paper.py

如需确认模块边界，再读：
- docs/architecture.md

如需确认 phase gate，再读：
- docs/implementation-plan.md

交付物：
- 一个 paper runner 模块，例如 `polybot/paper_runner.py`
- CLI/config 输入：Polymarket asset id、open price、market end time、stake、caller-supplied p_hat、运行秒数、输出 jsonl 路径
- 一个短时 demo/self-check 命令
- JSONL record 类型：runtime_note、signal_record、paper_trade_record、skipped_trade_record
- API/data 缺失时的明确 skip/runtime note

修改点：
- Runner 只负责 orchestration，不重写 signal、capture、marketability、paper fill 规则。
- Runner 必须调用现有 `generate_signal` / market data capture / `evaluate_marketability`。
- 如果没有 Polymarket orderbook 记录，写 runtime note 或 skipped record，不伪造成交。
- 如果没有 caller-supplied p_hat，沿用 Phase 3 行为记录 missing_p_hat，不估算 p_hat。
- 输出使用 JSONL；不要引入数据库。
- 每条记录包含 local timestamp；能带 source timestamp 的 market data 继续保留。

执行区自测：
- `python3 -m polybot.paper_runner --self-check` 或等价命令通过。
- 短时 demo 能生成 JSONL 文件，至少包含 runtime_note，并在有样例/捕获数据时包含 signal 或 skipped/filled paper decision。
- forbidden search 确认无 wallet、signing、credential、order placement、live order path。
- search/diff 确认 signal、market capture、marketability 核心规则未被重写。
- compile check 通过。

停止条件：
- 需要自动发现当前/下一个 15 分钟市场。
- 需要决定 final p_hat 模型。
- 需要结算源、winning side 或最终 PnL。
- 需要真实资金、wallet、私钥、credential 或交易权限。
- 需要长期数据库 schema。
- 需要新增未确认交易规则。
```

## Phase 4 执行区证据报告模板

`执行区` 完成后必须把这份证据写入 `docs/project_notes/issues.md` 的当前任务日志块，不要只停留在聊天回复里。

```text
任务ID：
polybot-paper-phase-4-single-market-runner

改动文件：

范围边界：

运行命令：

结果：

JSONL 输出样例：

手工检查：

范围外未做：

阻塞/待规划决定：
```

## Phase 4 验收合同

```text
任务ID：
polybot-paper-phase-4-single-market-runner

目标：
Single-market paper runner exists, wires existing modules without redefining strategy, and records paper simulation events to JSONL.

必须不做：
- 不下单
- 不接 wallet / signing / credentials
- 不自动发现或轮换市场
- 不估算 p_hat
- 不做 settlement / final PnL
- 不修改 signal、market capture、ask-depth fill 核心规则
- 不引入长期数据库 schema

必测：
- runner self-check 或短时 demo 通过
- JSONL 文件生成且包含 expected record type
- 缺少 orderbook 或 p_hat 时有明确 runtime note / skip reason
- 代码中无 live order / wallet / signing 路径
- 现有 Phase 1-3 self-check 仍通过

重点风险：
- Runner 偷偷变成策略层或交易层
- 自动发现市场导致执行区自行决定未规划规则
- 用伪造盘口生成 filled trade
- 把结算/PnL 提前混进 Phase 4

验收输入：验收合同 + issues.md 中当前任务ID对应的最新执行证据块 + 当前 diff
```

## 给验收区的 Phase 4 任务

```text
你现在是 PolyBot 的验收区。

目标：
只判断 Phase 4 是否通过，不改代码；重点检查 runner 是否只做单市场 orchestration，是否没有实盘、市场轮换、p_hat 估算、settlement/PnL 越界。

先读：
- AGENTS.md
- docs/project_notes/zone_operating_model.md
- 上面的 Phase 4 验收合同

验收输入：
- Phase 4 验收合同
- `docs/project_notes/issues.md` 中 `polybot-paper-phase-4-single-market-runner` 的最新执行证据块
- 当前 diff

重点检查：
- paper runner 是否调用现有模块而不是重写规则
- JSONL 输出是否存在并包含合理 record type
- 缺数据时是否记录 skip/runtime note，而不是伪造成交
- 是否存在 wallet、signing、credential、order placement、live order path
- 是否偷偷加入 market discovery、p_hat 模型、settlement 或 PnL

不要重复：
- 不要复述完整执行任务卡
- 不要重写执行区证据报告
- 不要无差别重跑所有命令；只重跑最高信号检查

输出：
- 先给通过 / 不通过
- 若不通过，列问题、证据、文件行号、最小返工任务
```

## Phase 5 Summary

Intent:

- close Phase 4 paper runner JSONL records after a market is complete
- calculate signal-only and tradable-signal outcomes from explicit winning side
- produce a small result summary without discovering or rotating markets

Locked decisions:

- no live trading
- no wallet/signing/credentials
- no market discovery or rotation
- no final `p_hat` model
- no long-term database
- winning side is explicit input or a verified resolution record

Not for `执行区` to decide:

- Polymarket market discovery path
- settlement source automation beyond explicit input / verified record parsing
- final `p_hat` estimation method
- unattended 15-minute rotation
- live trading path

If one of these is required, stop and route back to `规划区`.

## 给执行区的 Phase 5 任务

```text
你现在是 PolyBot 的执行区。请使用 goal 模式执行下面任务。

目标：
建立 Phase 5 settlement/result closer：读取 Phase 4 paper runner 生成的 JSONL，使用显式传入的 winning side（UP 或 DOWN）或一个已验证 resolution record，关闭该市场的纸面结果，输出 signal-only 和 tradable-signal 的结果摘要。

范围外：
- 不做实盘。
- 不下单。
- 不做 wallet、签名、credential、order placement。
- 不自动发现或轮换 15 分钟市场。
- 不实现或估算 p_hat 模型。
- 不训练、不平滑、不回填历史 p_hat。
- 不修改 Phase 1 signal 规则。
- 不修改 Phase 2 market capture 主路径。
- 不修改 Phase 3 ask-depth fill 规则。
- 不修改 Phase 4 runner orchestration。
- 不设计长期数据库 schema。

先读：
- AGENTS.md
- docs/project_notes/zone_operating_model.md
- docs/project_notes/key_facts.md
- docs/project_notes/issues.md 的 Current Summary 和 `polybot-paper-phase-4-single-market-runner` 最新证据块
- polybot/paper_runner.py
- polybot/paper.py

如需确认 phase gate，再读：
- docs/implementation-plan.md

如需确认模块边界，再读：
- docs/architecture.md

交付物：
- 一个 result closer 模块，例如 `polybot/result_closer.py`
- CLI/config 输入：runner JSONL 路径、winning side、输出 JSON/JSONL 路径
- 一个最小 self-check，使用样例 runner JSONL 覆盖 filled 与 skipped trade
- 输出摘要至少包含：
  - signal-only counts by signal side and winning side
  - filled trade count
  - skipped trade count by reason
  - paper PnL for filled trades
  - total paper PnL

修改点：
- Result closer 只消费 Phase 4 JSONL，不重新跑 signal、market capture、marketability 或 paper fill。
- Winning side 只能来自显式 CLI/config 输入或已验证 resolution record；本 phase 不自动抓 settlement。
- Filled paper trade PnL：
  - if trade signal == winning side: shares - stake
  - else: -stake
- Skipped trades 不计入 PnL，但要进入 skipped summary。
- NO_SIGNAL 不生成 paper PnL。
- 输出使用 JSON 或 JSONL；不要引入数据库。

执行区自测：
- `python3 -m polybot.result_closer --self-check` 或等价命令通过。
- self-check 覆盖：
  - winning filled trade
  - losing filled trade
  - skipped trade
  - signal-only summary
  - total paper PnL
- 现有 Phase 1-4 self-check 仍通过。
- forbidden search 确认无 wallet、signing、credential、order placement、live order path、market discovery、rotation、p_hat training。
- compile check 通过。

停止条件：
- 需要自动获取 Polymarket resolution 或发现当前/下一个市场。
- 需要决定 final p_hat 模型。
- 需要真实资金、wallet、私钥、credential 或交易权限。
- 需要长期数据库 schema。
- 需要新增未确认交易规则。

执行完成后：
把下面格式写入 `docs/project_notes/issues.md` 的当前任务日志块。

任务ID：
polybot-paper-phase-5-result-closer

改动文件：

范围边界：

运行命令：

结果：

result summary 样例：

手工检查：

范围外未做：

阻塞/待规划决定：
```

## Phase 5 验收合同

```text
任务ID：
polybot-paper-phase-5-result-closer

目标：
Result closer can score Phase 4 runner JSONL with explicit winning side while preserving phase boundaries.

必须不做：
- 不下单
- 不接 wallet / signing / credentials
- 不自动发现或轮换市场
- 不自动抓 settlement
- 不估算 p_hat
- 不修改 Phase 1-4 核心规则
- 不引入长期数据库 schema

必测：
- result closer self-check 通过
- filled win/loss PnL 计算正确
- skipped trades 不计入 PnL 但计入 skipped summary
- signal-only 与 tradable-signal/result summary 分离
- 代码中无 live order / wallet / signing / market discovery / rotation / p_hat training 路径
- 现有 Phase 1-4 self-check 仍通过

重点风险：
- 把 result closer 偷偷变成 settlement crawler
- 把 skipped trade 算进 PnL
- 把 p_hat 模型或历史回填混进 Phase 5
- 修改已验收的 signal/capture/fill/runner 规则

验收输入：验收合同 + issues.md 中当前任务ID对应的最新执行证据块 + 当前 diff
```

## Phase 6 Summary

Intent:

- resolve current and next BTC 15-minute markets from public market metadata
- validate token/outcome mapping before a runner can use it
- prepare session rotation inputs for Phase 4 runner without creating a long-running daemon yet

Locked decisions:

- no live trading
- no wallet/signing/credentials
- no order placement APIs
- no automatic settlement
- no final `p_hat` model
- no long-running unattended daemon yet
- skip ambiguous discovery instead of guessing

Not for `执行区` to decide:

- final `p_hat` estimation method
- automatic settlement source
- live trading path
- daemon supervision/restart policy
- new strategy rules

If one of these is required, stop and route back to `规划区`.

## 给执行区的 Phase 6 任务

```text
你现在是 PolyBot 的执行区。请使用 goal 模式执行下面任务。

任务ID：
polybot-paper-phase-6-market-discovery-rotation

目标：
建立 Phase 6 market discovery and session rotation planner：用公开市场元数据发现当前/下一个 BTC 15-minute Polymarket 市场，验证 UP/DOWN token/outcome mapping，并输出 Phase 4 runner 可以消费的 session config。只做发现和轮换计划，不启动长期无人值守 daemon。

范围外：
- 不做实盘。
- 不下单。
- 不做 wallet、签名、credential、order placement。
- 不自动抓 settlement 或关闭结果。
- 不实现或估算 p_hat 模型。
- 不训练、不平滑、不回填历史 p_hat。
- 不修改 Phase 1 signal 规则。
- 不修改 Phase 2 WebSocket capture 主路径。
- 不修改 Phase 3 ask-depth fill 规则。
- 不修改 Phase 4 runner orchestration，除非只增加读取 session config 的最小兼容入口。
- 不修改 Phase 5 result closer。
- 不做长期 daemon、进程监督、重启策略或持久数据库 schema。

先读：
- AGENTS.md
- docs/project_notes/zone_operating_model.md
- docs/project_notes/key_facts.md
- docs/project_notes/issues.md 的 Current Summary
- docs/project_notes/decisions.md 中 ADR-009
- polybot/paper_runner.py
- polybot/market_data.py

如需确认 phase gate，再读：
- docs/implementation-plan.md

如需确认策略或模块边界，再读：
- docs/product_consensus/polymarket_paper_trader_v1.md
- docs/architecture.md

如需确认 Polymarket API 形态，参考官方文档：
- https://docs.polymarket.com/market-data/overview
- https://docs.polymarket.com/market-data/fetching-markets

交付物：
- 一个 market/session discovery 模块，例如 `polybot/market_discovery.py`
- CLI/config 输入：
  - discovery query 或 tag/filter 参数
  - now timestamp
  - lookahead minutes
  - output path
  - optional paper stake
  - optional caller-supplied p_hat
- 输出一个 JSON session config，至少包含：
  - market/event id 或 slug
  - question/title
  - market start time
  - market end time
  - UP token id
  - DOWN token id
  - selected side labels
  - discovery source timestamp / local timestamp
  - skip reason when no safe selection exists
- 一个 rotation planner 函数或 CLI mode：
  - 输入当前 session config 和 candidate list
  - 输出 next session config 或 skip reason
- 一个最小 self-check，使用样例 metadata 覆盖：
  - exactly one valid current BTC 15m market
  - exactly one valid next BTC 15m market
  - ambiguous candidates -> skip
  - missing or unclear UP/DOWN token mapping -> skip

修改点：
- Public market metadata discovery can use REST because discovery is not the low-latency price/orderbook path.
- Price/orderbook capture remains WebSocket-first in the existing Phase 2 path.
- Auto-select only when exactly one candidate passes configured validation.
- Validation must check BTC/Bitcoin identity, 15-minute duration, active/open status, start/end time, and UP/DOWN token mapping.
- If live API response shape differs from docs or sample data, record the mismatch and stop instead of guessing.
- Session config is an input artifact for the runner; do not start an infinite loop in this phase.
- Prefer Python standard library and existing dependencies; do not add a dependency unless current code already needs it for existing network behavior.

执行区自测：
- `python3 -m polybot.market_discovery --self-check` 或等价命令通过。
- self-check 覆盖 current selection、next selection、ambiguous skip、mapping skip。
- 如果实现了 CLI demo，用样例 JSON 或 live public metadata 输出一份 session config。
- 现有 Phase 1-5 self-check 仍通过。
- forbidden search 确认无 wallet、signing、credential、order placement、live order path、settlement crawler、p_hat training、daemon supervisor。
- compile check 通过。

停止条件：
- 需要真实资金、wallet、私钥、credential 或交易权限。
- 需要自动 settlement 或 resolution source。
- 需要决定 final p_hat 模型。
- 需要长期数据库 schema。
- 需要 daemon 进程管理或重启策略。
- 需要新增未确认交易规则。
- 公开市场数据无法明确识别 BTC 15m UP/DOWN token mapping。

执行完成后：
把下面格式写入 `docs/project_notes/issues.md` 的当前任务日志块。

任务ID：
polybot-paper-phase-6-market-discovery-rotation

改动文件：

范围边界：

运行命令：

结果：

session config 样例：

skip reason 样例：

手工检查：

范围外未做：

阻塞/待规划决定：
```

## Phase 6 验收合同

```text
任务ID：
polybot-paper-phase-6-market-discovery-rotation

目标：
Discovery/rotation planner can resolve safe current/next BTC 15-minute session configs for the existing paper runner without adding live trading or daemon behavior.

必须不做：
- 不下单
- 不接 wallet / signing / credentials
- 不自动抓 settlement
- 不估算 p_hat
- 不启动长期 daemon
- 不修改 Phase 1-5 核心规则
- 不引入长期数据库 schema

必测：
- market discovery self-check 通过
- current market selection 正确
- next market selection 正确
- ambiguous candidates 会 skip 而不是猜
- missing/unclear UP/DOWN mapping 会 skip
- 输出 session config 包含 runner 需要的 market id/slug、start/end time、UP/DOWN token ids
- 代码中无 live order / wallet / signing / settlement crawler / p_hat training / daemon supervisor 路径
- 现有 Phase 1-5 self-check 仍通过

重点风险：
- 用低频轮询替代 WebSocket 价格/盘口主路径
- market discovery 猜错 BTC 15m 市场或 token mapping
- 把 Phase 6 偷偷变成长期 daemon
- 把 settlement、p_hat 或实盘路径混进发现/轮换
- 修改已验收的 signal/capture/fill/runner/result closer 规则

验收输入：验收合同 + issues.md 中当前任务ID对应的最新执行证据块 + 当前 diff
```

## 给验收区的 Phase 6 任务

```text
你现在是 PolyBot 的验收区。

目标：
只判断 Phase 6 是否通过，不改代码；重点检查 discovery/rotation planner 是否能安全生成当前/下一个 BTC 15m session config，并且没有越界进入实盘、settlement、p_hat 或 daemon。

先读：
- AGENTS.md
- docs/project_notes/zone_operating_model.md
- docs/project_notes/issues.md 的 Current Summary
- docs/project_notes/decisions.md 中 ADR-009
- 上面的 Phase 6 验收合同

验收输入：
- Phase 6 验收合同
- `docs/project_notes/issues.md` 中 `polybot-paper-phase-6-market-discovery-rotation` 的最新执行证据块
- 当前 diff

重点检查：
- 是否只使用公开市场元数据做发现，不碰 wallet/signing/order API。
- 是否保持 Phase 2 价格/盘口捕获 WebSocket-first，没有改成低频轮询。
- 是否只在 exactly one candidate 通过验证时 auto-select。
- ambiguous candidates 和 unclear UP/DOWN mapping 是否有明确 skip reason。
- session config 是否足够 Phase 4 runner 使用，但没有启动长期 daemon。
- 是否没有引入 settlement crawler、p_hat model/training、长期 DB schema。
- Phase 1-5 self-check 是否仍通过。

不要重复：
- 不要复述完整执行任务卡。
- 不要重写执行区证据报告。
- 不要做实现或补测试。
- 不要把 Phase 7 daemon hardening 提前要求进 Phase 6。

输出：
- 先给通过 / 不通过。
- 若不通过，列问题、证据、文件行号、最小返工任务。
- 若通过，简短说明验收依据，并列出仍属于后续 Phase 的残余风险。
```

## Phase 7 Summary

Intent:

- let the paper runner consume Phase 6 session config
- choose UP/DOWN token id from the root signal direction, not manually
- keep one session per run before adding a continuous supervisor

Locked decisions:

- no live trading
- no wallet/signing/credentials
- no automatic settlement
- no final `p_hat` model
- no automatic open-price capture in this phase
- no long-running daemon yet
- one configured/discovered session only

Not for `执行区` to decide:

- automatic open-price source/capture policy
- automatic settlement source
- final `p_hat` estimation method
- daemon supervision/restart policy
- new strategy rules

If one of these is required, stop and route back to `规划区`.

## 给执行区的 Phase 7 任务

```text
你现在是 PolyBot 的执行区。请使用 goal 模式执行下面任务。

任务ID：
polybot-paper-phase-7-session-config-runner

目标：
建立 Phase 7 session-config runner wiring：让 paper runner 能消费 Phase 6 生成的 session config JSON，并在根本策略信号产生 UP 或 DOWN 后，自动选择对应的 up_token_id 或 down_token_id 进行单 session 模拟交易记录。

范围外：
- 不做实盘。
- 不下单。
- 不做 wallet、签名、credential、order placement。
- 不自动抓 settlement 或关闭结果。
- 不实现或估算 p_hat 模型。
- 不训练、不平滑、不回填历史 p_hat。
- 不自动捕获 open price；本 phase 仍使用显式 open price 输入。
- 不做长期 daemon、进程监督、重启策略或持久数据库 schema。
- 不修改 Phase 1 signal 规则。
- 不修改 Phase 2 WebSocket capture 主路径。
- 不修改 Phase 3 ask-depth fill 规则。
- 不修改 Phase 5 result closer。
- 不修改 Phase 6 discovery selection/validation 规则。

先读：
- AGENTS.md
- docs/project_notes/zone_operating_model.md
- docs/project_notes/key_facts.md
- docs/project_notes/issues.md 的 Current Summary
- docs/project_notes/decisions.md 中 ADR-011
- polybot/paper_runner.py
- polybot/market_discovery.py

如需确认 phase gate，再读：
- docs/implementation-plan.md

如需确认策略或模块边界，再读：
- docs/product_consensus/polymarket_paper_trader_v1.md
- docs/architecture.md

交付物：
- 一个最小 runner wiring 入口，可以是：
  - 在 `polybot/paper_runner.py` 增加 `--session-config` CLI 输入；或
  - 新增很小的 `polybot/session_runner.py`
- 该入口接受：
  - Phase 6 session config JSON path
  - explicit open price
  - seconds
  - output JSONL path
  - optional caller-supplied p_hat
  - optional stake override；默认优先使用 session config 的 paper_stake
- JSONL 输出必须记录：
  - session market_id / event_id / slug
  - signal side
  - selected token id
  - selected side label
  - paper_trade_record 或 skipped_trade_record
  - skip/runtime note when no token is selected
- 一个最小 self-check，使用 Phase 6 sample session config 和本地 sample market/BTC records 覆盖 UP、DOWN、NO_SIGNAL。

修改点：
- Signal 仍然只由 open price、current BTC price、market end time、now、threshold 决定。
- 如果 signal 是 UP，选择 session config 的 up_token_id。
- 如果 signal 是 DOWN，选择 session config 的 down_token_id。
- 如果 signal 是 NO_SIGNAL，不选择 token，不模拟 fill，记录 NO_SIGNAL/runtime note。
- 如果 session config 缺少对应 token id，记录 skip/runtime note，不猜 token。
- Marketability/paper fill 仍使用真实 ask-side depth 逻辑或已有 sample book；不要用 midpoint、last trade 或 best ask shortcut。
- Runner JSONL 必须保留 Phase 4/5 可消费的记录形状；如需新增字段，只能追加 session/selected-token metadata，不破坏旧字段。
- 优先复用 `paper_runner.py`、`market_discovery.py`、`paper.py` 现有函数；不要新增服务层或长期调度抽象。

执行区自测：
- `python3 -m polybot.paper_runner --self-check` 仍通过。
- 新的 session-config runner self-check 通过。
- self-check 覆盖：
  - UP signal selects up_token_id
  - DOWN signal selects down_token_id
  - NO_SIGNAL selects no token and creates no paper fill
  - missing token mapping records skip/runtime note
- 现有 Phase 1-6 self-check 仍通过。
- forbidden search 确认无 wallet、signing、credential、order placement、live order path、settlement crawler、p_hat training、daemon supervisor。
- compile check 通过。

停止条件：
- 需要自动获取 open price。
- 需要自动 settlement 或 resolution source。
- 需要决定 final p_hat 模型。
- 需要真实资金、wallet、私钥、credential 或交易权限。
- 需要长期数据库 schema。
- 需要 daemon 进程管理或重启策略。
- 需要新增未确认交易规则。

执行完成后：
把下面格式写入 `docs/project_notes/issues.md` 的当前任务日志块。

任务ID：
polybot-paper-phase-7-session-config-runner

改动文件：

范围边界：

运行命令：

结果：

session runner JSONL 样例：

手工检查：

范围外未做：

阻塞/待规划决定：
```

## Phase 7 验收合同

```text
任务ID：
polybot-paper-phase-7-session-config-runner

目标：
Runner can consume Phase 6 session config and choose UP/DOWN token ids from the root signal direction for one paper session.

必须不做：
- 不下单
- 不接 wallet / signing / credentials
- 不自动抓 settlement
- 不估算 p_hat
- 不自动捕获 open price
- 不启动长期 daemon
- 不修改 Phase 1-6 核心规则
- 不引入长期数据库 schema

必测：
- session-config runner self-check 通过
- UP signal selects up_token_id
- DOWN signal selects down_token_id
- NO_SIGNAL selects no token and creates no fill
- missing token mapping records skip/runtime note instead of guessing
- JSONL records include session identifiers and selected token metadata without breaking Phase 4/5 record consumers
- 代码中无 live order / wallet / signing / settlement crawler / p_hat training / daemon supervisor 路径
- 现有 Phase 1-6 self-check 仍通过

重点风险：
- 在 signal 之前手动固定某个 token，导致方向和 token 可能不一致
- 把 automatic open-price capture 偷偷混进 Phase 7
- 把 Phase 7 偷偷变成长期 daemon
- 修改已验收的 signal/capture/fill/result closer/discovery 规则

验收输入：验收合同 + issues.md 中当前任务ID对应的最新执行证据块 + 当前 diff
```

## 给验收区的 Phase 7 任务

```text
你现在是 PolyBot 的验收区。

目标：
只判断 Phase 7 是否通过，不改代码；重点检查 runner 是否能从 session config 正确选择 UP/DOWN token，并且没有越界进入 open-price automation、settlement、p_hat、实盘或 daemon。

先读：
- AGENTS.md
- docs/project_notes/zone_operating_model.md
- docs/project_notes/issues.md 的 Current Summary
- docs/project_notes/decisions.md 中 ADR-011
- 上面的 Phase 7 验收合同

验收输入：
- Phase 7 验收合同
- `docs/project_notes/issues.md` 中 `polybot-paper-phase-7-session-config-runner` 的最新执行证据块
- 当前 diff

重点检查：
- Signal 方向是否决定 selected token id，而不是提前固定 token。
- UP/DOWN/NO_SIGNAL/missing token mapping 是否都有 self-check 覆盖。
- JSONL 是否包含 session identifiers 和 selected token metadata。
- Phase 4/5 record consumer 是否没有被破坏。
- 是否没有自动 open-price capture、settlement crawler、p_hat model/training、长期 DB、daemon supervisor。
- Phase 1-6 self-check 是否仍通过。

不要重复：
- 不要复述完整执行任务卡。
- 不要重写执行区证据报告。
- 不要做实现或补测试。
- 不要把 Phase 8 bounded supervisor 提前要求进 Phase 7。

输出：
- 先给通过 / 不通过。
- 若不通过，列问题、证据、文件行号、最小返工任务。
- 若通过，简短说明验收依据，并列出仍属于后续 Phase 的残余风险。
```

## Phase 8 Summary

Intent:

- derive the session open reference price without manual input
- keep the root signal unchanged: it still compares current BTC price to open price
- prepare for later bounded continuous supervision without implementing it yet

Locked decisions:

- no live trading
- no wallet/signing/credentials
- no automatic settlement
- no final `p_hat` model
- no long-running daemon yet
- one configured/discovered session only
- use the existing BTC reference WebSocket source
- open price is the first valid BTC reference trade at or after market start within a configured max delay

Not for `执行区` to decide:

- a different BTC reference source
- candle aggregation or exchange-candle alignment
- automatic settlement source
- final `p_hat` estimation method
- daemon supervision/restart policy
- new strategy rules

If one of these is required, stop and route back to `规划区`.

## 给执行区的 Phase 8 任务

```text
你现在是 PolyBot 的执行区。请使用 goal 模式执行下面任务。

任务ID：
polybot-paper-phase-8-open-price-capture

目标：
建立 Phase 8 automatic open-price capture：对一个 Phase 6/7 session config，在 market_start_time 附近使用现有 BTC reference WebSocket records 捕获 open_price，并把 session config enrich 成可供 Phase 7 runner 直接使用的配置。仍然只处理一个 session，不做连续 daemon。

范围外：
- 不做实盘。
- 不下单。
- 不做 wallet、签名、credential、order placement。
- 不自动抓 settlement 或关闭结果。
- 不实现或估算 p_hat 模型。
- 不训练、不平滑、不回填历史 p_hat。
- 不新增 BTC reference source，不做 candle aggregation。
- 不做长期 daemon、进程监督、重启策略或持久数据库 schema。
- 不修改 Phase 1 signal 规则。
- 不修改 Phase 2 WebSocket capture 主路径。
- 不修改 Phase 3 ask-depth fill 规则。
- 不修改 Phase 5 result closer。
- 不修改 Phase 6 discovery selection/validation 规则。
- 不修改 Phase 7 token selection 规则。

先读：
- AGENTS.md
- docs/project_notes/zone_operating_model.md
- docs/project_notes/key_facts.md
- docs/project_notes/issues.md 的 Current Summary
- docs/project_notes/decisions.md 中 ADR-012
- polybot/market_data.py
- polybot/paper_runner.py
- polybot/market_discovery.py

如需确认 phase gate，再读：
- docs/implementation-plan.md

如需确认策略或模块边界，再读：
- docs/product_consensus/polymarket_paper_trader_v1.md
- docs/architecture.md

交付物：
- 一个最小 open-price capture/enrichment 入口，可以是：
  - 新增 `polybot/open_price.py`；或
  - 在现有 runner/discovery 附近增加少量函数，保持边界清楚
- CLI/config 输入：
  - session config JSON path
  - output enriched session config path
  - max open-price delay seconds
  - optional sample/input records path for self-check/demo
- 输出 enriched session config，至少追加：
  - open_price
  - open_price_timestamp
  - open_price_source
  - open_price_max_delay_seconds
  - open_price_capture_status 或 skip_reason
- Phase 7 runner 兼容：
  - 如果 `--open-price` 未传入，但 session config 有 valid `open_price`，runner 可以使用 config open_price
  - 如果两者都存在，CLI `--open-price` 优先，并记录/保留现有行为
- 一个最小 self-check，使用本地 sample BTC reference records 覆盖 valid、pre-start-only、stale/missing。

修改点：
- Use existing `CaptureRecord` shape from `polybot.market_data`.
- Open price selection rule:
  - ignore records before `market_start_time`
  - choose the first record at or after `market_start_time`
  - require positive numeric price
  - require source timestamp or local receive timestamp to be within `max_open_price_delay_seconds`
  - otherwise return skip reason, do not guess
- Do not change root signal thresholds, entry times, or direction logic.
- Do not make low-frequency polling the market-data path.
- Do not start an infinite loop; this phase enriches or runs one session only.
- Prefer Python standard library and existing dependencies; do not add new dependencies.

执行区自测：
- `python3 -m polybot.open_price --self-check` 或等价命令通过。
- `python3 -m polybot.paper_runner --session-self-check` 仍通过。
- 新增 runner-with-config-open-price check 通过：不传 `--open-price` 时能使用 enriched config 的 `open_price`。
- self-check 覆盖：
  - first valid post-start record becomes open_price
  - pre-start-only records produce skip reason
  - stale/missing records produce skip reason
  - non-positive or non-numeric price is rejected
- 现有 Phase 1-7 self-check 仍通过。
- forbidden search 确认无 wallet、signing、credential、order placement、live order path、settlement crawler、p_hat training、daemon supervisor。
- compile check 通过。

停止条件：
- 需要选择新的 BTC reference source。
- 需要 candle aggregation 或外部 candle alignment。
- 需要自动 settlement 或 resolution source。
- 需要决定 final p_hat 模型。
- 需要真实资金、wallet、私钥、credential 或交易权限。
- 需要长期数据库 schema。
- 需要 daemon 进程管理或重启策略。
- 需要新增未确认交易规则。

执行完成后：
把下面格式写入 `docs/project_notes/issues.md` 的当前任务日志块。

任务ID：
polybot-paper-phase-8-open-price-capture

改动文件：

范围边界：

运行命令：

结果：

enriched session config 样例：

skip reason 样例：

手工检查：

范围外未做：

阻塞/待规划决定：
```

## Phase 8 验收合同

```text
任务ID：
polybot-paper-phase-8-open-price-capture

目标：
One session config can be enriched with a deterministic BTC reference open_price and then drive the existing session runner without manual open-price input.

必须不做：
- 不下单
- 不接 wallet / signing / credentials
- 不自动抓 settlement
- 不估算 p_hat
- 不新增 BTC reference source
- 不做 candle aggregation
- 不启动长期 daemon
- 不修改 Phase 1-7 核心规则
- 不引入长期数据库 schema

必测：
- open-price self-check 通过
- first valid post-start record becomes open_price
- pre-start-only records produce skip reason
- stale/missing records produce skip reason
- invalid non-positive/non-numeric price is rejected
- enriched config can run Phase 7 session runner without CLI `--open-price`
- 代码中无 live order / wallet / signing / settlement crawler / p_hat training / daemon supervisor 路径
- 现有 Phase 1-7 self-check 仍通过

重点风险：
- 用开盘前价格当 open_price
- stale/missing 数据时猜 open_price
- 偷偷换 BTC reference source 或引入 candle aggregation
- 把 Phase 8 偷偷变成长期 daemon
- 修改已验收的 signal/capture/fill/result closer/discovery/token selection 规则

验收输入：验收合同 + issues.md 中当前任务ID对应的最新执行证据块 + 当前 diff
```

## 给验收区的 Phase 8 任务

```text
你现在是 PolyBot 的验收区。

目标：
只判断 Phase 8 是否通过，不改代码；重点检查 open-price capture 是否按 ADR-012 从现有 BTC reference records 得到确定 open_price，并且没有越界进入新数据源、candle aggregation、settlement、p_hat、实盘或 daemon。

先读：
- AGENTS.md
- docs/project_notes/zone_operating_model.md
- docs/project_notes/issues.md 的 Current Summary
- docs/project_notes/decisions.md 中 ADR-012
- 上面的 Phase 8 验收合同

验收输入：
- Phase 8 验收合同
- `docs/project_notes/issues.md` 中 `polybot-paper-phase-8-open-price-capture` 的最新执行证据块
- 当前 diff

重点检查：
- 是否忽略 market_start_time 之前的 BTC reference records。
- 是否选择 market_start_time 之后 max delay 内第一条有效正数价格。
- stale/missing/invalid price 是否 skip 而不是猜。
- runner 是否能用 enriched config 的 open_price 运行，且 CLI open_price 仍可覆盖。
- 是否没有新增 BTC source、candle aggregation、settlement crawler、p_hat model/training、长期 DB、daemon supervisor。
- Phase 1-7 self-check 是否仍通过。

不要重复：
- 不要复述完整执行任务卡。
- 不要重写执行区证据报告。
- 不要做实现或补测试。
- 不要把 Phase 9 bounded supervisor 提前要求进 Phase 8。

输出：
- 先给通过 / 不通过。
- 若不通过，列问题、证据、文件行号、最小返工任务。
- 若通过，简短说明验收依据，并列出仍属于后续 Phase 的残余风险。
```

## Phase 9 Summary

Intent:

- run more than one 15-minute paper session without manual market id, token id, or open price input
- prove the orchestration chain before building any long-running daemon
- keep all trading paper-only and bounded by explicit run limits

Locked decisions:

- no live trading
- no wallet/signing/credentials
- no automatic settlement
- no final `p_hat` model
- no unbounded daemon
- no process supervisor or restart policy
- no long-run database schema
- use existing discovery, open-price enrichment, session runner, and rotation behavior

Not for `执行区` to decide:

- automatic settlement source
- final `p_hat` estimation method
- daemon supervision/restart policy
- long-run storage schema
- new strategy rules

If one of these is required, stop and route back to `规划区`.

## 给执行区的 Phase 9 任务

```text
你现在是 PolyBot 的执行区。请使用 goal 模式执行下面任务。

任务ID：
polybot-paper-phase-9-bounded-supervisor

目标：
建立 Phase 9 bounded continuous supervisor：把已有的 market discovery、open-price enrichment、session-config runner、rotation planning 串起来，在明确边界内连续处理多个 BTC 15m paper sessions。它必须在 max sessions、max runtime 或 end time 达到时退出；不要做长期 daemon。

范围外：
- 不做实盘。
- 不下单。
- 不做 wallet、签名、credential、order placement。
- 不自动抓 settlement 或关闭结果。
- 不实现或估算 p_hat 模型。
- 不训练、不平滑、不回填历史 p_hat。
- 不新增 BTC reference source，不做 candle aggregation。
- 不做无边界 daemon。
- 不做进程监督、重启策略、后台服务、crontab/launchd/systemd 配置。
- 不设计长期数据库 schema。
- 不修改 Phase 1 signal 规则。
- 不修改 Phase 2 WebSocket capture 主路径。
- 不修改 Phase 3 ask-depth fill 规则。
- 不修改 Phase 5 result closer。
- 不修改 Phase 6 discovery selection/validation 规则。
- 不修改 Phase 7 token selection 规则。
- 不修改 Phase 8 open-price selection 规则。

先读：
- AGENTS.md
- docs/project_notes/zone_operating_model.md
- docs/project_notes/key_facts.md
- docs/project_notes/issues.md 的 Current Summary
- docs/project_notes/decisions.md 中 ADR-013
- polybot/market_discovery.py
- polybot/open_price.py
- polybot/paper_runner.py

如需确认 phase gate，再读：
- docs/implementation-plan.md

如需确认策略或模块边界，再读：
- docs/product_consensus/polymarket_paper_trader_v1.md
- docs/architecture.md

交付物：
- 一个最小 bounded supervisor 入口，例如 `polybot/supervisor.py`
- CLI/config 输入：
  - market discovery input/source 或 sample fixtures
  - max sessions
  - max runtime seconds 或 end time
  - lookahead minutes
  - max open-price delay seconds
  - output directory 或 supervisor JSONL path
  - paper stake
  - optional caller-supplied p_hat
  - per-session runner seconds
- supervisor JSONL 输出，至少包含：
  - supervisor_started
  - session_discovered / session_skipped
  - open_price_captured / open_price_skipped
  - session_runner_started / session_runner_finished / session_runner_skipped
  - rotation_planned
  - supervisor_stopped
  - stop_reason
- 每个 session 的 runner JSONL 输出路径必须可追踪。
- 一个最小 self-check，用本地 fixture 跑两个 sample sessions。

修改点：
- Supervisor 只能 orchestrate 现有模块，不重写 signal、discovery、open-price、marketability、paper fill 或 token selection 规则。
- Stop conditions:
  - reached_max_sessions
  - reached_max_runtime
  - reached_end_time
  - no_next_session
  - unrecoverable_error
- Recoverable skip examples:
  - no_valid_candidate
  - ambiguous_candidates
  - open_price skip reason
  - missing book / missing p_hat from runner
- Recoverable skip should be recorded and, when bounds allow, supervisor may continue to the next planned session.
- Use JSONL files only; do not introduce database schema.
- Use existing dependencies; do not add process-management libraries.
- Live/public API demo is optional; self-check must be local and deterministic.

执行区自测：
- `python3 -m polybot.supervisor --self-check` 或等价命令通过。
- self-check 覆盖：
  - two sessions are processed from local fixtures
  - one recoverable skip is recorded and does not crash the supervisor
  - max sessions stop condition works
  - session runner output path is recorded
  - supervisor JSONL has start/stop records
- 现有 Phase 1-8 self-check 仍通过。
- forbidden search 确认无 wallet、signing、credential、order placement、live order path、settlement crawler、p_hat training、daemon supervisor、restart policy、launchd/systemd/crontab。
- compile check 通过。

停止条件：
- 需要自动 settlement 或 resolution source。
- 需要决定 final p_hat 模型。
- 需要真实资金、wallet、私钥、credential 或交易权限。
- 需要长期数据库 schema。
- 需要无边界 daemon、进程管理或重启策略。
- 需要新增未确认交易规则。
- 需要修改已验收的核心 phase 规则才能继续。

执行完成后：
把下面格式写入 `docs/project_notes/issues.md` 的当前任务日志块。

任务ID：
polybot-paper-phase-9-bounded-supervisor

改动文件：

范围边界：

运行命令：

结果：

supervisor JSONL 样例：

session runner 输出样例：

手工检查：

范围外未做：

阻塞/待规划决定：
```

## Phase 9 验收合同

```text
任务ID：
polybot-paper-phase-9-bounded-supervisor

目标：
A bounded supervisor can process multiple paper sessions using existing discovery, open-price enrichment, session runner, and rotation logic, then stop at explicit bounds.

必须不做：
- 不下单
- 不接 wallet / signing / credentials
- 不自动抓 settlement
- 不估算 p_hat
- 不新增 BTC reference source
- 不做 candle aggregation
- 不启动无边界 daemon
- 不做进程监督 / 重启策略 / launchd / systemd / crontab
- 不修改 Phase 1-8 核心规则
- 不引入长期数据库 schema

必测：
- bounded supervisor self-check 通过
- two sample sessions are processed
- recoverable skip is recorded and does not crash the supervisor
- max sessions or max runtime/end time stop condition works
- supervisor JSONL includes start, per-session step records, and stop_reason
- each session runner JSONL path is recorded
- 代码中无 live order / wallet / signing / settlement crawler / p_hat training / daemon supervisor / restart policy 路径
- 现有 Phase 1-8 self-check 仍通过

重点风险：
- 把 bounded supervisor 偷偷做成无边界 daemon
- 在 supervisor 里重写 signal/discovery/open-price/token selection 规则
- skip/failure 后静默丢失记录
- 把 settlement、p_hat、长期 DB 或进程守护混进 Phase 9

验收输入：验收合同 + issues.md 中当前任务ID对应的最新执行证据块 + 当前 diff
```

## 给验收区的 Phase 9 任务

```text
你现在是 PolyBot 的验收区。

目标：
只判断 Phase 9 是否通过，不改代码；重点检查 bounded supervisor 是否只编排现有模块、能连续处理多个 paper sessions，并且会在明确边界停止。

先读：
- AGENTS.md
- docs/project_notes/zone_operating_model.md
- docs/project_notes/issues.md 的 Current Summary
- docs/project_notes/decisions.md 中 ADR-013
- 上面的 Phase 9 验收合同

验收输入：
- Phase 9 验收合同
- `docs/project_notes/issues.md` 中 `polybot-paper-phase-9-bounded-supervisor` 的最新执行证据块
- 当前 diff

重点检查：
- 是否只 orchestrate existing discovery / open-price / runner / rotation，不重写核心规则。
- 是否能处理至少两个 sample sessions。
- recoverable skip 是否有 JSONL 记录，且不会让 supervisor 崩溃。
- max sessions / max runtime / end time 是否能停止。
- 每个 session runner output path 是否可追踪。
- 是否没有 settlement crawler、p_hat model/training、长期 DB、无边界 daemon、restart policy、launchd/systemd/crontab。
- Phase 1-8 self-check 是否仍通过。

不要重复：
- 不要复述完整执行任务卡。
- 不要重写执行区证据报告。
- 不要做实现或补测试。
- 不要把 Phase 10 settlement 或 daemon hardening 提前要求进 Phase 9。

输出：
- 先给通过 / 不通过。
- 若不通过，列问题、证据、文件行号、最小返工任务。
- 若通过，简短说明验收依据，并列出仍属于后续 Phase 的残余风险。
```

## Phase 10 Summary

Intent:

- close the per-session runner JSONL files produced by Phase 9
- produce per-session and aggregate paper PnL summaries
- keep resolution input explicit so execution does not invent settlement rules

Locked decisions:

- no live trading
- no wallet/signing/credentials
- no automatic settlement crawler
- no final `p_hat` model
- no database schema
- no daemon behavior
- use existing result closer logic where possible

Not for `执行区` to decide:

- automatic Polymarket resolution source
- final `p_hat` estimation method
- long-run storage schema
- daemon supervision/restart policy
- new strategy rules

If one of these is required, stop and route back to `规划区`.

## 给执行区的 Phase 10 任务

```text
你现在是 PolyBot 的执行区。请使用 goal 模式执行下面任务。

任务ID：
polybot-paper-phase-10-supervisor-result-batch-close

目标：
建立 Phase 10 supervisor result batch closer：读取 Phase 9 supervisor JSONL，找到每个 session 的 runner JSONL 输出，用显式 resolution map 关闭结果，并写出 per-session summary 与 aggregate paper PnL summary。

范围外：
- 不做实盘。
- 不下单。
- 不做 wallet、签名、credential、order placement。
- 不自动抓 settlement，不爬 Polymarket resolution。
- 不猜 winning side。
- 不实现或估算 p_hat 模型。
- 不训练、不平滑、不回填历史 p_hat。
- 不设计长期数据库 schema。
- 不做无边界 daemon、进程监督、重启策略、crontab/launchd/systemd。
- 不修改 Phase 1 signal 规则。
- 不修改 Phase 3 marketability / paper fill 规则。
- 不修改 Phase 5 单 runner result closer 的既有语义，除非是为了复用而做最小兼容。
- 不修改 Phase 9 supervisor orchestration 规则，除非是为了补充已存在 runner output metadata 的最小兼容。

先读：
- AGENTS.md
- docs/project_notes/zone_operating_model.md
- docs/project_notes/key_facts.md
- docs/project_notes/issues.md 的 Current Summary
- docs/project_notes/decisions.md 中 ADR-014
- polybot/result_closer.py
- polybot/supervisor.py

如需确认 phase gate，再读：
- docs/implementation-plan.md

如需确认策略或模块边界，再读：
- docs/product_consensus/polymarket_paper_trader_v1.md
- docs/architecture.md

交付物：
- 一个最小 batch closer 入口，例如 `polybot/supervisor_results.py`。
- CLI/config 输入：
  - supervisor JSONL path
  - explicit resolution map JSON path
  - output summary path
- resolution map 支持按 market_id 或 runner_output path 指定 winning side。
- 输出 summary 至少包含：
  - sessions_seen
  - sessions_closed
  - sessions_skipped
  - skipped reasons
  - per-session result summaries
  - aggregate tradable paper PnL
  - aggregate signal-only counts

修改点：
- 复用 `polybot.result_closer.close_results` / `load_jsonl`，不要复制一套 PnL 规则。
- 从 supervisor JSONL 中读取 `session_runner_finished` 记录来定位 runner output。
- 缺少 runner output、runner file 不存在、缺少 resolution、winning side 非 UP/DOWN 时，记录 skipped session；不要猜。
- skipped session 不计入 PnL。
- 保持 JSON/JSONL 文件输出即可；不要引入数据库。
- self-check 使用本地 fixture，不需要联网。

执行区自测：
- `python3 -m polybot.supervisor_results --self-check` 或等价命令通过。
- self-check 覆盖：
  - two runner outputs from one sample supervisor JSONL
  - one closed UP/DOWN result
  - one missing resolution skipped
  - aggregate PnL equals closed sessions only
  - signal-only and tradable-signal views remain separate
- 现有 Phase 1-9 self-check 仍通过。
- forbidden search 确认无 wallet、signing、credential、order placement、live order path、settlement crawler、p_hat training、database schema、daemon、restart policy、launchd/systemd/crontab。
- compile check 通过。

停止条件：
- 需要自动 settlement 或 resolution source。
- 需要决定 final p_hat 模型。
- 需要真实资金、wallet、私钥、credential 或交易权限。
- 需要长期数据库 schema。
- 需要无边界 daemon、进程管理或重启策略。
- 需要新增未确认交易规则。
- 需要修改已验收的核心 phase 规则才能继续。

执行完成后：
把下面格式写入 `docs/project_notes/issues.md` 的当前任务日志块。

任务ID：
polybot-paper-phase-10-supervisor-result-batch-close

改动文件：

范围边界：

运行命令：

结果：

batch summary 样例：

手工检查：

范围外未做：

阻塞/待规划决定：
```

## Phase 10 验收合同

```text
任务ID：
polybot-paper-phase-10-supervisor-result-batch-close

目标：
Phase 10 can score a bounded supervisor run by closing per-session runner JSONL outputs with explicit resolution input, producing per-session and aggregate paper results.

必须不做：
- 不下单
- 不接 wallet / signing / credentials
- 不自动抓 settlement 或猜 winning side
- 不估算 p_hat
- 不引入长期数据库 schema
- 不启动无边界 daemon
- 不做进程监督 / 重启策略 / launchd / systemd / crontab
- 不修改 Phase 1、3、5、9 核心语义

必测：
- batch closer self-check 通过
- sample supervisor JSONL includes two runner outputs
- one session can be closed from explicit resolution
- one missing resolution is skipped and does not affect PnL
- output includes per-session summaries and aggregate paper PnL
- signal-only and tradable-signal views remain separate
- 代码中无 live order / wallet / signing / settlement crawler / p_hat training / DB schema / daemon supervisor / restart policy 路径
- 现有 Phase 1-9 self-check 仍通过

重点风险：
- 自动猜 settlement 或 winning side
- 复制并分叉 Phase 5 PnL 规则
- 把 skipped session 误计入收益
- 把长期 storage、p_hat 或 daemon hardening 混进 Phase 10

验收输入：验收合同 + issues.md 中当前任务ID对应的最新执行证据块 + 当前 diff
```

## 给验收区的 Phase 10 任务

```text
你现在是 PolyBot 的验收区。

目标：
只判断 Phase 10 是否通过，不改代码；重点检查 batch closer 是否只用显式 resolution 关闭 supervisor runner outputs，并正确汇总纸面结果。

先读：
- AGENTS.md
- docs/project_notes/zone_operating_model.md
- docs/project_notes/issues.md 的 Current Summary
- docs/project_notes/decisions.md 中 ADR-014
- 上面的 Phase 10 验收合同

验收输入：
- Phase 10 验收合同
- `docs/project_notes/issues.md` 中 `polybot-paper-phase-10-supervisor-result-batch-close` 的最新执行证据块
- 当前 diff

重点检查：
- 是否从 supervisor JSONL 的 finished runner records 定位 runner output。
- 是否使用 explicit resolution map，不猜 winning side。
- 是否复用 Phase 5 result closer 语义，没有复制出冲突 PnL 规则。
- missing resolution / missing runner output 是否被 skipped，且不计入 PnL。
- 是否输出 per-session summaries 和 aggregate paper PnL。
- 是否没有 settlement crawler、p_hat model/training、长期 DB、无边界 daemon、restart policy、launchd/systemd/crontab。
- Phase 1-9 self-check 是否仍通过。

不要重复：
- 不要复述完整执行任务卡。
- 不要重写执行区证据报告。
- 不要做实现或补测试。
- 不要把 Phase 11 automatic resolution 或 daemon hardening 提前要求进 Phase 10。

输出：
- 先给通过 / 不通过。
- 若不通过，列问题、证据、文件行号、最小返工任务。
- 若通过，简短说明验收依据，并列出仍属于后续 Phase 的残余风险。
```

## Phase 11 Summary

Intent:

- derive Phase 10-compatible resolution maps from public closed market metadata
- remove manual winning-side entry when the public payload is unambiguous
- keep ambiguous settlement cases skipped, not guessed

Locked decisions:

- public Gamma closed-market metadata is the first automatic source
- no wallet/signing/credentials
- no live orders
- no UMA proposal/dispute/redeem action
- no final `p_hat` model
- no long-run database schema
- no daemon behavior

Not for `执行区` to decide:

- alternate settlement source
- disputed/ambiguous market policy beyond skip
- final `p_hat` estimation method
- long-run storage schema
- daemon supervision/restart policy
- new strategy rules

If one of these is required, stop and route back to `规划区`.

## 给执行区的 Phase 11 任务

```text
你现在是 PolyBot 的执行区。请使用 goal 模式执行下面任务。

任务ID：
polybot-paper-phase-11-conservative-resolution-ingestion

目标：
建立 Phase 11 conservative automatic resolution ingestion：从 public Gamma closed-market metadata 或本地 fixture 中读取 market resolution 信息，只在 payload 明确、二元、可映射到 UP/DOWN 时生成 Phase 10 可消费的 resolution map；否则记录 skip reason。

范围外：
- 不做实盘。
- 不下单。
- 不做 wallet、签名、credential、order placement。
- 不做 UMA proposal、dispute、vote、redeem 或 onchain 调用。
- 不猜 winning side。
- 不处理 disputed/ambiguous case，除记录 skip 外不做判断。
- 不实现或估算 p_hat 模型。
- 不训练、不平滑、不回填历史 p_hat。
- 不设计长期数据库 schema。
- 不做无边界 daemon、进程监督、重启策略、crontab/launchd/systemd。
- 不修改 Phase 1 signal 规则。
- 不修改 Phase 5 result closer 语义。
- 不修改 Phase 10 batch closer 语义，除非是为了读取 Phase 11 输出做最小兼容。

先读：
- AGENTS.md
- docs/project_notes/zone_operating_model.md
- docs/project_notes/key_facts.md
- docs/project_notes/issues.md 的 Current Summary
- docs/project_notes/decisions.md 中 ADR-015
- polybot/supervisor_results.py
- polybot/market_discovery.py

如需确认官方字段来源，再读：
- Polymarket Resolution docs: https://docs.polymarket.com/concepts/resolution
- Polymarket Fetching Markets docs: https://docs.polymarket.com/market-data/fetching-markets
- Polymarket List Markets API docs: https://docs.polymarket.com/api-reference/markets/list-markets

如需确认 phase gate，再读：
- docs/implementation-plan.md

交付物：
- 一个最小 resolution ingestion 入口，例如 `polybot/resolution_ingestion.py`。
- CLI/config 输入：
  - market id 或 slug
  - optional local fixture JSON path
  - output resolution map JSON path
  - optional raw metadata output path
- 输出 Phase 10 兼容 resolution map，例如 `{market_id: "UP"}` 或 `{runner_output_path: "DOWN"}` 中至少支持 market_id。
- 输出或记录 raw source metadata，便于验收审查。
- skip records 至少覆盖：
  - not_closed
  - missing_outcomes
  - missing_outcome_prices
  - invalid_outcome_prices
  - non_binary_market
  - ambiguous_terminal_prices
  - fifty_fifty_resolution
  - unmapped_outcome

修改点：
- 使用 public Gamma market metadata；若需要网络访问，只使用 GET market metadata，不使用 trading/order/wallet API。
- Parse `outcomes` and `outcomePrices` whether they arrive as JSON strings or arrays.
- Accept automatic resolution only when:
  - `closed` is true
  - exactly two outcomes exist
  - exactly two prices exist
  - exactly one terminal price is 1.0
  - exactly one terminal price is 0.0
  - winning outcome label maps to UP or DOWN using existing selected_side_labels / outcome labels where available
- 任何不满足条件的 payload 都 skip，不猜。
- 保持 JSON/JSONL 文件输出即可；不要引入数据库。
- self-check 使用本地 fixtures；网络 live smoke test 可选。

执行区自测：
- `python3 -m polybot.resolution_ingestion --self-check` 或等价命令通过。
- self-check 覆盖：
  - UP winning fixture -> resolution map UP
  - DOWN winning fixture -> resolution map DOWN
  - not closed -> skipped
  - non-binary -> skipped
  - missing/invalid outcomePrices -> skipped
  - 50/50-like prices -> skipped
  - unmapped winner label -> skipped
  - generated map can be consumed by Phase 10 batch closer self-check or a small integration fixture
- 现有 Phase 1-10 self-check 仍通过。
- forbidden search 确认无 wallet、signing、credential、order placement、live order path、UMA proposal/dispute/vote/redeem action、p_hat training、database schema、daemon、restart policy、launchd/systemd/crontab。
- compile check 通过。

停止条件：
- 官方字段与实际 payload 不一致，无法可靠判断 winner。
- 需要处理 disputed、ambiguous 或 50/50 resolution policy。
- 需要 alternate settlement source。
- 需要真实资金、wallet、私钥、credential 或交易权限。
- 需要长期数据库 schema。
- 需要无边界 daemon、进程管理或重启策略。
- 需要新增未确认交易规则。

执行完成后：
把下面格式写入 `docs/project_notes/issues.md` 的当前任务日志块。

任务ID：
polybot-paper-phase-11-conservative-resolution-ingestion

改动文件：

范围边界：

运行命令：

结果：

resolution map 样例：

raw metadata / skip 样例：

手工检查：

范围外未做：

阻塞/待规划决定：
```

## Phase 11 验收合同

```text
任务ID：
polybot-paper-phase-11-conservative-resolution-ingestion

目标：
Phase 11 can derive a Phase 10-compatible resolution map from public closed market metadata only when the outcome is unambiguous and maps to UP/DOWN.

必须不做：
- 不下单
- 不接 wallet / signing / credentials
- 不做 UMA proposal / dispute / vote / redeem / onchain action
- 不猜 winning side
- 不处理 disputed/ambiguous/50-50 case，除 skip 外不做判断
- 不估算 p_hat
- 不引入长期数据库 schema
- 不启动无边界 daemon
- 不做进程监督 / 重启策略 / launchd / systemd / crontab
- 不修改 Phase 1、5、10 核心语义

必测：
- resolution ingestion self-check 通过
- UP and DOWN fixtures produce correct resolution map
- not_closed / non_binary / invalid prices / 50-50-like / unmapped cases are skipped
- raw metadata or equivalent source record is preserved for audit
- generated resolution map can feed Phase 10 batch closer
- 代码中无 live order / wallet / signing / UMA action / p_hat training / DB schema / daemon supervisor / restart policy 路径
- 现有 Phase 1-10 self-check 仍通过

重点风险：
- 用未 closed 的市场提前结算
- 用 ambiguous outcomePrices 猜 winner
- 把 UMA/onchain/redeem 行为引进 paper simulation
- 把 long-run storage、p_hat 或 daemon hardening 混进 Phase 11

验收输入：验收合同 + issues.md 中当前任务ID对应的最新执行证据块 + 当前 diff
```

## 给验收区的 Phase 11 任务

```text
你现在是 PolyBot 的验收区。

目标：
只判断 Phase 11 是否通过，不改代码；重点检查 automatic resolution ingestion 是否足够保守：只接受 closed + binary + 1/0 + UP/DOWN mapping 的明确 payload，其余全部 skip。

先读：
- AGENTS.md
- docs/project_notes/zone_operating_model.md
- docs/project_notes/issues.md 的 Current Summary
- docs/project_notes/decisions.md 中 ADR-015
- 上面的 Phase 11 验收合同

验收输入：
- Phase 11 验收合同
- `docs/project_notes/issues.md` 中 `polybot-paper-phase-11-conservative-resolution-ingestion` 的最新执行证据块
- 当前 diff

重点检查：
- 是否要求 `closed == true`。
- 是否 parse outcomes/outcomePrices，并要求 binary + exactly one 1.0 + exactly one 0.0。
- not_closed / non_binary / invalid prices / 50-50-like / unmapped winner 是否 skip。
- 是否保留 raw metadata 或等价 source record 以便审计。
- 生成的 resolution map 是否能被 Phase 10 batch closer 消费。
- 是否没有 wallet/signing/order、UMA proposal/dispute/vote/redeem、p_hat、长期 DB、daemon/restart policy、launchd/systemd/crontab。
- Phase 1-10 self-check 是否仍通过。

不要重复：
- 不要复述完整执行任务卡。
- 不要重写执行区证据报告。
- 不要做实现或补测试。
- 不要把 daemon hardening 或 p_hat modeling 提前要求进 Phase 11。

输出：
- 先给通过 / 不通过。
- 若不通过，列问题、证据、文件行号、最小返工任务。
- 若通过，简短说明验收依据，并列出仍属于后续 Phase 的残余风险。
```

## Phase 12 Summary

Intent:

- make each paper-trading run inspectable as one local artifact directory
- provide a manifest and session index before daemon hardening
- avoid a database until local JSON/JSONL files are proven insufficient

Locked decisions:

- local JSON/JSONL files only
- no database schema
- no daemon behavior
- no process supervision or restart policy
- no live trading
- no wallet/signing/credentials
- no final `p_hat` model
- preserve existing Phase 1-11 record formats

Not for `执行区` to decide:

- database choice
- daemon supervision/restart policy
- alternate storage backend
- final `p_hat` estimation method
- live trading path
- new strategy rules

If one of these is required, stop and route back to `规划区`.

## 给执行区的 Phase 12 任务

```text
你现在是 PolyBot 的执行区。请使用 goal 模式执行下面任务。

任务ID：
polybot-paper-phase-12-stable-run-artifacts

目标：
建立 Phase 12 stable run artifacts and local index：为一次 bounded/continuous paper run 生成稳定的本地目录结构、run manifest、session index 和 summary linkage，使用户不用逐个读 raw JSONL 也能看懂每个 15m session 发生了什么。

范围外：
- 不做实盘。
- 不下单。
- 不做 wallet、签名、credential、order placement。
- 不做 UMA action 或 onchain 调用。
- 不实现或估算 p_hat 模型。
- 不训练、不平滑、不回填历史 p_hat。
- 不引入数据库、SQLite、ORM 或长期 DB schema。
- 不做无边界 daemon。
- 不做进程监督、重启策略、crontab/launchd/systemd。
- 不修改 Phase 1 signal 规则。
- 不修改 Phase 3 marketability / paper fill 规则。
- 不修改 Phase 5 result closer 语义。
- 不修改 Phase 9 supervisor orchestration 规则，除非是为了写入/传递 artifact path 的最小兼容。
- 不修改 Phase 10 batch closer 语义，除非是为了写入/传递 artifact path 的最小兼容。
- 不修改 Phase 11 resolution ingestion 语义，除非是为了写入/传递 artifact path 的最小兼容。

先读：
- AGENTS.md
- docs/project_notes/zone_operating_model.md
- docs/project_notes/key_facts.md
- docs/project_notes/issues.md 的 Current Summary
- docs/project_notes/decisions.md 中 ADR-016
- polybot/supervisor.py
- polybot/supervisor_results.py
- polybot/resolution_ingestion.py

如需确认 phase gate，再读：
- docs/implementation-plan.md

交付物：
- 一个最小 run artifact helper/entry point，例如 `polybot/run_artifacts.py`。
- 一个固定本地目录布局，建议形状：
  - `run_manifest.json`
  - `session_index.json`
  - `supervisor.jsonl`
  - `sessions/<session_key>/runner.jsonl`
  - `sessions/<session_key>/resolution.json`
  - `sessions/<session_key>/resolution_raw.json`
  - `sessions/<session_key>/result.json`
  - `summary.json`
- run manifest 至少包含：
  - run_id
  - created_at / updated_at
  - mode
  - config snapshot
  - supervisor_jsonl path
  - session_index path
  - summary path
  - status
  - schema_version
- session index 至少包含每个 session：
  - session_key
  - market_id / market_slug
  - market_start_time / market_end_time
  - runner_output path
  - runner_status
  - resolution_status / resolution path / raw metadata path
  - result_status / result path
  - skip_reason
  - paper_pnl when available
- 一个本地 deterministic self-check，用 Phase 9-11 fixture 输出组装一个 two-session sample run index。

修改点：
- 优先增加围绕现有输出文件的 index/manifest，不重写既有 JSONL record shape。
- 如需改已有 CLI，只做最小兼容：允许指定 run directory 或把已产生的 path 写入 manifest/index。
- 路径保存为相对 run directory 的路径，除非现有模块只能提供绝对路径；验收时必须能读回。
- skipped sessions 必须留在 session index 里，不能因为没有成交或没有 resolution 被丢掉。
- 保持标准库和现有依赖；不要添加数据库或文件监控依赖。

执行区自测：
- `python3 -m polybot.run_artifacts --self-check` 或等价命令通过。
- self-check 覆盖：
  - sample two-session run directory is created under temp dir
  - run_manifest.json exists and has schema_version/status/paths
  - session_index.json lists both closed and skipped sessions
  - closed session links runner/resolution/result and includes paper_pnl
  - skipped session keeps skip_reason
  - summary.json can be read without reading raw runner JSONL
- 现有 Phase 1-11 self-check 仍通过。
- forbidden search 确认无 wallet、signing、credential、order placement、live order path、UMA action、p_hat training、SQLite/ORM/database schema、daemon、restart policy、launchd/systemd/crontab。
- compile check 通过。

停止条件：
- 需要选择数据库、ORM 或外部 storage backend。
- 需要无边界 daemon、进程管理或重启策略。
- 需要真实资金、wallet、私钥、credential 或交易权限。
- 需要改变 signal、marketability、fill、result closer、resolution ingestion 的语义。
- 需要新增未确认交易规则。

执行完成后：
把下面格式写入 `docs/project_notes/issues.md` 的当前任务日志块。

任务ID：
polybot-paper-phase-12-stable-run-artifacts

改动文件：

范围边界：

运行命令：

结果：

run manifest 样例：

session index 样例：

手工检查：

范围外未做：

阻塞/待规划决定：
```

## Phase 12 验收合同

```text
任务ID：
polybot-paper-phase-12-stable-run-artifacts

目标：
Phase 12 provides stable local JSON/JSONL run artifacts: one run directory, manifest, session index, and summary links that make a multi-session paper run inspectable after the process exits.

必须不做：
- 不下单
- 不接 wallet / signing / credentials
- 不做 UMA / onchain action
- 不估算 p_hat
- 不引入数据库 / SQLite / ORM / 长期 DB schema
- 不启动无边界 daemon
- 不做进程监督 / 重启策略 / launchd / systemd / crontab
- 不修改 Phase 1、3、5、9、10、11 核心语义

必测：
- run artifact self-check 通过
- sample run directory contains manifest, session index, supervisor path, per-session paths, and summary
- session index includes both closed and skipped sessions
- closed session links runner/resolution/result and includes PnL
- skipped session retains skip_reason
- summary can be read without manually scanning raw runner JSONL
- 代码中无 live order / wallet / signing / UMA action / p_hat training / DB schema / daemon supervisor / restart policy 路径
- 现有 Phase 1-11 self-check 仍通过

重点风险：
- 为了“持久化”过早引入数据库
- 改写已验收 raw record formats
- skipped session 从索引里消失
- 把 daemon recovery 或 restart policy 混进 Phase 12

验收输入：验收合同 + issues.md 中当前任务ID对应的最新执行证据块 + 当前 diff
```

## 给验收区的 Phase 12 任务

```text
你现在是 PolyBot 的验收区。

目标：
只判断 Phase 12 是否通过，不改代码；重点检查本地 run artifacts 是否足够稳定、可读、可追踪，并且没有越界进入数据库或 daemon hardening。

先读：
- AGENTS.md
- docs/project_notes/zone_operating_model.md
- docs/project_notes/issues.md 的 Current Summary
- docs/project_notes/decisions.md 中 ADR-016
- 上面的 Phase 12 验收合同

验收输入：
- Phase 12 验收合同
- `docs/project_notes/issues.md` 中 `polybot-paper-phase-12-stable-run-artifacts` 的最新执行证据块
- 当前 diff

重点检查：
- 是否有固定 run directory layout。
- manifest 是否包含 schema_version/status/config/关键路径。
- session index 是否能覆盖 closed 和 skipped sessions。
- runner/resolution/result/summary 路径是否可读回。
- skipped session 是否保留 skip_reason。
- 是否没有 DB/SQLite/ORM、daemon、restart policy、launchd/systemd/crontab。
- 是否没有修改 Phase 1、3、5、9、10、11 核心语义。
- Phase 1-11 self-check 是否仍通过。

不要重复：
- 不要复述完整执行任务卡。
- 不要重写执行区证据报告。
- 不要做实现或补测试。
- 不要把 Phase 13 daemon hardening 提前要求进 Phase 12。

输出：
- 先给通过 / 不通过。
- 若不通过，列问题、证据、文件行号、最小返工任务。
- 若通过，简短说明验收依据，并列出仍属于后续 Phase 的残余风险。
```

## Phase 13 Summary

Intent:

- make the paper supervisor safe to run for repeated sessions as one process
- resume from Phase 12 run artifacts after interruption
- record heartbeat, stop status, recoverable errors, and bounded retries

Locked decisions:

- paper trading only
- no live orders
- no wallet/signing/credentials
- no final `p_hat` model
- no database schema
- no launchd/systemd/crontab/background service install
- no OS-level restart policy
- use Phase 12 run artifacts as recovery state

Not for `执行区` to decide:

- OS service manager choice
- machine reboot/restart policy
- final `p_hat` estimation method
- live trading path
- database/storage backend
- new strategy rules

If one of these is required, stop and route back to `规划区`.

## 给执行区的 Phase 13 任务

```text
你现在是 PolyBot 的执行区。请使用 goal 模式执行下面任务。

任务ID：
polybot-paper-phase-13-resumable-long-run-supervisor

目标：
建立 Phase 13 resumable long-run paper supervisor：让模拟盘 supervisor 能围绕 Phase 12 run artifacts 长时间运行、记录 heartbeat/status、处理可恢复错误、支持从已有 run directory 恢复，并在优雅停止时留下可读状态。

范围外：
- 不做实盘。
- 不下单。
- 不做 wallet、签名、credential、order placement。
- 不实现或估算 p_hat 模型。
- 不训练、不平滑、不回填历史 p_hat。
- 不引入数据库、SQLite、ORM 或长期 DB schema。
- 不安装或生成 launchd/systemd/crontab。
- 不做 OS-level process supervision、后台服务安装、机器重启策略。
- 不修改 Phase 1 signal 规则。
- 不修改 Phase 3 marketability / paper fill 规则。
- 不修改 Phase 5 result closer 语义。
- 不修改 Phase 11 resolution ingestion 语义。
- 不改写 Phase 12 artifact schema，除非只做向后兼容字段追加。

先读：
- AGENTS.md
- docs/project_notes/zone_operating_model.md
- docs/project_notes/key_facts.md
- docs/project_notes/issues.md 的 Current Summary
- docs/project_notes/decisions.md 中 ADR-017
- polybot/supervisor.py
- polybot/run_artifacts.py
- polybot/supervisor_results.py
- polybot/resolution_ingestion.py

如需确认 phase gate，再读：
- docs/implementation-plan.md

交付物：
- 一个最小 long-run 入口，例如 `polybot/long_run.py`，或对现有 supervisor 的最小扩展。
- CLI/config 输入：
  - run directory
  - resume flag
  - max sessions / max runtime / end time / optional explicit continuous flag
  - heartbeat interval seconds
  - retry limit
  - retry backoff seconds
  - runner/session limits from existing supervisor
- status/heartbeat 输出：
  - manifest status updates
  - heartbeat JSONL or status JSON
  - last_error / last_session / processed_sessions
- resume 行为：
  - 读取 Phase 12 `run_manifest.json` 和 `session_index.json`
  - 已经 closed 或 skipped 的 session 不重复处理
  - incomplete/current session 要么继续，要么记录明确 skip/retry 状态；不要静默覆盖
- graceful stop 行为：
  - 捕获可测试的 stop signal/stop request
  - manifest/status 标记为 `stopped` 或 `interrupted`
  - 已存在 artifacts 不损坏
- bounded retry/backoff：
  - 对可恢复 discovery/open-price/runner/resolution/result-closing 错误记录 retry
  - 超过 retry limit 后记录 skip/failure reason，不无限卡住

修改点：
- 优先复用 Phase 9 supervisor、Phase 12 run artifacts、Phase 10/11 result/resolution outputs。
- 如果需要新增状态文件，保持 JSON/JSONL。
- 不要引入异步任务框架、调度器库、文件监控库或数据库。
- 不要把 OS service wrapper 混进本 phase。
- self-check 使用本地 fixtures 和模拟 stop/resume；不需要真实长时间等待。

执行区自测：
- `python3 -m polybot.long_run --self-check` 或等价命令通过。
- self-check 覆盖：
  - sample run starts and writes heartbeat/status
  - simulated interruption marks run stopped/interrupted
  - resume from existing run directory does not duplicate already closed/skipped sessions
  - recoverable error is recorded and retried within configured limit
  - retry limit reached records skip/failure reason and run remains inspectable
  - manifest/session index remain readable after stop/resume
- 现有 Phase 1-12 self-check 仍通过。
- forbidden search 确认无 wallet、signing、credential、order placement、live order path、p_hat training、SQLite/ORM/database schema、launchd/systemd/crontab、service install、OS restart policy。
- compile check 通过。

停止条件：
- 需要选择 OS service manager、后台服务安装或机器重启策略。
- 需要数据库、ORM 或外部 storage backend。
- 需要真实资金、wallet、私钥、credential 或交易权限。
- 需要改变 signal、marketability、fill、result closer、resolution ingestion 的语义。
- 需要新增未确认交易规则。

执行完成后：
把下面格式写入 `docs/project_notes/issues.md` 的当前任务日志块。

任务ID：
polybot-paper-phase-13-resumable-long-run-supervisor

改动文件：

范围边界：

运行命令：

结果：

heartbeat/status 样例：

resume/stop 样例：

手工检查：

范围外未做：

阻塞/待规划决定：
```

## Phase 13 验收合同

```text
任务ID：
polybot-paper-phase-13-resumable-long-run-supervisor

目标：
Phase 13 provides process-local long-run reliability: heartbeat/status, graceful stop, bounded retry/backoff, and resume from Phase 12 artifacts without duplicating completed sessions.

必须不做：
- 不下单
- 不接 wallet / signing / credentials
- 不估算 p_hat
- 不引入数据库 / SQLite / ORM / 长期 DB schema
- 不安装 launchd / systemd / crontab
- 不做 OS-level process supervision / service install / machine restart policy
- 不修改 Phase 1、3、5、11、12 核心语义

必测：
- long-run self-check 通过
- heartbeat/status records are written
- simulated stop marks manifest/status stopped or interrupted
- resume does not duplicate closed/skipped sessions
- recoverable error retry is bounded and recorded
- retry exhaustion records skip/failure reason
- manifest/session index remain readable after stop/resume
- 代码中无 live order / wallet / signing / p_hat training / DB schema / launchd / systemd / crontab / OS restart policy 路径
- 现有 Phase 1-12 self-check 仍通过

重点风险：
- 把 long-run CLI 偷偷做成 OS daemon installer
- retry 无限循环或静默吞错
- resume 重复处理已 closed/skipped session
- stop 后 manifest/index 损坏或状态不可读

验收输入：验收合同 + issues.md 中当前任务ID对应的最新执行证据块 + 当前 diff
```

## 给验收区的 Phase 13 任务

```text
你现在是 PolyBot 的验收区。

目标：
只判断 Phase 13 是否通过，不改代码；重点检查 long-run supervisor 是否能基于 Phase 12 artifacts 恢复、记录状态、有限重试、优雅停止，并且没有越界到 OS service/数据库/实盘。

先读：
- AGENTS.md
- docs/project_notes/zone_operating_model.md
- docs/project_notes/issues.md 的 Current Summary
- docs/project_notes/decisions.md 中 ADR-017
- 上面的 Phase 13 验收合同

验收输入：
- Phase 13 验收合同
- `docs/project_notes/issues.md` 中 `polybot-paper-phase-13-resumable-long-run-supervisor` 的最新执行证据块
- 当前 diff

重点检查：
- 是否写 heartbeat/status。
- graceful stop 是否留下可读 manifest/index。
- resume 是否不会重复 closed/skipped sessions。
- retry/backoff 是否有上限，并记录失败原因。
- 是否没有 launchd/systemd/crontab/service install/OS restart policy。
- 是否没有 DB/SQLite/ORM、live order、wallet/signing、p_hat。
- 是否没有修改 Phase 1、3、5、11、12 核心语义。
- Phase 1-12 self-check 是否仍通过。

不要重复：
- 不要复述完整执行任务卡。
- 不要重写执行区证据报告。
- 不要做实现或补测试。
- 不要把真实部署、系统服务安装、p_hat modeling 或实盘提前要求进 Phase 13。

输出：
- 先给通过 / 不通过。
- 若不通过，列问题、证据、文件行号、最小返工任务。
- 若通过，简短说明验收依据，并列出仍属于后续 Phase 的残余风险。
```

## Phase 14 Summary

Intent:

- prove the current paper robot can run end to end on public data in a bounded dry run
- generate one inspectable run directory and a concise dry-run report
- discover real API/data gaps before adding deployment service wrappers

Locked decisions:

- paper trading only
- no live orders
- no wallet/signing/credentials
- no final `p_hat` model
- no database schema
- no launchd/systemd/crontab/background service install
- no OS-level restart policy
- use existing Phase 1-13 modules and artifacts

Not for `执行区` to decide:

- live trading path
- final `p_hat` estimation method
- OS service manager choice
- database/storage backend
- new strategy rules
- alternate settlement policy for ambiguous markets

If one of these is required, stop and route back to `规划区`.

## 给执行区的 Phase 14 任务

```text
你现在是 PolyBot 的执行区。请使用 goal 模式执行下面任务。

任务ID：
polybot-paper-phase-14-public-data-e2e-dry-run

目标：
执行 Phase 14 public-data end-to-end dry run：用现有 Phase 1-13 模块，在真实公开数据上跑一个有界模拟盘链路，产出一个可审查的 run directory 和 dry-run report。重点是验证机器人能否持续模拟、记录、结算或明确 skip，而不是新增策略或实盘能力。

范围外：
- 不做实盘。
- 不下单。
- 不做 wallet、签名、credential、order placement。
- 不实现或估算 p_hat 模型。
- 不训练、不平滑、不回填历史 p_hat。
- 不引入数据库、SQLite、ORM 或长期 DB schema。
- 不安装或生成 launchd/systemd/crontab。
- 不做 OS-level process supervision、后台服务安装、机器重启策略。
- 不修改 Phase 1 signal 规则。
- 不修改 Phase 3 marketability / paper fill 规则。
- 不修改 Phase 5 result closer 语义。
- 不修改 Phase 11 resolution ingestion 的保守结算规则。
- 不改写 Phase 12 artifact schema。
- 不修改 Phase 13 resume/retry 语义，除非只做 dry-run CLI 兼容。

先读：
- AGENTS.md
- docs/project_notes/zone_operating_model.md
- docs/project_notes/key_facts.md
- docs/project_notes/issues.md 的 Current Summary
- docs/project_notes/decisions.md 中 ADR-018
- polybot/long_run.py
- polybot/run_artifacts.py
- polybot/market_discovery.py
- polybot/market_data.py

如需确认 phase gate，再读：
- docs/implementation-plan.md

交付物：
- 一个 dry-run invocation 或最小入口，例如 `polybot/e2e_dry_run.py`；如果现有 CLI 足够，优先写最小脚本/文档化命令而不是新增大模块。
- 一个真实公开数据 dry-run run directory，使用 Phase 12/13 artifacts：
  - run_manifest.json
  - session_index.json
  - status.json / heartbeat.jsonl
  - supervisor/runner/resolution/result/summary paths where available
- 一个 dry-run report，写入本地文件或 `docs/project_notes/issues.md` 证据块，至少包含：
  - exact commands
  - config values: max sessions/runtime, paper stake, caller-supplied p_hat, thresholds
  - public data source used
  - discovered market/session or explicit skip reason
  - open-price result or skip reason
  - signal/fill/skip result
  - resolution/result status when available
  - final run status
  - blockers/follow-up issues grounded in observed evidence

修改点：
- 先尝试复用已有 CLI/entry points；只有当串联 dry run 不可操作时，才新增最小 `e2e_dry_run` wrapper。
- Dry run 必须 bounded：
  - max sessions 建议 1-2
  - max runtime 或 end time 必须设置
  - runner duration 使用小值，除非需要等真实 15m session 的尾段信号
- 使用 explicit fixed small paper stake。
- `p_hat` 只能是 caller-supplied config；不能估算。
- 如果 live public data/API/WebSocket 在当前环境不可用，记录具体错误和命令；不要伪造成功。
- 如果当前时间没有可交易/可发现 BTC 15m market，记录 skip reason，而不是改 discovery rules。
- 如果 resolution 尚未 available，记录 unresolved/pending，不要猜 winner。
- 保持 JSON/JSONL 文件输出；不要引入数据库或系统服务。

执行区自测：
- 现有 Phase 1-13 self-check 全部仍通过。
- dry-run command 至少运行一次：
  - 成功路径：产生 run directory、manifest、session index、status/heartbeat、dry-run report
  - 如果网络/API/市场时机导致不能完整成交或结算，也必须产生明确 skip/blocker report
- forbidden search 确认无 wallet、signing、credential、order placement、live order path、p_hat training、SQLite/ORM/database schema、launchd/systemd/crontab、service install、OS restart policy。
- compile check 通过。

停止条件：
- 需要真实资金、wallet、私钥、credential 或交易权限。
- 需要改变策略规则、signal timing、marketability/fill 语义或 resolution policy。
- 需要选择 OS service manager、后台服务安装或机器重启策略。
- 需要数据库、ORM 或外部 storage backend。
- 公开 API 与代码假设不一致，且修复会改变已确认边界。

执行完成后：
把下面格式写入 `docs/project_notes/issues.md` 的当前任务日志块。

任务ID：
polybot-paper-phase-14-public-data-e2e-dry-run

改动文件：

范围边界：

运行命令：

结果：

dry-run report 摘要：

run directory 样例：

观察到的真实数据/skip/blocker：

手工检查：

范围外未做：

阻塞/待规划决定：
```

## Phase 14 验收合同

```text
任务ID：
polybot-paper-phase-14-public-data-e2e-dry-run

目标：
Phase 14 demonstrates a bounded public-data end-to-end paper dry run, or produces an evidence-backed blocker list when public data/API/timing prevents full completion.

必须不做：
- 不下单
- 不接 wallet / signing / credentials
- 不估算 p_hat
- 不引入数据库 / SQLite / ORM / 长期 DB schema
- 不安装 launchd / systemd / crontab
- 不做 OS-level process supervision / service install / machine restart policy
- 不修改 Phase 1、3、5、11、12、13 核心语义
- 不猜 winner 或新增 settlement policy

必测：
- Phase 1-13 self-check 仍通过
- dry-run command 实际运行过，且命令、配置、输出路径有证据
- run directory contains manifest/session index/status or heartbeat
- discovery/open-price/runner/result/resolution outcomes are recorded as success, skip, pending, or blocker
- skip/blocker has concrete reason, not silent failure
- no live order / wallet / signing / p_hat training / DB schema / launchd / systemd / crontab / OS restart policy path exists

重点风险：
- 把 dry run 伪装成成功但没有真实公共数据证据
- 为了通过 dry run 改策略或猜结算
- 网络/API 失败时静默吞错
- 把 deployment/service wrapper 混进 Phase 14

验收输入：验收合同 + issues.md 中当前任务ID对应的最新执行证据块 + 当前 diff
```

## 给验收区的 Phase 14 任务

```text
你现在是 PolyBot 的验收区。

目标：
只判断 Phase 14 是否通过，不改代码；重点检查 public-data e2e dry run 是否真实运行、证据完整、边界干净，并且没有把失败伪装成成功。

先读：
- AGENTS.md
- docs/project_notes/zone_operating_model.md
- docs/project_notes/issues.md 的 Current Summary
- docs/project_notes/decisions.md 中 ADR-018
- 上面的 Phase 14 验收合同

验收输入：
- Phase 14 验收合同
- `docs/project_notes/issues.md` 中 `polybot-paper-phase-14-public-data-e2e-dry-run` 的最新执行证据块
- 当前 diff

重点检查：
- dry-run command 是否实际运行，并有命令/config/output path。
- run directory 是否包含 manifest/session index/status 或 heartbeat。
- discovery/open-price/runner/result/resolution 是否都有 success/skip/pending/blocker 记录。
- 如果没有完整成交或结算，原因是否来自真实 public data/API/timing，而不是 silent failure。
- 是否没有 wallet/signing/order、p_hat model/training、DB、launchd/systemd/crontab/service install。
- 是否没有修改 Phase 1、3、5、11、12、13 核心语义。
- Phase 1-13 self-check 是否仍通过。

不要重复：
- 不要复述完整执行任务卡。
- 不要重写执行区证据报告。
- 不要做实现或补测试。
- 不要要求 Phase 14 必须盈利、必须成交、必须结算；它必须真实、有证据、边界干净。

输出：
- 先给通过 / 不通过。
- 若不通过，列问题、证据、文件行号、最小返工任务。
- 若通过，简短说明验收依据，并列出后续是否需要 Phase 15 的真实稳定性修复或部署规划。
```

## Phase 15 Summary

Intent:

- fix the live Phase 14 blocker: public discovery did not find a valid current BTC 15m market
- broaden public discovery sources using documented events/markets/tag/slug/pagination paths
- keep candidate validation strict and improve diagnostics

Locked decisions:

- public data only
- no live orders
- no wallet/signing/credentials
- no final `p_hat` model
- no database schema
- no OS service behavior
- preserve existing strategy, fill, open-price, resolution, artifacts, and long-run semantics

Not for `执行区` to decide:

- loosening BTC/15m/UP-DOWN validation
- live trading path
- final `p_hat` estimation method
- OS service manager choice
- database/storage backend
- alternate settlement policy
- new strategy rules

If one of these is required, stop and route back to `规划区`.

## 给执行区的 Phase 15 任务

```text
你现在是 PolyBot 的执行区。请使用 goal 模式执行下面任务。

任务ID：
polybot-paper-phase-15-public-btc-15m-discovery-hardening

目标：
执行 Phase 15 public BTC 15m discovery hardening：针对 Phase 14 live dry run 的 `no_valid_candidate` 结果，扩展公开 market/session discovery 的来源覆盖和诊断能力，让下一次 dry run 能从 documented public sources 找到 BTC 15m session，或给出比 `no_valid_candidate` 更精确的 live blocker。

范围外：
- 不做实盘。
- 不下单。
- 不做 wallet、签名、credential、order placement。
- 不实现或估算 p_hat 模型。
- 不训练、不平滑、不回填历史 p_hat。
- 不引入数据库、SQLite、ORM 或长期 DB schema。
- 不安装或生成 launchd/systemd/crontab。
- 不做 OS-level process supervision、后台服务安装、机器重启策略。
- 不放宽 BTC/Bitcoin identity、15-minute duration、active/open、UP/DOWN token mapping validation。
- 不修改 Phase 1 signal 规则。
- 不修改 Phase 3 marketability / paper fill 规则。
- 不修改 Phase 8 open-price selection 规则。
- 不修改 Phase 11 resolution ingestion 的保守结算规则。
- 不改写 Phase 12 artifact schema 或 Phase 13 long-run semantics。

先读：
- AGENTS.md
- docs/project_notes/zone_operating_model.md
- docs/project_notes/key_facts.md
- docs/project_notes/issues.md 的 Current Summary
- docs/project_notes/decisions.md 中 ADR-019
- polybot/market_discovery.py
- polybot/e2e_dry_run.py

如需确认官方字段来源，再读：
- Polymarket Fetching Markets docs: https://docs.polymarket.com/market-data/fetching-markets
- Polymarket List Markets API docs: https://docs.polymarket.com/api-reference/markets/list-markets

如需确认 phase gate，再读：
- docs/implementation-plan.md

交付物：
- 对 `polybot.market_discovery` 的最小 hardening，或一个小 helper，被 Phase 14 dry-run 使用。
- 支持 documented public discovery paths：
  - events endpoint pagination
  - markets endpoint pagination
  - optional `tag_id` + `related_tags`
  - optional `slug`
  - explicit `source_url`
- diagnostics 输出，至少包含：
  - sources tried
  - source timestamps
  - pages fetched / offsets
  - events count / markets count
  - validation_skip_reasons
  - top candidate snapshots with question/title/slug/start/end/outcomes/token mapping presence
  - final skip_reason
- Phase 14 dry-run report 能包含这些 diagnostics。
- 本地 fixture self-check 覆盖 nested events payload、flat markets payload、pagination merge、ambiguous candidates、no candidate diagnostics。

修改点：
- 保留现有 `validate_candidate(...)` 的严格规则；不要为了通过 live dry run 放宽规则。
- 可以增加 source normalization，让 events 和 markets 两种 payload 都进入同一验证路径。
- 可以增加 pagination 参数和循环，但必须有 page/limit 上限，不能无限抓取。
- 可以增加 minimal User-Agent 复用 Phase 14 dry-run 经验。
- 如果 live public fetch 受网络权限或 API 403/429 限制，记录具体 blocker；不要伪造候选市场。
- 如果公开 payload 的字段形状与当前假设不同，记录 diagnostics；只做不改变业务语义的解析兼容。

执行区自测：
- `python3 -m polybot.market_discovery --self-check` 或新增等价 self-check 通过。
- self-check 覆盖：
  - valid BTC 15m session from nested events payload
  - valid BTC 15m session from flat markets payload
  - pagination combines multiple pages within configured bound
  - ambiguous candidates remain ambiguous
  - no candidate includes useful diagnostics
- `python3 -m polybot.e2e_dry_run --self-check` 仍通过。
- 至少运行一次 bounded public dry-run 或 discovery smoke：
  - 成功找到 session；或
  - 产生比 Phase 14 更精确的 live diagnostics/blocker
- 现有 Phase 1-14 self-check 仍通过。
- forbidden search 确认无 wallet、signing、credential、order placement、live order path、p_hat training、SQLite/ORM/database schema、launchd/systemd/crontab、service install、OS restart policy。
- compile check 通过。

停止条件：
- 需要放宽 BTC/15m/UP-DOWN validation 才能找到 candidate。
- 需要真实资金、wallet、私钥、credential 或交易权限。
- 需要改变策略规则、signal timing、marketability/fill 语义、open-price selection 或 resolution policy。
- 需要选择 OS service manager、后台服务安装或机器重启策略。
- 需要数据库、ORM 或外部 storage backend。
- 官方公开 API 与代码假设不一致，且修复会改变已确认边界。

执行完成后：
把下面格式写入 `docs/project_notes/issues.md` 的当前任务日志块。

任务ID：
polybot-paper-phase-15-public-btc-15m-discovery-hardening

改动文件：

范围边界：

运行命令：

结果：

discovery diagnostics 样例：

public dry-run/discovery smoke 摘要：

手工检查：

范围外未做：

阻塞/待规划决定：
```

## Phase 15 验收合同

```text
任务ID：
polybot-paper-phase-15-public-btc-15m-discovery-hardening

目标：
Phase 15 hardens public BTC 15m discovery so the next dry run either finds a valid session from documented public sources or produces precise diagnostics explaining why none was selected.

必须不做：
- 不下单
- 不接 wallet / signing / credentials
- 不估算 p_hat
- 不引入数据库 / SQLite / ORM / 长期 DB schema
- 不安装 launchd / systemd / crontab
- 不做 OS-level process supervision / service install / machine restart policy
- 不放宽 BTC/15m/UP-DOWN/active-open validation
- 不修改 Phase 1、3、8、11、12、13、14 核心语义

必测：
- discovery self-check 通过
- nested events fixture and flat markets fixture can both yield valid BTC 15m config
- pagination fixture works within configured bound
- ambiguous and no-candidate cases remain safe and diagnostic-rich
- Phase 14 dry-run report includes discovery diagnostics
- bounded public smoke either finds a valid session or records precise live blocker
- no live order / wallet / signing / p_hat training / DB schema / launchd / systemd / crontab / OS restart policy path exists
- 现有 Phase 1-14 self-check 仍通过

重点风险：
- 为了发现候选而放宽市场验证
- 分页无上限
- live API 失败时回退到伪造 fixture success
- 把 discovery hardening 混成策略修改、结算修改或部署服务

验收输入：验收合同 + issues.md 中当前任务ID对应的最新执行证据块 + 当前 diff
```

## 给验收区的 Phase 15 任务

```text
你现在是 PolyBot 的验收区。

目标：
只判断 Phase 15 是否通过，不改代码；重点检查 public BTC 15m discovery 是否来源覆盖更完整、诊断更清楚，并且没有放宽候选市场验证规则。

先读：
- AGENTS.md
- docs/project_notes/zone_operating_model.md
- docs/project_notes/issues.md 的 Current Summary
- docs/project_notes/decisions.md 中 ADR-019
- 上面的 Phase 15 验收合同

验收输入：
- Phase 15 验收合同
- `docs/project_notes/issues.md` 中 `polybot-paper-phase-15-public-btc-15m-discovery-hardening` 的最新执行证据块
- 当前 diff

重点检查：
- 是否支持 events/markets payload 和 pagination。
- 是否保留严格 BTC/15m/active-open/UP-DOWN token mapping validation。
- diagnostics 是否包含 sources tried、counts、skip reasons、candidate snapshots。
- Phase 14 dry-run 是否能消费 diagnostics。
- live smoke 是否有真实证据，不伪造成成功。
- 是否没有 wallet/signing/order、p_hat model/training、DB、launchd/systemd/crontab/service install。
- 是否没有修改 Phase 1、3、8、11、12、13、14 核心语义。
- Phase 1-14 self-check 是否仍通过。

不要重复：
- 不要复述完整执行任务卡。
- 不要重写执行区证据报告。
- 不要做实现或补测试。
- 不要要求 Phase 15 必须发现市场；它必须改进来源覆盖和诊断，不能放宽规则硬找。

输出：
- 先给通过 / 不通过。
- 若不通过，列问题、证据、文件行号、最小返工任务。
- 若通过，简短说明验收依据，并判断下一步是否应重跑 Phase 14 dry run 或进入部署规划。
```

## Phase 16 Summary

Intent:

- identify the correct public source path for current BTC 15m Up/Down markets
- prove the calibrated source with a bounded discovery smoke or Phase 14 dry run
- avoid weakening validation or changing strategy just to force a candidate

Locked decisions:

- public data only
- no live orders
- no wallet/signing/credentials
- no final `p_hat` model
- no database schema
- no OS service behavior
- preserve strict BTC/15m/UP-DOWN validation
- preserve existing strategy, fill, open-price, resolution, artifacts, dry-run, and long-run semantics

Not for `执行区` to decide:

- loosening BTC/15m/UP-DOWN validation
- live trading path
- final `p_hat` estimation method
- OS service manager choice
- database/storage backend
- alternate settlement policy
- new strategy rules

If one of these is required, stop and route back to `规划区`.

## 给执行区的 Phase 16 任务

```text
你现在是 PolyBot 的执行区。请使用 goal 模式执行下面任务。

任务ID：
polybot-paper-phase-16-btc-15m-source-calibration

目标：
执行 Phase 16 BTC 15m public source calibration and dry-run proof：基于 Phase 15 的 diagnostics，找出当前 Polymarket BTC 15m Up/Down 市场应使用的公开 source path（tag、slug、source_url 或 documented filter combination），并用 bounded discovery smoke 或 Phase 14 dry run 证明它能被现有严格验证消费；如果找不到，输出精确 source blocker。

范围外：
- 不做实盘。
- 不下单。
- 不做 wallet、签名、credential、order placement。
- 不实现或估算 p_hat 模型。
- 不训练、不平滑、不回填历史 p_hat。
- 不引入数据库、SQLite、ORM 或长期 DB schema。
- 不安装或生成 launchd/systemd/crontab。
- 不做 OS-level process supervision、后台服务安装、机器重启策略。
- 不放宽 BTC/Bitcoin identity、15-minute duration、active/open、UP/DOWN token mapping validation。
- 不修改 Phase 1 signal 规则。
- 不修改 Phase 3 marketability / paper fill 规则。
- 不修改 Phase 8 open-price selection 规则。
- 不修改 Phase 11 resolution ingestion 的保守结算规则。
- 不改写 Phase 12 artifact schema、Phase 13 long-run semantics 或 Phase 14 dry-run semantics。

先读：
- AGENTS.md
- docs/project_notes/zone_operating_model.md
- docs/project_notes/key_facts.md
- docs/project_notes/issues.md 的 Current Summary
- docs/project_notes/decisions.md 中 ADR-020
- docs/project_notes/issues.md 中 `polybot-paper-phase-15-public-btc-15m-discovery-hardening` 的最新执行证据块
- polybot/market_discovery.py
- polybot/e2e_dry_run.py

如需确认官方字段来源，再读：
- Polymarket Fetching Markets docs: https://docs.polymarket.com/market-data/fetching-markets
- Polymarket List Markets API docs: https://docs.polymarket.com/api-reference/markets/list-markets

如需确认 phase gate，再读：
- docs/implementation-plan.md

交付物：
- source calibration evidence，写入 `docs/project_notes/issues.md` 执行证据块：
  - sources tried
  - exact URLs or tag/slug/filter combinations
  - source timestamps
  - result: selected session or precise blocker
- 如发现稳定 source：
  - 最小配置/CLI 支持，允许 Phase 14 dry run 使用该 source，无需改代码
  - 不要硬编码成唯一不可配置路径，除非已有代码已有默认 source pattern
- bounded discovery smoke 或 Phase 14 dry-run invocation：
  - 使用 calibrated source
  - 产生 run directory 或 discovery output
  - 保留 diagnostics
- 如果找不到：
  - 记录 exact blocker，不伪造 fixture success
  - 给规划区一个最小下一步建议，例如需要用户提供 Polymarket 前端 URL/slug，或需要扩展哪个 documented source

修改点：
- 优先不改代码：先用现有 `--source-url` / `--slug` / `--tag-id` / `--source-kind` / pagination 参数证明 source。
- 只有当现有 CLI 无法表达稳定 source 时，才做最小兼容改动。
- 任何候选仍必须通过现有 `validate_candidate(...)`。
- 可以增加更清晰的 source calibration report 输出；不要新增数据库或长期服务。
- 网络/API 失败必须记录具体错误和命令。

执行区自测：
- 现有 Phase 1-15 self-check 仍通过。
- 至少运行一个 bounded discovery smoke 或 Phase 14 dry-run：
  - 成功：选出 valid BTC 15m session，并记录 source。
  - 未成功：记录比 Phase 15 更具体的 source blocker 和 next planning input。
- 如果改代码：
  - `python3 -m polybot.market_discovery --self-check` 仍通过。
  - `python3 -m polybot.e2e_dry_run --self-check` 仍通过。
  - compile check 通过。
- forbidden search 确认无 wallet、signing、credential、order placement、live order path、p_hat training、SQLite/ORM/database schema、launchd/systemd/crontab、service install、OS restart policy。

停止条件：
- 需要放宽 BTC/15m/UP-DOWN validation 才能找到 candidate。
- 需要真实资金、wallet、私钥、credential 或交易权限。
- 需要改变策略规则、signal timing、marketability/fill 语义、open-price selection 或 resolution policy。
- 需要选择 OS service manager、后台服务安装或机器重启策略。
- 需要数据库、ORM 或外部 storage backend。
- 需要用户提供前端 Polymarket URL/slug 才能继续定位 source。

执行完成后：
把下面格式写入 `docs/project_notes/issues.md` 的当前任务日志块。

任务ID：
polybot-paper-phase-16-btc-15m-source-calibration

改动文件：

范围边界：

运行命令：

结果：

source calibration evidence：

dry-run/discovery proof：

手工检查：

范围外未做：

阻塞/待规划决定：
```

## Phase 16 验收合同

```text
任务ID：
polybot-paper-phase-16-btc-15m-source-calibration

目标：
Phase 16 identifies and proves a public source path for BTC 15m discovery, or returns a precise source blocker without loosening validation.

必须不做：
- 不下单
- 不接 wallet / signing / credentials
- 不估算 p_hat
- 不引入数据库 / SQLite / ORM / 长期 DB schema
- 不安装 launchd / systemd / crontab
- 不做 OS-level process supervision / service install / machine restart policy
- 不放宽 BTC/15m/UP-DOWN/active-open validation
- 不修改 Phase 1、3、8、11、12、13、14、15 核心语义

必测：
- source calibration evidence includes exact sources/URLs/filters tried
- bounded discovery smoke or Phase 14 dry-run actually ran
- if a session is selected, it passes existing strict validation
- if no session is selected, blocker is precise and more actionable than Phase 15 generic source coverage
- no fixture success is presented as live public proof
- no live order / wallet / signing / p_hat training / DB schema / launchd / systemd / crontab / OS restart policy path exists
- 现有 Phase 1-15 self-check 仍通过

重点风险：
- 为了找到市场而放宽验证
- 把前端搜索/猜测当成已验证 API source
- live API 失败时回退到伪造成功
- 把 source calibration 混成策略修改、结算修改或部署服务

验收输入：验收合同 + issues.md 中当前任务ID对应的最新执行证据块 + 当前 diff
```

## 给验收区的 Phase 16 任务

```text
你现在是 PolyBot 的验收区。

目标：
只判断 Phase 16 是否通过，不改代码；重点检查是否真实校准 BTC 15m public source，或给出明确 source blocker，并且没有放宽候选验证。

先读：
- AGENTS.md
- docs/project_notes/zone_operating_model.md
- docs/project_notes/issues.md 的 Current Summary
- docs/project_notes/decisions.md 中 ADR-020
- 上面的 Phase 16 验收合同

验收输入：
- Phase 16 验收合同
- `docs/project_notes/issues.md` 中 `polybot-paper-phase-16-btc-15m-source-calibration` 的最新执行证据块
- 当前 diff

重点检查：
- source evidence 是否包含 exact URLs/tags/slugs/filters。
- 是否实际运行 bounded discovery smoke 或 Phase 14 dry-run。
- 若选出 session，是否通过现有 strict validation。
- 若未选出 session，blocker 是否足够具体，可交回规划区决策。
- 是否没有用 fixture 伪装 live public proof。
- 是否没有 wallet/signing/order、p_hat model/training、DB、launchd/systemd/crontab/service install。
- 是否没有修改 Phase 1、3、8、11、12、13、14、15 核心语义。
- Phase 1-15 self-check 是否仍通过。

不要重复：
- 不要复述完整执行任务卡。
- 不要重写执行区证据报告。
- 不要做实现或补测试。
- 不要要求 Phase 16 必须发现市场；它必须证明 source，或给出可行动 blocker。

输出：
- 先给通过 / 不通过。
- 若不通过，列问题、证据、文件行号、最小返工任务。
- 若通过，简短说明验收依据，并判断下一步是否重跑 full Phase 14 dry run、继续 source 调研，或进入稳定运行验证。
```

## Phase 17 Summary

Intent:

- use the Phase 16 calibrated source path against the next BTC 15m session
- align dry-run BTC reference capture to the market open
- prove open-price capture with real WebSocket data, or return a precise operational blocker

Locked decisions:

- public data only
- no live orders
- no wallet/signing/credentials
- no final `p_hat` model
- no database schema
- no OS service behavior
- no historical backfill or reconstructed opening BTC price
- preserve strict open-price freshness and Phase 1 signal semantics

Not for `执行区` to decide:

- accepting stale/pre-start BTC records as open price
- changing the strategy entry timing or move threshold logic
- replacing WebSocket-first capture with low-frequency polling
- introducing a new BTC reference source without routing back to `规划区`
- adding deployment/service/restart policy

If one of these is required, stop and route back to `规划区`.

## 给执行区的 Phase 17 任务

```text
你现在是 PolyBot 的执行区。请使用 goal 模式执行下面任务。

任务ID：
polybot-paper-phase-17-open-price-window-alignment

目标：
执行 Phase 17 open-price window alignment：用 Phase 16 已校准的 public source `--search-query "bitcoin up down 15m"` 选择下一场 BTC 15m session，并让 dry-run 在有界等待后于 market_start_time 附近通过 WebSocket 抓 BTC reference，从而满足现有 open-price freshness 规则；如果不能做到，输出精确 operational blocker。

范围外：
- 不做实盘。
- 不下单。
- 不做 wallet、签名、credential、order placement。
- 不实现或估算 p_hat 模型。
- 不训练、不平滑、不回填历史 p_hat。
- 不引入数据库、SQLite、ORM 或长期 DB schema。
- 不安装或生成 launchd/systemd/crontab。
- 不做 OS-level process supervision、后台服务安装、机器重启策略。
- 不修改 Phase 1 signal 规则。
- 不修改 Phase 3 marketability / paper fill 规则。
- 不修改 Phase 8 open-price freshness 语义。
- 不把 pre-start、stale、历史回填、REST 历史价格或推断价格当成 open price。
- 不放宽 BTC/15m/UP-DOWN discovery validation。
- 不改变 result closing、resolution、artifact schema、long-run recovery 语义。

先读：
- AGENTS.md
- docs/project_notes/zone_operating_model.md
- docs/project_notes/issues.md 的 Current Summary
- docs/project_notes/issues.md 中 `polybot-paper-phase-16-btc-15m-source-calibration` 的最新执行证据块
- docs/project_notes/decisions.md 中 ADR-021
- polybot/e2e_dry_run.py
- polybot/open_price.py
- polybot/market_data.py

如需确认边界，再读：
- docs/product_consensus/polymarket_paper_trader_v1.md
- docs/architecture.md
- docs/implementation-plan.md 的 Phase 17

交付物：
- 最小 dry-run 等待开盘支持：
  - 当 selected session 的 `market_start_time` 在未来时，允许在明确 `max_wait_to_open_seconds` 预算内等待到开盘附近再抓 BTC reference。
  - 如果需要等待的时间超过预算，跳过并记录 `wait_to_open_budget_exceeded` 或同等明确原因。
  - 如果 session 已经开盘太久，不要事后补 open price；改用 `--mode next` 的真实 proof，或记录明确 blocker。
- dry-run report 中记录：
  - `wait_to_open` step，包括 session start、当前时间、需要等待秒数、等待预算、结果。
  - `btc_reference_capture` step，包括 record_count 或具体异常。
  - `open_price` step，包括 captured 或现有 skip_reason。
- 一次真实 calibrated-source dry-run 尝试：
  - 使用 `--search-query "bitcoin up down 15m"`
  - 使用 `--mode next`
  - 使用明确 wait budget
  - 输出 run_dir 和 `dry_run_report.json`
- 如果网络或等待窗口导致无法完整证明，给出最小下一步 blocker，不要伪造 fixture success。

修改点：
- 优先只改 `polybot/e2e_dry_run.py`；只有共享逻辑确实已存在或必须复用时，才触碰其他文件。
- 等待逻辑用 Python 标准库 / asyncio 即可；不要新增依赖。
- 保留 `open_price.py` 的选择规则；不要为了通过 dry-run 改它的 freshness 语义。
- 保留 Phase 16 `--search-query` source 支持。

执行区自测：
- touched module self-check 通过，至少包括：
  - `python3 -m polybot.e2e_dry_run --self-check`
  - `python3 -m polybot.open_price --self-check`
  - 如修改 market data：`python3 -m polybot.market_data --self-check`
- compile check 通过：
  - `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache python3 -m compileall -q polybot`
- 运行一次 bounded public dry-run proof；成功标准二选一：
  - 成功路径：`session_discovery: success`、`wait_to_open: success/no_wait_needed`、`btc_reference_capture` 有记录、`open_price: captured`。
  - 阻塞路径：报告比 Phase 16 更具体的 blocker，例如 wait budget 不足、BTC websocket timeout、无 post-start record，并保留 run_dir/report。
- forbidden search 确认无 wallet、signing、credential、order placement、live order path、p_hat training、SQLite/ORM/database schema、launchd/systemd/crontab、service install、OS restart policy。

停止条件：
- 需要使用历史回填、REST historical klines、推断价格或放宽 open-price freshness 才能得到 open price。
- 需要改变策略 signal、entry timing、move threshold、marketability/fill 或 resolution policy。
- 需要真实资金、wallet、私钥、credential 或交易权限。
- 需要选择 OS service manager、后台服务安装、机器重启策略。
- 需要数据库、ORM 或外部 storage backend。
- 需要更换 BTC reference source。

执行完成后：
把下面格式写入 `docs/project_notes/issues.md` 的当前任务日志块。

任务ID：
polybot-paper-phase-17-open-price-window-alignment

改动文件：

范围边界：

运行命令：

结果：

dry-run proof：

手工检查：

范围外未做：

阻塞/待规划决定：
```

## Phase 17 验收合同

```text
任务ID：
polybot-paper-phase-17-open-price-window-alignment

目标：
Phase 17 proves that public dry-run can align BTC reference capture to the next market open, or returns a precise operational blocker without changing strategy or open-price semantics.

必须不做：
- 不下单
- 不接 wallet / signing / credentials
- 不估算 p_hat
- 不引入数据库 / SQLite / ORM / 长期 DB schema
- 不安装 launchd / systemd / crontab
- 不做 OS-level process supervision / service install / machine restart policy
- 不用历史回填、推断价格、pre-start record 或 stale record 伪装 open price
- 不放宽 BTC/15m/UP-DOWN discovery validation
- 不修改 Phase 1、3、8、11、12、13、14、15、16 核心语义

必测：
- dry-run report 包含 `wait_to_open`、`btc_reference_capture`、`open_price` 证据
- bounded public dry-run 使用 `--search-query "bitcoin up down 15m"` 和 `--mode next`
- 成功时 open price 来自 post-start fresh BTC WebSocket record
- 失败时 blocker 精确说明是 wait budget、network/WS timeout、missing post-start record，或其他可行动原因
- touched self-checks 和 compile check 通过
- forbidden search 无 wallet/signing/order、p_hat training、DB schema、launchd/systemd/crontab/service install/OS restart policy path

重点风险：
- 为了通过 dry-run 而接受 stale/pre-start BTC record
- 把历史价格回填伪装成实时 open price
- 把等待逻辑做成无限阻塞
- 顺手改策略、marketability、settlement、storage 或 deployment

验收输入：验收合同 + issues.md 中当前任务ID对应的最新执行证据块 + 当前 diff
```

## 给验收区的 Phase 17 任务

```text
你现在是 PolyBot 的验收区。

目标：
只判断 Phase 17 是否通过，不改代码；重点检查 dry-run 是否正确等待下一场开盘并用真实 WebSocket BTC record 捕获 open price，或是否输出了精确 blocker。

先读：
- AGENTS.md
- docs/project_notes/zone_operating_model.md
- docs/project_notes/issues.md 的 Current Summary
- docs/project_notes/decisions.md 中 ADR-021
- 上面的 Phase 17 验收合同

验收输入：
- Phase 17 验收合同
- `docs/project_notes/issues.md` 中 `polybot-paper-phase-17-open-price-window-alignment` 的最新执行证据块
- 当前 diff

重点检查：
- 是否没有修改策略 signal、open-price freshness 语义、marketability/fill、resolution、storage 或 deployment。
- dry-run 是否使用 calibrated source 和 `--mode next`。
- report 是否包含 wait/capture/open-price 三段证据。
- 如果 captured，open price 是否来自 post-start fresh WebSocket BTC record。
- 如果 blocked，原因是否可行动，不是泛泛的 dry-run failed。
- 等待是否有上限，没有无限阻塞。
- 自测、compile、forbidden search 是否完成。

不要重复：
- 不要复述完整执行任务卡。
- 不要重写执行区证据报告。
- 不要做实现或补测试。

输出：
- 先给通过 / 不通过。
- 若不通过，列问题、证据、文件行号、最小返工任务。
- 若通过，简短说明验收依据，并判断下一步是否进入真实一轮 session paper-run proof。
```

## Later Phases

Later phases should be generated only after the Phase 17 gate passes, in the same paired shape.
