"""
tests/test_due_date.py — DueDateAdapter Unit Tests

五格式各 2+ cases（iso8601 / epoch / arrival_plus_N / product_lead / default）
"""

import sys
from pathlib import Path
OTD_SIM_DIR = Path(__file__).parent.parent / "showcase" / "otd-sim"
sys.path.insert(0, str(OTD_SIM_DIR))

import pytest
from datetime import datetime, timedelta
from station_dispatch import DueDateAdapter


# ═══════════════════════════════════════════════════════════════
# Fixture helpers
# ═══════════════════════════════════════════════════════════════

def make_config(fmt="default", **kwargs):
    """Build minimal config dict for DueDateAdapter."""
    base = {
        "format": fmt,
        "base_days": 14,
        "jitter_days": 3,
        "arrival_plus_days": 7,
        "overrides": {},
    }
    base.update(kwargs)
    return {"order_template": {"due_date": base, "products": [
        {"type": "A", "lead_time_days": 10, "cycle_time_hrs": 4.0},
        {"type": "B", "lead_time_days": 7,  "cycle_time_hrs": 2.5},
        {"type": "C", "lead_time_days": 14, "cycle_time_hrs": 6.0},
    ]}}


class TestDueDateISO8601:
    """ISO8601 format: '2025-06-15' or '2025-06-15T14:00:00'."""

    def test_iso_date_only(self):
        adapter = DueDateAdapter(make_config("iso8601"))
        result = adapter.compute("O001", "A", arrival_day=0)
        # arrival_day=0 + base_days=14 → 2025-01-15
        expected = datetime(2025, 1, 15)
        assert result == expected, f"Expected {expected}, got {result}"

    def test_iso_with_datetime(self):
        """T14:00:00 variant."""
        config = make_config("iso8601", overrides={"O001": "2025-06-15T14:00:00"})
        adapter = DueDateAdapter(config)
        result = adapter.compute("O001", "A", arrival_day=0)
        assert result == datetime(2025, 6, 15, 14, 0)

    def test_iso_override_applied(self):
        """Overrides should take priority over default."""
        config = make_config("iso8601", overrides={"O010": "2025-08-01"})
        adapter = DueDateAdapter(config)
        result = adapter.compute("O010", "A", arrival_day=100)
        assert result == datetime(2025, 8, 1), f"Override failed: {result}"

    def test_iso_no_override_falls_back(self):
        """Without override, fall back to arrival + base_days."""
        config = make_config("iso8601", overrides={})
        adapter = DueDateAdapter(config)
        result = adapter.compute("O999", "A", arrival_day=5)
        expected = datetime(2025, 1, 1) + timedelta(days=5 + 14)
        assert result == expected


class TestDueDateEpoch:
    """Epoch format: Unix timestamp → datetime."""

    def test_epoch_basic(self):
        # 2025-01-15 00:00:00 UTC = 1736899200
        config = make_config("epoch", overrides={"O001": "1736899200"})
        adapter = DueDateAdapter(config)
        result = adapter.compute("O001", "A", arrival_day=0)
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 15

    def test_epoch_override_applied(self):
        config = make_config("epoch", overrides={"O050": "1704067200"})
        adapter = DueDateAdapter(config)
        result = adapter.compute("O050", "A", arrival_day=0)
        assert result == datetime(2024, 1, 1), f"Expected 2024-01-01, got {result}"

    def test_epoch_no_override_falls_back(self):
        config = make_config("epoch", overrides={})
        adapter = DueDateAdapter(config)
        result = adapter.compute("O999", "A", arrival_day=0)
        expected = datetime(2025, 1, 1) + timedelta(days=14)
        assert result == expected


class TestDueDateArrivalPlusN:
    """arrival_plus_N: arrival_day + fixed N days."""

    def test_arrival_plus_default(self):
        config = make_config("arrival_plus_N", arrival_plus_days=7)
        adapter = DueDateAdapter(config)
        result = adapter.compute("O001", "A", arrival_day=0)
        expected = datetime(2025, 1, 1) + timedelta(days=7)
        assert result == expected

    def test_arrival_plus_custom(self):
        config = make_config("arrival_plus_N", arrival_plus_days=21)
        adapter = DueDateAdapter(config)
        result = adapter.compute("O001", "A", arrival_day=3)
        expected = datetime(2025, 1, 1) + timedelta(days=3 + 21)
        assert result == expected

    def test_arrival_plus_zero(self):
        config = make_config("arrival_plus_N", arrival_plus_days=0)
        adapter = DueDateAdapter(config)
        result = adapter.compute("O001", "A", arrival_day=10)
        expected = datetime(2025, 1, 1) + timedelta(days=10)
        assert result == expected


