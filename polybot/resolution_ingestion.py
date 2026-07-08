from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from polybot.market_discovery import fetch_json, first_text, parse_jsonish, truthy
from polybot.supervisor_results import batch_close, load_resolution_map


GAMMA_MARKETS_URL = "https://gamma-api.polymarket.com/markets"


def market_id(market: dict[str, Any]) -> str | None:
    return first_text(market, ("id", "conditionId", "questionID", "questionId"))


def selected_side(market: dict[str, Any], outcome: str) -> str | None:
    label = outcome.strip()
    upper = label.upper()
    if upper in ("UP", "DOWN"):
        return upper
    labels = market.get("selected_side_labels") or {}
    if isinstance(labels, dict):
        for side, value in labels.items():
            if str(side).upper() in ("UP", "DOWN") and str(value).strip().lower() == label.lower():
                return str(side).upper()
    return None


def parse_outcomes(market: dict[str, Any]) -> list[str] | str:
    outcomes = parse_jsonish(market.get("outcomes"))
    if not isinstance(outcomes, list) or not outcomes:
        return "missing_outcomes"
    if len(outcomes) != 2:
        return "non_binary_market"
    return [str(outcome) for outcome in outcomes]


def parse_prices(market: dict[str, Any]) -> list[float] | str:
    prices = parse_jsonish(market.get("outcomePrices"))
    if prices is None:
        return "missing_outcome_prices"
    if not isinstance(prices, list) or len(prices) != 2:
        return "invalid_outcome_prices"
    try:
        return [float(price) for price in prices]
    except (TypeError, ValueError):
        return "invalid_outcome_prices"


def resolution_status_skip_reason(market: dict[str, Any]) -> str | None:
    status = first_text(market, ("umaResolutionStatus", "resolutionStatus", "resolution_status"))
    if status is None:
        return None
    normalized = status.strip().lower()
    if "disput" in normalized:
        return "disputed_resolution_status"
    if normalized in ("resolved", "settled", "finalized", "complete", "completed"):
        return None
    return "unresolved_resolution_status"


def derive_resolution(market: dict[str, Any]) -> dict[str, Any]:
    mid = market_id(market)
    if not truthy(market.get("closed")):
        return {"market_id": mid, "status": "skipped", "skip_reason": "not_closed"}
    status_skip = resolution_status_skip_reason(market)
    if status_skip:
        return {"market_id": mid, "status": "skipped", "skip_reason": status_skip}

    outcomes = parse_outcomes(market)
    if isinstance(outcomes, str):
        return {"market_id": mid, "status": "skipped", "skip_reason": outcomes}
    prices = parse_prices(market)
    if isinstance(prices, str):
        return {"market_id": mid, "status": "skipped", "skip_reason": prices}

    ones = [index for index, price in enumerate(prices) if price == 1.0]
    zeros = [index for index, price in enumerate(prices) if price == 0.0]
    if len(set(prices)) == 1 and prices[0] == 0.5:
        return {"market_id": mid, "status": "skipped", "skip_reason": "fifty_fifty_resolution"}
    if len(ones) != 1 or len(zeros) != 1:
        return {"market_id": mid, "status": "skipped", "skip_reason": "ambiguous_terminal_prices"}

    side = selected_side(market, outcomes[ones[0]])
    if side is None:
        return {"market_id": mid, "status": "skipped", "skip_reason": "unmapped_outcome", "winning_outcome": outcomes[ones[0]]}
    return {"market_id": mid, "status": "resolved", "winning_side": side, "winning_outcome": outcomes[ones[0]]}


def extract_market(payload: Any) -> dict[str, Any]:
    data = payload.get("data", payload) if isinstance(payload, dict) else payload
    if isinstance(data, list):
        if len(data) != 1 or not isinstance(data[0], dict):
            raise ValueError("expected exactly one market metadata object")
        return data[0]
    if isinstance(data, dict):
        return data
    raise ValueError("expected market metadata object")


def build_markets_url(args: argparse.Namespace) -> str:
    params: dict[str, str | int] = {"limit": 1}
    if args.market_id:
        params["id"] = args.market_id
    if args.slug:
        params["slug"] = args.slug
    if len(params) == 1:
        raise SystemExit("missing required args: --market-id, --slug, --source-url, or --fixture-json")
    return f"{GAMMA_MARKETS_URL}?{urlencode(params)}"


