from __future__ import annotations

import argparse
import json
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


GAMMA_EVENTS_URL = "https://gamma-api.polymarket.com/events"
GAMMA_MARKETS_URL = "https://gamma-api.polymarket.com/markets"
GAMMA_PUBLIC_SEARCH_URL = "https://gamma-api.polymarket.com/public-search"
USER_AGENT = "PolyBot public discovery"
POLYMARKET_OPEN_PRICE_KEYS = ("openPrice", "open_price", "referencePrice", "reference_price", "targetPrice", "target_price")


@dataclass(frozen=True)
class SessionConfig:
    market_id: str
    event_id: str | None
    market_slug: str | None
    event_slug: str | None
    question: str
    market_start_time: str
    market_end_time: str
    up_token_id: str
    down_token_id: str
    selected_side_labels: dict[str, str]
    discovery_source_timestamp: str | None
    local_timestamp: str
    paper_stake: float | None = None
    caller_supplied_p_hat: float | None = None
    polymarket_open_price: float | None = None
    polymarket_open_price_source: str | None = None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_jsonish(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def first_text(item: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = item.get(key)
        if value:
            return str(value)
    return None


def truthy(value: Any) -> bool:
    return value is True or (isinstance(value, str) and value.lower() == "true")


def falsey(value: Any) -> bool:
    return value is False or (isinstance(value, str) and value.lower() == "false")


def polymarket_open_price(market: dict[str, Any]) -> tuple[float | None, str | None]:
    for key in POLYMARKET_OPEN_PRICE_KEYS:
        value = market.get(key)
        try:
            price = float(value)
        except (TypeError, ValueError):
            continue
        if price > 0:
            return price, key
    return None, None


def extract_markets(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list) and any(isinstance(item, list) or (isinstance(item, dict) and ("data" in item or "events" in item)) for item in payload):
        markets: list[dict[str, Any]] = []
        for page in payload:
            markets.extend(extract_markets(page))
        return markets
    data = payload.get("events", payload.get("data", payload)) if isinstance(payload, dict) else payload
    markets: list[dict[str, Any]] = []
    for item in data if isinstance(data, list) else []:
        nested = item.get("markets") if isinstance(item, dict) else None
        if isinstance(nested, list):
            for market in nested:
                if isinstance(market, dict):
                    merged = {**market, "_event": item}
                    markets.append(merged)
        elif isinstance(item, dict):
            markets.append(item)
    return markets


def market_count(payload: Any) -> int:
    if isinstance(payload, list) and any(isinstance(item, list) or (isinstance(item, dict) and ("data" in item or "events" in item)) for item in payload):
        return sum(market_count(page) for page in payload)
    data = payload.get("events", payload.get("data", payload)) if isinstance(payload, dict) else payload
    if not isinstance(data, list):
        return 0
    return sum(len(item.get("markets", [])) if isinstance(item, dict) and isinstance(item.get("markets"), list) else 1 for item in data)


def market_times(market: dict[str, Any]) -> tuple[datetime | None, datetime | None]:
    start = first_text(market, ("eventStartTime", "startTime", "startDate", "startDateIso", "start_date"))
    end = first_text(market, ("endTime", "endDate", "endDateIso", "end_date"))
    try:
        return (parse_datetime(start) if start else None, parse_datetime(end) if end else None)
    except ValueError:
        return None, None


def token_mapping(market: dict[str, Any]) -> tuple[str | None, str | None, dict[str, str] | None]:
    tokens = parse_jsonish(market.get("tokens"))
    if isinstance(tokens, list):
        by_label = {str(token.get("outcome", "")).upper(): str(token.get("token_id") or token.get("tokenId") or "") for token in tokens}
        if by_label.get("UP") and by_label.get("DOWN"):
            return by_label["UP"], by_label["DOWN"], {"UP": "UP", "DOWN": "DOWN"}

    outcomes = parse_jsonish(market.get("outcomes"))
    token_ids = parse_jsonish(market.get("clobTokenIds") or market.get("tokenIds"))
    if not isinstance(outcomes, list) or not isinstance(token_ids, list) or len(outcomes) != len(token_ids):
        return None, None, None

    mapped: dict[str, str] = {}
    labels: dict[str, str] = {}
    for outcome, token_id in zip(outcomes, token_ids):
        label = str(outcome).strip()
        upper = label.upper()
        if upper in ("UP", "DOWN"):
            mapped[upper] = str(token_id)
            labels[upper] = label
    if mapped.get("UP") and mapped.get("DOWN"):
        return mapped["UP"], mapped["DOWN"], labels
    return None, None, None


def is_active_open(market: dict[str, Any]) -> bool:
    event = market.get("_event") if isinstance(market.get("_event"), dict) else {}
    active = market.get("active", event.get("active"))
    closed = market.get("closed", event.get("closed"))
    accepting = market.get("acceptingOrders", market.get("accepting_orders", True))
    archived = market.get("archived", event.get("archived", False))
    return truthy(active) and falsey(closed) and truthy(accepting) and falsey(archived)


def validate_candidate(market: dict[str, Any]) -> tuple[SessionConfig | None, str | None]:
    event = market.get("_event") if isinstance(market.get("_event"), dict) else {}
    question = first_text(market, ("question", "title", "description")) or first_text(event, ("title", "question")) or ""
    identity_text = f"{question} {first_text(event, ('title', 'slug')) or ''}".lower()
    if "btc" not in identity_text and "bitcoin" not in identity_text:
        return None, "not_btc"

    start, end = market_times(market)
    if start is None or end is None:
        return None, "missing_start_or_end_time"
    if end - start != timedelta(minutes=15):
        return None, "not_15m"
    if not is_active_open(market):
        return None, "not_active_open"

    up_token_id, down_token_id, labels = token_mapping(market)
    if not up_token_id or not down_token_id or not labels:
        return None, "unclear_up_down_mapping"

    market_id = first_text(market, ("id", "conditionId", "questionID", "questionId"))
    if not market_id:
        return None, "missing_market_id"

    open_price, open_price_source = polymarket_open_price(market)
    return (
        SessionConfig(
            market_id=market_id,
            event_id=first_text(event, ("id", "eventId")),
            market_slug=first_text(market, ("slug",)),
            event_slug=first_text(event, ("slug",)),
            question=question,
            market_start_time=start.isoformat(),
            market_end_time=end.isoformat(),
            up_token_id=up_token_id,
            down_token_id=down_token_id,
            selected_side_labels=labels,
            discovery_source_timestamp=None,
            local_timestamp=utc_now().isoformat(),
            polymarket_open_price=open_price,
            polymarket_open_price_source=open_price_source,
        ),
        None,
    )


def candidate_snapshot(market: dict[str, Any], reason: str | None = None) -> dict[str, Any]:
    event = market.get("_event") if isinstance(market.get("_event"), dict) else {}
    up_token_id, down_token_id, _labels = token_mapping(market)
    start, end = market_times(market)
    return {
        "question": first_text(market, ("question", "title", "description")) or first_text(event, ("title", "question")),
        "market_slug": first_text(market, ("slug",)),
        "event_slug": first_text(event, ("slug",)),
        "start": start.isoformat() if start else None,
        "end": end.isoformat() if end else None,
        "has_up_down_mapping": bool(up_token_id and down_token_id),
        "reason": reason,
    }


def select_session(
    payload: Any,
    now: datetime,
    lookahead_minutes: int,
    mode: str,
    paper_stake: float | None = None,
    caller_supplied_p_hat: float | None = None,
    source_timestamp: str | None = None,
    diagnostics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    window_end = now + timedelta(minutes=lookahead_minutes)
    candidates: list[SessionConfig] = []
    skip_reasons: dict[str, int] = {}
    snapshots: list[dict[str, Any]] = []

    for market in extract_markets(payload):
        config, reason = validate_candidate(market)
        if reason:
            skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
            if len(snapshots) < 10:
                snapshots.append(candidate_snapshot(market, reason))
            continue
        assert config is not None
        start = parse_datetime(config.market_start_time)
        end = parse_datetime(config.market_end_time)
        in_window = start <= now < end if mode == "current" else now < start <= window_end
        if in_window:
            if len(snapshots) < 10:
                snapshots.append(candidate_snapshot(market, "candidate_in_window"))
            candidates.append(
                config.__class__(
                    **{
                        **asdict(config),
                        "discovery_source_timestamp": source_timestamp,
                        "paper_stake": paper_stake,
                        "caller_supplied_p_hat": caller_supplied_p_hat,
                    }
                )
            )
        else:
            reason = f"valid_but_outside_{mode}_window"
            skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
            if len(snapshots) < 10:
                snapshots.append(candidate_snapshot(market, reason))

    if mode == "next" and candidates:
        earliest = min(parse_datetime(candidate.market_start_time) for candidate in candidates)
        candidates = [candidate for candidate in candidates if parse_datetime(candidate.market_start_time) == earliest]

    if len(candidates) == 1:
        result = {"selection": asdict(candidates[0]), "skip_reason": None}
        if diagnostics is not None:
            result["diagnostics"] = {**diagnostics, "validation_skip_reasons": skip_reasons, "top_candidate_snapshots": snapshots, "final_skip_reason": None}
        return result
    reason = "no_valid_candidate" if not candidates else "ambiguous_candidates"
    result = {
        "selection": None,
        "skip_reason": reason,
        "candidate_count": len(candidates),
        "validation_skip_reasons": skip_reasons,
        "local_timestamp": utc_now().isoformat(),
    }
    if diagnostics is not None:
        result["diagnostics"] = {**diagnostics, "validation_skip_reasons": skip_reasons, "top_candidate_snapshots": snapshots, "final_skip_reason": reason}
    return result


def plan_rotation(
    current_session: dict[str, Any],
    payload: Any,
    now: datetime,
    lookahead_minutes: int,
) -> dict[str, Any]:
    result = select_session(payload, now, lookahead_minutes, "next")
    if result["selection"] and result["selection"]["market_id"] == current_session.get("market_id"):
        return {"selection": None, "skip_reason": "next_matches_current", "local_timestamp": utc_now().isoformat()}
    return result


def build_source_url(base_url: str, args: argparse.Namespace, offset: int = 0) -> str:
    params: dict[str, str | int] = {"active": "true", "closed": "false", "limit": args.limit, "offset": offset}
    if args.tag_id:
        params["tag_id"] = args.tag_id
        params["related_tags"] = "true"
    if args.slug:
        params["slug"] = args.slug
    return f"{base_url}?{urlencode(params)}"


def build_events_url(args: argparse.Namespace) -> str:
    return build_source_url(GAMMA_EVENTS_URL, args)


def build_markets_url(args: argparse.Namespace) -> str:
    return build_source_url(GAMMA_MARKETS_URL, args)


def fetch_json(url: str) -> tuple[Any, str | None]:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=10) as response:
        source_timestamp = response.headers.get("Date")
        return json.loads(response.read().decode("utf-8")), source_timestamp


def discovery_sources(args: argparse.Namespace) -> list[tuple[str, str, int]]:
    if args.source_url:
        return [("source_url", args.source_url, 0)]
    if args.search_query:
        return [
            (
                "search",
                f"{GAMMA_PUBLIC_SEARCH_URL}?{urlencode({'q': args.search_query, 'events_status': 'active', 'limit_per_type': args.limit, 'page': page + 1, 'keep_closed_markets': 0})}",
                page + 1,
            )
            for page in range(args.max_pages)
        ]
    kinds = ("events", "markets") if args.source_kind == "both" else (args.source_kind,)
    sources: list[tuple[str, str, int]] = []
    for kind in kinds:
        base_url = GAMMA_EVENTS_URL if kind == "events" else GAMMA_MARKETS_URL
        for page in range(args.max_pages):
            offset = page * args.limit
            sources.append((kind, build_source_url(base_url, args, offset), offset))
    return sources


def discover_session(
    args: argparse.Namespace,
    now: datetime,
    fetcher: Any = fetch_json,
) -> dict[str, Any]:
    payloads: list[Any] = []
    source_timestamps: list[str | None] = []
    diagnostics: dict[str, Any] = {
        "sources_tried": [],
        "source_timestamps": [],
        "pages_fetched": 0,
        "offsets": [],
        "events_count": 0,
        "markets_count": 0,
    }
    exhausted: set[str] = set()
    for kind, url, offset in discovery_sources(args):
        if kind in exhausted:
            continue
        payload, source_timestamp = fetcher(url)
        payloads.append(payload)
        source_timestamps.append(source_timestamp)
        data = payload.get("events", payload.get("data", payload)) if isinstance(payload, dict) else payload
        count = len(data) if isinstance(data, list) else 0
        diagnostics["sources_tried"].append({"kind": kind, "url": url, "count": count})
        diagnostics["source_timestamps"].append(source_timestamp)
        diagnostics["pages_fetched"] += 1
        diagnostics["offsets"].append(offset)
        if kind in ("events", "search"):
            diagnostics["events_count"] += count
        else:
            diagnostics["markets_count"] += market_count(payload)
        if count < args.limit or args.source_url:
            exhausted.add(kind)
    result = select_session(
        payloads,
        now,
        args.lookahead_minutes,
        args.mode,
        paper_stake=args.paper_stake,
        caller_supplied_p_hat=args.p_hat,
        source_timestamp=next((stamp for stamp in source_timestamps if stamp), None),
        diagnostics=diagnostics,
    )
    return result


def load_payload(args: argparse.Namespace) -> tuple[Any, str | None]:
    if args.input_json:
        return json.loads(args.input_json.read_text(encoding="utf-8")), None
    return fetch_json(args.source_url or build_events_url(args))


def sample_payload() -> list[dict[str, Any]]:
    return [
        {
            "id": "event-current",
            "slug": "btc-updown-current",
            "title": "Bitcoin Up or Down - current",
            "active": True,
            "closed": False,
            "markets": [
                {
                    "id": "market-current",
                    "slug": "btc-15m-current",
                    "question": "Bitcoin Up or Down - current",
                    "active": True,
                    "closed": False,
                    "acceptingOrders": True,
                    "startDate": "2026-07-06T12:00:00+00:00",
                    "endDate": "2026-07-06T12:15:00+00:00",
                    "outcomes": '["Up", "Down"]',
                    "clobTokenIds": '["up-token-current", "down-token-current"]',
                    "openPrice": "100.05",
                }
            ],
        },
        {
            "id": "event-next",
            "slug": "btc-updown-next",
            "title": "Bitcoin Up or Down - next",
            "active": True,
            "closed": False,
            "markets": [
                {
                    "id": "market-next",
                    "slug": "btc-15m-next",
                    "question": "Bitcoin Up or Down - next",
                    "active": True,
                    "closed": False,
                    "acceptingOrders": True,
                    "startDate": "2026-07-06T12:15:00+00:00",
                    "endDate": "2026-07-06T12:30:00+00:00",
                    "outcomes": '["Up", "Down"]',
                    "clobTokenIds": '["up-token-next", "down-token-next"]',
                }
            ],
        },
    ]


def self_check() -> Path:
    output = Path(tempfile.gettempdir()) / "polybot_phase6_session_config.json"
    now = datetime(2026, 7, 6, 12, 5, tzinfo=timezone.utc)
    current = select_session(sample_payload(), now, 20, "current", paper_stake=9.0, caller_supplied_p_hat=0.55)
    next_result = select_session(sample_payload(), now, 20, "next")
    next_with_extra_future = select_session(
        sample_payload()
        + [
            {
                "id": "event-later",
                "slug": "btc-updown-later",
                "title": "Bitcoin Up or Down - later",
                "active": True,
                "closed": False,
                "markets": [
                    {
                        "id": "market-later",
                        "slug": "btc-15m-later",
                        "question": "Bitcoin Up or Down - later",
                        "active": True,
                        "closed": False,
                        "acceptingOrders": True,
                        "startDate": "2026-07-06T12:20:00+00:00",
                        "endDate": "2026-07-06T12:35:00+00:00",
                        "outcomes": '["Up", "Down"]',
                        "clobTokenIds": '["up-token-later", "down-token-later"]',
                    }
                ],
            }
        ],
        now,
        40,
        "next",
    )
    ambiguous = select_session(sample_payload() + sample_payload()[:1], now, 20, "current")
    missing_mapping = select_session(
        [
            {
                "id": "event-bad",
                "title": "BTC 15m",
                "active": True,
                "closed": False,
                "markets": [
                    {
                        "id": "market-bad",
                        "question": "BTC 15m",
                        "active": True,
                        "closed": False,
                        "startDate": "2026-07-06T12:00:00+00:00",
                        "endDate": "2026-07-06T12:15:00+00:00",
                        "outcomes": '["Yes", "No"]',
                        "clobTokenIds": '["yes-token", "no-token"]',
                    }
                ],
            }
        ],
        now,
        20,
        "current",
    )
    rotation = plan_rotation(current["selection"], sample_payload(), now, 20)
    flat_markets = [
        {
            "id": "flat-current",
            "slug": "btc-15m-flat",
            "question": "BTC Up or Down flat",
            "active": True,
            "closed": False,
            "acceptingOrders": True,
            "startDate": "2026-07-06T12:00:00+00:00",
            "endDate": "2026-07-06T12:15:00+00:00",
            "outcomes": '["UP", "DOWN"]',
            "clobTokenIds": '["flat-up", "flat-down"]',
        }
    ]
    flat_result = select_session(flat_markets, now, 20, "current")
    gamma_15m_result = select_session(
        [
            {
                "id": "gamma-current",
                "slug": "btc-updown-15m-gamma",
                "question": "Bitcoin Up or Down - gamma",
                "active": True,
                "closed": False,
                "acceptingOrders": True,
                "eventStartTime": "2026-07-06T12:00:00Z",
                "startDate": "2026-07-05T02:23:10.40683Z",
                "endDate": "2026-07-06T12:15:00Z",
                "outcomes": '["Up", "Down"]',
                "clobTokenIds": '["gamma-up", "gamma-down"]',
            }
        ],
        now,
        20,
        "current",
    )
    no_candidate = select_session([{"id": "not-btc", "question": "ETH Up or Down"}], now, 20, "current", diagnostics={"sources_tried": ["fixture"]})
    search_result = select_session({"events": sample_payload()}, now, 20, "current")

    page_payloads = [
        [{"id": "eth", "question": "ETH Up or Down", "active": True, "closed": False}],
        sample_payload(),
    ]
    fetch_calls: list[str] = []

    def fixture_fetcher(url: str) -> tuple[Any, str]:
        fetch_calls.append(url)
        return page_payloads[len(fetch_calls) - 1], f"fixture-date-{len(fetch_calls)}"

    page_args = argparse.Namespace(
        source_url=None,
        search_query=None,
        source_kind="events",
        tag_id=None,
        slug=None,
        limit=1,
        max_pages=2,
        lookahead_minutes=20,
        mode="current",
        paper_stake=None,
        p_hat=None,
    )
    paged = discover_session(page_args, now, fixture_fetcher)

    assert current["selection"]["market_id"] == "market-current"
    assert current["selection"]["up_token_id"] == "up-token-current"
    assert current["selection"]["down_token_id"] == "down-token-current"
    assert current["selection"]["polymarket_open_price"] == 100.05
    assert current["selection"]["polymarket_open_price_source"] == "openPrice"
    assert next_result["selection"]["market_id"] == "market-next"
    assert next_with_extra_future["selection"]["market_id"] == "market-next"
    assert rotation["selection"]["market_id"] == "market-next"
    assert ambiguous["skip_reason"] == "ambiguous_candidates"
    assert missing_mapping["skip_reason"] == "no_valid_candidate"
    assert missing_mapping["validation_skip_reasons"] == {"unclear_up_down_mapping": 1}
    assert flat_result["selection"]["market_id"] == "flat-current"
    assert gamma_15m_result["selection"]["market_id"] == "gamma-current"
    assert search_result["selection"]["market_id"] == "market-current"
    assert paged["selection"]["market_id"] == "market-current"
    assert paged["diagnostics"]["pages_fetched"] == 2
    assert "not_btc" in no_candidate["diagnostics"]["validation_skip_reasons"]
    assert no_candidate["diagnostics"]["top_candidate_snapshots"][0]["reason"] == "not_btc"

    output.write_text(json.dumps(current, sort_keys=True) + "\n", encoding="utf-8")
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Discover BTC 15m paper-runner sessions.")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--input-json", type=Path)
    parser.add_argument("--source-url")
    parser.add_argument("--search-query")
    parser.add_argument("--source-kind", choices=("events", "markets", "both"), default="both")
    parser.add_argument("--tag-id")
    parser.add_argument("--slug")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--max-pages", type=int, default=3)
    parser.add_argument("--now")
    parser.add_argument("--lookahead-minutes", type=int, default=30)
    parser.add_argument("--mode", choices=("current", "next"), default="current")
    parser.add_argument("--current-session-json", type=Path)
    parser.add_argument("--paper-stake", type=float)
    parser.add_argument("--p-hat", type=float)
    parser.add_argument("--output", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.self_check:
        output = self_check()
        print(json.dumps({"self_check": "passed", "output": str(output)}, sort_keys=True))
        return 0

    if args.output is None:
        raise SystemExit("missing required args: --output")

    now = parse_datetime(args.now) if args.now else utc_now()
    if args.current_session_json:
        payload, source_timestamp = load_payload(args)
        current_session = json.loads(args.current_session_json.read_text(encoding="utf-8"))["selection"]
        result = plan_rotation(current_session, payload, now, args.lookahead_minutes)
    else:
        if args.input_json:
            payload, source_timestamp = load_payload(args)
            result = select_session(payload, now, args.lookahead_minutes, args.mode, paper_stake=args.paper_stake, caller_supplied_p_hat=args.p_hat, source_timestamp=source_timestamp, diagnostics={"sources_tried": [str(args.input_json)], "source_timestamps": [source_timestamp], "pages_fetched": 1, "offsets": [], "events_count": 0, "markets_count": market_count(payload)})
        else:
            result = discover_session(args, now)
    args.output.write_text(json.dumps(result, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "skip_reason": result.get("skip_reason")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
