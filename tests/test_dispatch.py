"""
tests/test_dispatch.py — Dispatch Policy Unit Tests

Tests: FIFO / EDD / SPT + edge cases
"""

import sys
from pathlib import Path
OTD_SIM_DIR = Path(__file__).parent.parent / "showcase" / "otd-sim"
sys.path.insert(0, str(OTD_SIM_DIR))

import pytest
from dispatch_policy import fifo, edd, spt, apply_policy, POLICIES, get_policy


# ═══════════════════════════════════════════════════════════════
# Fixture: WO factory
# ═══════════════════════════════════════════════════════════════

class FakeWO:
    """Minimal work-order mock with all attributes policies touch."""
    def __init__(self, wo_id, arrival_hour=0, due_date_hours=0, spt_score=0.0, product_type="A", qty_planned=100):
        self.wo_id = wo_id
        self._queue_entry_hour = arrival_hour
        self.due_date_hours = due_date_hours
        self.spt_score = spt_score
        self.product_type = product_type
        self.qty_planned = qty_planned

    def __repr__(self):
        return f"WO({self.wo_id}, arr={self._queue_entry_hour}, dd={self.due_date_hours}, spt={self.spt_score})"


def make_queue(*wo_list):
    return list(wo_list)


# ═══════════════════════════════════════════════════════════════
# FIFO tests
# ═══════════════════════════════════════════════════════════════

class TestFIFO:
    """FIFO: 先進先出，按 _queue_entry_hour 排序。"""

    def test_fifo_basic_order(self):
        wos = make_queue(
            FakeWO("W001", arrival_hour=5),
            FakeWO("W002", arrival_hour=0),
            FakeWO("W003", arrival_hour=3),
        )
        fifo(wos, {})
        assert [w.wo_id for w in wos] == ["W002", "W003", "W001"], "FIFO should sort by arrival_hour"

    def test_fifo_same_arrival(self):
        """Same arrival_hour → order unchanged (stable)."""
        wos = make_queue(
            FakeWO("W001", arrival_hour=0),
            FakeWO("W002", arrival_hour=0),
            FakeWO("W003", arrival_hour=0),
        )
        fifo(wos, {})
        ids = [w.wo_id for w in wos]
        assert ids == ["W001", "W002", "W003"], "Same arrival_hour should preserve order"

    def test_fifo_empty_queue(self):
        """Empty queue: no error."""
        fifo([], {})
        assert [] == []

    def test_fifo_single_item(self):
        wos = make_queue(FakeWO("W001", arrival_hour=10))
        fifo(wos, {})
        assert [w.wo_id for w in wos] == ["W001"]

    def test_fifo_zero_arrival_default(self):
        """_queue_entry_hour defaults to 0."""
        wos = make_queue(FakeWO("W001"), FakeWO("W002"), FakeWO("W003"))
        fifo(wos, {})
        assert [w.wo_id for w in wos] == ["W001", "W002", "W003"]


# ═══════════════════════════════════════════════════════════════
# EDD tests
# ═══════════════════════════════════════════════════════════════

class TestEDD:
    """EDD: Earliest due_date_hours first."""

    def test_edd_basic_order(self):
        wos = make_queue(
            FakeWO("W001", due_date_hours=48),
            FakeWO("W002", due_date_hours=24),
            FakeWO("W003", due_date_hours=72),
        )
        edd(wos, {})
        assert [w.wo_id for w in wos] == ["W002", "W001", "W003"], "EDD should sort by due_date_hours"

    def test_edd_tie_break(self):
        """Tie on due_date → tie-break by _queue_entry_hour."""
        wos = make_queue(
            FakeWO("W001", due_date_hours=24, arrival_hour=5),
            FakeWO("W002", due_date_hours=24, arrival_hour=0),
        )
        edd(wos, {})
        assert [w.wo_id for w in wos] == ["W002", "W001"], "Tie → FIFO tie-break"

    def test_edd_empty_queue(self):
        edd([], {})

    def test_edd_single_item(self):
        wos = make_queue(FakeWO("W001", due_date_hours=100))
        edd(wos, {})
        assert [w.wo_id for w in wos] == ["W001"]

    def test_edd_auto_compute(self):
        """If due_date_hours is 0, edd auto-computes from cycle_time_map."""
        wos = make_queue(
            FakeWO("W_A", product_type="B", qty_planned=50, arrival_hour=0),  # cycle 2.5h
            FakeWO("W_C", product_type="C", qty_planned=50, arrival_hour=0),  # cycle 6.0h
        )
        edd(wos, {"cycle_time_map": {"A": 4.0, "B": 2.5, "C": 6.0}})
        # B (2.5h) should have shorter due_date_hours → earlier in queue
        assert wos[0].wo_id == "W_A", f"W_A due_date={wos[0].due_date_hours}, W_C due_date={wos[1].due_date_hours}"


# ═══════════════════════════════════════════════════════════════
# SPT tests
# ═══════════════════════════════════════════════════════════════

