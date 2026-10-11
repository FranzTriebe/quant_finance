"""Phase 0 smoke test: the engine package and all its modules import."""
import importlib

import pytest

MODULES = ["data", "risk", "backtest", "stats", "validation", "plotting"]


@pytest.mark.parametrize("name", MODULES)
def test_module_imports(name: str) -> None:
    importlib.import_module(f"quantlab.{name}")