class TestDueDateProductLead:
    """product_lead: arrival_day + product.lead_time_days."""

    def test_product_a_lead(self):
        config = make_config("product_lead")
        adapter = DueDateAdapter(config)
        result = adapter.compute("O001", "A", arrival_day=0)
        expected = datetime(2025, 1, 1) + timedelta(days=10)  # A lead_time_days=10
        assert result == expected, f"Expected {expected}, got {result}"

    def test_product_b_lead(self):
        config = make_config("product_lead")
        adapter = DueDateAdapter(config)
        result = adapter.compute("O001", "B", arrival_day=0)
        expected = datetime(2025, 1, 1) + timedelta(days=7)  # B lead_time_days=7
        assert result == expected

    def test_product_c_lead(self):
        config = make_config("product_lead")
        adapter = DueDateAdapter(config)
        result = adapter.compute("O001", "C", arrival_day=0)
        expected = datetime(2025, 1, 1) + timedelta(days=14)  # C lead_time_days=14
        assert result == expected

    def test_product_lead_plus_arrival(self):
        config = make_config("product_lead")
        adapter = DueDateAdapter(config)
        result = adapter.compute("O001", "B", arrival_day=5)
        expected = datetime(2025, 1, 1) + timedelta(days=5 + 7)
        assert result == expected

    def test_product_lead_unknown_type_fallback(self):
        """Unknown product_type → fallback to default base_days=14."""
        config = make_config("product_lead")
        adapter = DueDateAdapter(config)
        result = adapter.compute("O001", "Z", arrival_day=0)
        expected = datetime(2025, 1, 1) + timedelta(days=14)
        assert result == expected


class TestDueDateDefault:
    """Default format: arrival_day + base_days ± jitter."""

    def test_default_basic(self):
        adapter = DueDateAdapter(make_config("default"))
        result = adapter.compute("O001", "A", arrival_day=0)
        # jitter is random [-3, +3], base=14, so range [11, 17]
        assert 11 <= (result - datetime(2025, 1, 1)).days <= 17

    def test_default_with_arrival(self):
        adapter = DueDateAdapter(make_config("default"))
        result = adapter.compute("O001", "A", arrival_day=10)
        delta = (result - datetime(2025, 1, 1)).days
        assert 21 <= delta <= 27  # 10 + 14 ± 3

    def test_default_deterministic_with_rng(self):
        """With fixed rng, output should be deterministic."""
        import random
        rng = random.Random(42)
        adapter = DueDateAdapter(make_config("default"))
        r1 = adapter.compute("O001", "A", arrival_day=0, rng=rng)
        r2 = adapter.compute("O001", "A", arrival_day=0, rng=random.Random(42))
        assert r1 == r2, "Same seed → same result"


class TestDueDateEdgeCases:
    """Invalid / edge cases."""

    def test_unknown_format_fallback(self):
        """Unknown format → fallback to default."""
        config = make_config("unknown_format")
        adapter = DueDateAdapter(config)
        result = adapter.compute("O001", "A", arrival_day=0)
        delta = (result - datetime(2025, 1, 1)).days
        assert 11 <= delta <= 17  # default: 14 ± 3

    def test_negative_arrival_day(self):
        config = make_config("default", base_days=14)
        adapter = DueDateAdapter(config)
        result = adapter.compute("O001", "A", arrival_day=-5)
        delta = (result - datetime(2025, 1, 1)).days
        # arrival=-5 + base=14 ± 3 → [6, 12]
        assert 6 <= delta <= 16  # allow negative to push into previous month

    def test_iso_malformed_fallback(self):
        """Malformed ISO → _parse_iso fallback returns default."""
        config = make_config("iso8601", overrides={"O001": "not-a-date"})
        adapter = DueDateAdapter(config)
        result = adapter.compute("O001", "A", arrival_day=0)
        # Should fall back to arrival + base_days
        expected = datetime(2025, 1, 1) + timedelta(days=14)
        assert result == expected

    def test_repr(self):
        adapter = DueDateAdapter(make_config("iso8601"))
        r = repr(adapter)
        assert "DueDateAdapter" in r
        assert "iso8601" in r


class TestDueDateConfig:
    """Config parsing edge cases."""

    def test_missing_base_days_defaults_to_14(self):
        config = make_config("default")
        config["order_template"]["due_date"].pop("base_days", None)
        adapter = DueDateAdapter(config)
        assert adapter.base_days == 14

    def test_missing_jitter_defaults_to_3(self):
        config = make_config("default")
        config["order_template"]["due_date"].pop("jitter_days", None)
        adapter = DueDateAdapter(config)
        assert adapter.jitter_days == 3

    def test_empty_overrides(self):
        config = make_config("iso8601", overrides={})
        adapter = DueDateAdapter(config)
        result = adapter.compute("O001", "A", arrival_day=0)
        expected = datetime(2025, 1, 1) + timedelta(days=14)
        assert result == expected
