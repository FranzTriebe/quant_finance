"""Backtest engine.

Strategies hand in target weights as of the close of day t. run() lags them by lag days
(default 1) before applying them to returns. This module is the only place in the repo
that shifts weights, so look ahead bias can only enter in one place. Implemented in Phase 1."""
