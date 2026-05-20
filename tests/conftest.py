"""
conftest.py — OTD Engine 測試共享 fixtures
"""

import sys
from pathlib import Path

# Add showcase/otd-sim to path so we can import engine modules
OTD_SIM_DIR = Path(__file__).parent.parent / "showcase" / "otd-sim"
sys.path.insert(0, str(OTD_SIM_DIR))

import pytest
from datetime import datetime


# ═══════════════════════════════════════════════════════════════
# Fixtures: WorkOrder / Station / Factory helpers
# ═══════════════════════════════════════════════════════════════

@pytest.fixture
def make_wo():
    """Factory: create a WorkOrder-like mock with required attributes."""
    def _make(
        wo_id="W001",
        product_type="A",
        qty_planned=100,
        arrival_day=0,
        qty_good=0,
        qty_defect=0,
        station_idx=0,
        **kwargs,
    ):
        class _WO:
            def __init__(self):
                self.wo_id = wo_id
                self.product_type = product_type
                self.qty_planned = qty_planned
                self.arrival_day = arrival_day
                self.qty_good = qty_good
                self.qty_defect = qty_defect
                self._queue_entry_hour = kwargs.get("_queue_entry_hour", 0.0)
                self.due_date_hours = kwargs.get("due_date_hours", 0.0)
                self.spt_score = kwargs.get("spt_score", 0.0)
                for k, v in kwargs.items():
                    setattr(self, k, v)
        return _WO()
    return _make


@pytest.fixture
def sample_factory_config():
    """Minimal factory config for DueDateAdapter."""
    return {
        "order_template": {
            "due_date": {
                "format": "default",
                "base_days": 14,
                "jitter_days": 3,
                "arrival_plus_days": 7,
                "overrides": {},
            },
            "products": [
                {"type": "A", "lead_time_days": 10, "cycle_time_hrs": 4.0},
                {"type": "B", "lead_time_days": 7, "cycle_time_hrs": 2.5},
                {"type": "C", "lead_time_days": 14, "cycle_time_hrs": 6.0},
            ],
        }
    }


@pytest.fixture
def sample_stations():
    """Minimal stations dict for StationDispatchLoop."""
    return {
        "S1": type("Station", (), {"name": "S1", "capacity": 1, "process_fn": lambda wo, h: None})(),
        "S2": type("Station", (), {"name": "S2", "capacity": 1, "process_fn": lambda wo, h: None})(),
        "S3": type("Station", (), {"name": "S3", "capacity": 1, "process_fn": lambda wo, h: None})(),
    }
