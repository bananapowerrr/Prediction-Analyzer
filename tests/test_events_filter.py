"""Tests for data.events — Prediction Analyzer event normalization and filtering."""

from __future__ import annotations

from data.events import (
    normalize_event,
    parse_events,
    filter_events_by_type,
    MarketQuote,
    BlockchainEvent,
    MarketEvent,
    ChainMetric,
)


class TestNormalizeEvent:
    def test_full_raw_snake_case_keys(self):
        raw = {"id": 1, "event_type": "trade", "timestamp": 1234.5}
        assert normalize_event(raw) == {"id": 1, "type": "trade", "ts": 1234.5}

    def test_full_raw_short_keys(self):
        raw = {"id": 1, "type": "trade", "ts": 1234.5}
        assert normalize_event(raw) == {"id": 1, "type": "trade", "ts": 1234.5}

    def test_event_type_precedence_over_type(self):
        raw = {"id": 1, "type": "fallback", "event_type": "trade", "ts": 1.0}
        assert normalize_event(raw)["type"] == "trade"

    def test_empty_event_type_falls_back_to_type(self):
        raw = {"id": 1, "event_type": "", "type": "quote", "ts": 1.0}
        assert normalize_event(raw)["type"] == "quote"

    def test_timestamp_preferred_over_ts(self):
        raw = {"id": 1, "type": "trade", "timestamp": 99.0, "ts": 1.0}
        assert normalize_event(raw)["ts"] == 99.0

    def test_missing_keys_yield_none(self):
        assert normalize_event({}) == {"id": None, "type": None, "ts": None}

    def test_partial_keys(self):
        assert normalize_event({"id": 5}) == {"id": 5, "type": None, "ts": None}

    def test_preserves_extra_values(self):
        result = normalize_event({"id": 1, "type": "trade", "ts": 1.0})
        assert set(result.keys()) == {"id", "type", "ts"}


class TestParseEvents:
    def test_empty_list(self):
        assert parse_events([]) == []

    def test_normalizes_dict_items(self):
        items = [
            {"id": 1, "event_type": "trade", "timestamp": 1.0},
            {"id": 2, "type": "quote", "ts": 2.0},
        ]
        result = parse_events(items)
        assert result == [
            {"id": 1, "type": "trade", "ts": 1.0},
            {"id": 2, "type": "quote", "ts": 2.0},
        ]

    def test_passes_through_non_dict_items(self):
        items = [1, "raw", None, ["nested"]]
        assert parse_events(items) == items

    def test_mixed_items(self):
        items = [{"id": 1, "type": "trade", "ts": 1.0}, "plain"]
        result = parse_events(items)
        assert result == [{"id": 1, "type": "trade", "ts": 1.0}, "plain"]

    def test_empty_dict_is_normalized(self):
        assert parse_events([{}]) == [{"id": None, "type": None, "ts": None}]


class TestFilterEventsByType:
    def test_filters_matching_type(self):
        events = [
            {"type": "trade", "id": 1},
            {"type": "quote", "id": 2},
            {"type": "trade", "id": 3},
        ]
        result = filter_events_by_type(events, "trade")
        assert result == [{"type": "trade", "id": 1}, {"type": "trade", "id": 3}]

    def test_returns_empty_when_no_match(self):
        events = [{"type": "quote", "id": 1}]
        assert filter_events_by_type(events, "trade") == []

    def test_returns_empty_for_empty_input(self):
        assert filter_events_by_type([], "trade") == []

    def test_skips_events_without_type(self):
        events = [{"id": 1}, {"type": "trade", "id": 2}]
        assert filter_events_by_type(events, "trade") == [{"type": "trade", "id": 2}]


class TestEventModels:
    def test_market_quote_defaults(self):
        quote = MarketQuote(market_id="m1", bid=0.5, ask=0.6)
        assert quote.market_id == "m1"
        assert quote.bid == 0.5
        assert quote.ask == 0.6
        assert isinstance(quote.timestamp, float)

    def test_blockchain_event_defaults(self):
        event = BlockchainEvent(event_type="transfer", data={"amount": 1})
        assert event.event_type == "transfer"
        assert event.data == {"amount": 1}
        assert isinstance(event.timestamp, float)

    def test_market_event(self):
        event = MarketEvent(symbol="BTC", timestamp=1.0, price=100.0, volume=10.0, source="polymarket")
        assert event.source == "polymarket"

    def test_chain_metric_defaults(self):
        metric = ChainMetric(metric_name="tvl", value=12.5)
        assert metric.metric_name == "tvl"
        assert metric.value == 12.5
        assert isinstance(metric.timestamp, float)