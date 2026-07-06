# API Mismatch Notes

## 2026-07-06 - Phase 2 Polymarket Market WebSocket Smoke Test

- Context: Phase 2 market-data capture demo.
- Official docs checked:
  - Polymarket market WebSocket endpoint: `wss://ws-subscriptions-clob.polymarket.com/ws/market`
  - Subscription shape: `{"assets_ids": [...], "type": "market", "custom_feature_enabled": true}`
  - Expected event types include `book`, `price_change`, `best_bid_ask`, `new_market`, and `market_resolved`.
- Runtime observation:
  - The demo connected and sent a market subscription, but no Polymarket event arrived before timeout.
  - CLOB `/simplified-markets` pagination did not yield an `active && !closed && accepting_orders` token in the checked pages.
  - Gamma events returned CLOB token IDs for an active-looking event, but CLOB `/book?token_id=...` returned 404 for the sampled token.
- Current handling:
  - The capture layer keeps WebSocket as the Polymarket primary path.
  - The demo reports `polymarket_connected_no_event_before_timeout` instead of silently treating this as success.
  - BTC reference capture works through Binance BTCUSDT trade WebSocket records.
- Follow-up:
  - Planning or maintenance should confirm the current official BTC 15m market discovery path and token source before Phase 3 consumes Polymarket orderbook data.

## 2026-07-06 - Phase 2 Refill Polymarket Event Evidence

- Context: Acceptance returned Phase 2 because there was no real Polymarket record proving timestamp mapping.
- Runtime finding:
  - `https://clob.polymarket.com/sampling-simplified-markets` returned active, open, accepting-order CLOB tokens.
  - Using token `43187333641922996188398060383389814287787647811837308994701068387397271207198`, the market WebSocket returned a real `book` event.
- Evidence:
  - Captured Polymarket event type: `book`
  - Payload source timestamp key: `timestamp`
  - Recorded `source_timestamp_ms`: `1783327698002`
  - Recorded `local_receive_timestamp`: `2026-07-06T08:48:29.309337+00:00`
- Current handling:
  - `polybot.market_data.source_timestamp_ms()` supports Polymarket `timestamp` payloads and Binance `E` / `T` payloads.
  - `polybot.market_data --self-check` now includes a Polymarket-style `timestamp` assertion.
- Remaining note:
  - BTC 15m-specific token discovery is still not solved by this refill. Phase 3 should not assume a BTC 15m market discovery path until planning or maintenance verifies it.
