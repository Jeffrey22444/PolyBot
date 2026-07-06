# Polymarket Paper Trading Task Plan

Use this file as the copy-ready source for `执行区` and `验收区`.

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

## Later Phases

Later phases should be generated only after the Phase 5 gate passes, in the same paired shape:

- one execution task
- one execution evidence template
- one acceptance contract
- one acceptance task

Do not start them until the previous phase gate passes.