def load_metadata(args: argparse.Namespace) -> tuple[Any, str | None]:
    if args.fixture_json:
        return json.loads(args.fixture_json.read_text(encoding="utf-8")), None
    return fetch_json(args.source_url or build_markets_url(args))


def ingest_metadata(payload: Any) -> dict[str, Any]:
    market = extract_market(payload)
    result = derive_resolution(market)
    resolutions: dict[str, str] = {}
    skipped: list[dict[str, Any]] = []
    if result["status"] == "resolved":
        if not result.get("market_id"):
            skipped.append({**result, "status": "skipped", "skip_reason": "missing_market_id"})
        else:
            resolutions[str(result["market_id"])] = result["winning_side"]
    else:
        skipped.append(result)
    return {"resolutions": resolutions, "skipped": skipped, "source_market_id": result.get("market_id")}


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def base_market(**overrides: Any) -> dict[str, Any]:
    market = {
        "id": "market-up",
        "closed": True,
        "outcomes": '["Up", "Down"]',
        "outcomePrices": '["1", "0"]',
    }
    market.update(overrides)
    return market


def self_check() -> Path:
    output_dir = Path(tempfile.gettempdir()) / "polybot_phase11_resolution_ingestion"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "resolution_map.json"
    batch_output = output_dir / "batch_summary.json"
    supervisor_jsonl = output_dir / "supervisor.jsonl"
    runner_jsonl = output_dir / "session_1_market-up.jsonl"

    cases = [
        (base_market(), "resolved", "UP"),
        (base_market(id="market-down", outcomePrices=["0", "1"]), "resolved", "DOWN"),
        (base_market(id="market-open", closed=False), "not_closed", None),
        (base_market(id="market-missing-outcomes", outcomes=None), "missing_outcomes", None),
        (base_market(id="market-many", outcomes='["Up", "Down", "Flat"]', outcomePrices='["1", "0", "0"]'), "non_binary_market", None),
        (base_market(id="market-missing-price", outcomePrices=None), "missing_outcome_prices", None),
        (base_market(id="market-invalid-price", outcomePrices='["won", "lost"]'), "invalid_outcome_prices", None),
        (base_market(id="market-ambiguous", outcomePrices=["1", "1"]), "ambiguous_terminal_prices", None),
        (base_market(id="market-half", outcomePrices=["0.5", "0.5"]), "fifty_fifty_resolution", None),
        (base_market(id="market-unclear", outcomes='["Yes", "No"]'), "unmapped_outcome", None),
        (base_market(id="market-disputed", umaResolutionStatus="disputed"), "disputed_resolution_status", None),
        (base_market(id="market-proposed", umaResolutionStatus="proposed"), "unresolved_resolution_status", None),
    ]
    results = [derive_resolution(market) for market, _reason, _side in cases]
    for result, (_market, reason, side) in zip(results, cases):
        if side:
            assert result["status"] == "resolved"
            assert result["winning_side"] == side
        else:
            assert result["skip_reason"] == reason

    write_json(output, ingest_metadata(base_market()))

    runner_jsonl.write_text(
        "\n".join(
            json.dumps(record, sort_keys=True)
            for record in [
                {"record_type": "signal_record", "record": {"signal": "UP"}},
                {"record_type": "paper_trade_record", "record": {"signal": "UP", "stake": 9.0, "shares": 20.0}},
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    supervisor_jsonl.write_text(
        json.dumps({"record_type": "session_runner_finished", "session": {"market_id": "market-up"}, "runner_output": str(runner_jsonl)}, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    batch_summary = batch_close(supervisor_jsonl, load_resolution_map(output))
    write_json(batch_output, batch_summary)
    assert batch_summary["sessions_closed"] == 1
    assert batch_summary["aggregate_tradable_paper_pnl"] == 11.0
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Conservatively derive a Phase 10 resolution map from closed market metadata.")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--market-id")
    parser.add_argument("--slug")
    parser.add_argument("--source-url")
    parser.add_argument("--fixture-json", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--raw-output", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.self_check:
        output = self_check()
        print(json.dumps({"self_check": "passed", "output": str(output)}, sort_keys=True))
        return 0

    if args.output is None:
        raise SystemExit("missing required args: --output")
    payload, _source_timestamp = load_metadata(args)
    market = extract_market(payload)
    summary = ingest_metadata(market)
    write_json(args.output, summary)
    if args.raw_output:
        write_json(args.raw_output, market)
    print(json.dumps({"output": str(args.output), "resolved": bool(summary["resolutions"]), "skipped": summary["skipped"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