class TestSPT:
    """SPT: Shortest Processing Time first."""

    def test_spt_basic_order(self):
        wos = make_queue(
            FakeWO("W001", product_type="C", qty_planned=100),  # cycle 6.0h → spt_score=6.0
            FakeWO("W002", product_type="B", qty_planned=100),  # cycle 2.5h → spt_score=2.5
            FakeWO("W003", product_type="A", qty_planned=100),  # cycle 4.0h → spt_score=4.0
        )
        spt(wos, {"cycle_time_map": {"A": 4.0, "B": 2.5, "C": 6.0}})
        assert [w.wo_id for w in wos] == ["W002", "W003", "W001"], f"SPT: {[w.wo_id for w in wos]}"

    def test_spt_smaller_qty_priority(self):
        """Smaller qty → shorter spt_score (even with same product_type)."""
        wos = make_queue(
            FakeWO("W001", product_type="A", qty_planned=200),  # spt=8.0
            FakeWO("W002", product_type="A", qty_planned=50),   # spt=2.0
        )
        spt(wos, {"cycle_time_map": {"A": 4.0}})
        assert [w.wo_id for w in wos] == ["W002", "W001"]

    def test_spt_empty_queue(self):
        spt([], {})

    def test_spt_single_item(self):
        wos = make_queue(FakeWO("W001"))
        spt(wos, {})
        assert [w.wo_id for w in wos] == ["W001"]

    def test_spt_tie_break(self):
        """Tie on spt_score → tie-break by _queue_entry_hour."""
        wos = make_queue(
            FakeWO("W001", product_type="A", qty_planned=100, arrival_hour=5),
            FakeWO("W002", product_type="A", qty_planned=100, arrival_hour=0),
        )
        spt(wos, {"cycle_time_map": {"A": 4.0}})
        assert [w.wo_id for w in wos] == ["W002", "W001"], "SPT tie → FIFO tie-break"


# ═══════════════════════════════════════════════════════════════
# Policy registry tests
# ═══════════════════════════════════════════════════════════════

class TestPolicyRegistry:
    """Policy registry: POLICIES dict, get_policy, apply_policy."""

    def test_policies_registered(self):
        assert "FIFO" in POLICIES
        assert "SPT" in POLICIES
        assert "EDD" in POLICIES

    def test_get_policy_known(self):
        assert get_policy("FIFO") is fifo
        assert get_policy("SPT") is spt
        assert get_policy("EDD") is edd

    def test_get_policy_unknown_fallback(self):
        assert get_policy("UNKNOWN") is fifo, "Unknown policy should fallback to FIFO"

    def test_get_policy_case_insensitive(self):
        assert get_policy("fifo") is fifo
        assert get_policy("Edd") is edd
        assert get_policy("SpT") is spt

    def test_apply_policy_fifo(self):
        wos = make_queue(FakeWO("W002"), FakeWO("W001"))
        apply_policy(wos, "FIFO", {})
        assert [w.wo_id for w in wos] == ["W002", "W001"]

    def test_apply_policy_spt(self):
        wos = make_queue(
            FakeWO("W001", product_type="C", qty_planned=100),
            FakeWO("W002", product_type="A", qty_planned=100),
        )
        apply_policy(wos, "SPT", {"cycle_time_map": {"A": 4.0, "B": 2.5, "C": 6.0}})
        assert [w.wo_id for w in wos] == ["W002", "W001"]

    def test_apply_policy_edd(self):
        wos = make_queue(
            FakeWO("W001", due_date_hours=72),
            FakeWO("W002", due_date_hours=24),
        )
        apply_policy(wos, "EDD", {})
        assert [w.wo_id for w in wos] == ["W002", "W001"]

    def test_apply_policy_unknown_fallback_fifo(self):
        wos = make_queue(FakeWO("W002", arrival_hour=0), FakeWO("W001", arrival_hour=5))
        apply_policy(wos, "RANDOM", {})
        # Should fallback to FIFO: sorted by _queue_entry_hour
        assert [w.wo_id for w in wos] == ["W002", "W001"]


# ═══════════════════════════════════════════════════════════════
# Capacity overflow edge case
# ═══════════════════════════════════════════════════════════════

class TestPolicyEdgeCases:
    def test_policy_preserves_queue_length(self):
        wos = make_queue(
            FakeWO(f"W{i:03d}", arrival_hour=i) for i in range(50)
        )
        original_len = len(wos)
        fifo(wos, {})
        assert len(wos) == original_len

    def test_edd_with_zero_due_dates(self):
        """All zero due_date_hours → EDD should still produce sorted order."""
        wos = make_queue(
            FakeWO("W001"),
            FakeWO("W002"),
            FakeWO("W003"),
        )
        edd(wos, {"cycle_time_map": {"A": 4.0, "B": 2.5, "C": 6.0}})
        # Should be sorted by auto-computed due_date
        assert len(wos) == 3
        for i in range(len(wos) - 1):
            assert wos[i].due_date_hours <= wos[i + 1].due_date_hours
