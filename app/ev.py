from __future__ import annotations

import math
from dataclasses import dataclass

from app.schemas import BetSide


@dataclass(frozen=True)
class EdgeResult:
    game_id: str
    side: BetSide
    model_total: float
    market_total: float
    market_price: int
    edge_runs: float
    estimated_probability: float
    break_even_probability: float
    expected_value: float
    full_kelly_fraction: float
    applied_kelly_fraction: float
    stake: float
    should_bet: bool
    confidence: str
    reason: str


# Backward-compatible name used by existing API code.
EVResult = EdgeResult


def american_to_decimal(price: int) -> float:
    if price == 0:
        raise ValueError('American odds cannot be zero')
    if price > 0:
        return 1 + price / 100
    return 1 + 100 / abs(price)


def break_even_probability(price: int) -> float:
    return 1 / american_to_decimal(price)


def logistic_total_probability(edge_runs: float, sigma: float = 1.45) -> float:
    """Map absolute total-runs edge to cover probability.

    This is conservative and should be recalibrated from historical prediction
    error distribution before real-money deployment.
    """
    return 1 / (1 + math.exp(-edge_runs / sigma))


def expected_value(probability: float, price: int) -> float:
    decimal_price = american_to_decimal(price)
    return probability * decimal_price - 1


def full_kelly_fraction(probability: float, price: int) -> float:
    decimal_price = american_to_decimal(price)
    b = decimal_price - 1
    q = 1 - probability
    return ((b * probability) - q) / b


def applied_kelly_fraction(
    probability: float,
    price: int,
    kelly_fraction: float,
    max_stake_pct: float,
) -> float:
    raw = full_kelly_fraction(probability, price)
    return max(0.0, min(raw * kelly_fraction, max_stake_pct))


def kelly_stake(
    probability: float,
    price: int,
    bankroll: float,
    kelly_fraction: float,
    max_stake_pct: float,
) -> float:
    applied = applied_kelly_fraction(probability, price, kelly_fraction, max_stake_pct)
    return round(bankroll * applied, 2)


def determine_side(model_total: float, market_total: float) -> BetSide:
    if model_total > market_total:
        return BetSide.over
    if model_total < market_total:
        return BetSide.under
    return BetSide.pass_bet


def calculate_edge(
    *,
    game_id: str,
    model_total: float,
    market_total: float,
    over_price: int,
    under_price: int,
    edge_threshold_runs: float,
    min_ev: float,
    bankroll: float,
    kelly_fraction: float,
    max_stake_pct: float,
) -> EdgeResult:
    edge_runs = model_total - market_total
    abs_edge = abs(edge_runs)
    side = determine_side(model_total, market_total)

    if side == BetSide.pass_bet:
        market_price = over_price
    else:
        market_price = over_price if side == BetSide.over else under_price

    estimated_prob = logistic_total_probability(abs_edge)
    breakeven = break_even_probability(market_price)
    ev = expected_value(estimated_prob, market_price)
    raw_kelly = full_kelly_fraction(estimated_prob, market_price)
    applied_kelly = applied_kelly_fraction(estimated_prob, market_price, kelly_fraction, max_stake_pct)

    should_bet = True
    reason = 'Model total exceeds market threshold with positive expected value.'
    confidence = 'HIGH' if abs_edge >= 0.75 and ev >= 0.04 else 'MEDIUM'

    if side == BetSide.pass_bet:
        should_bet = False
        reason = 'Model total equals market total.'
        confidence = 'LOW'
    elif abs_edge < edge_threshold_runs:
        should_bet = False
        reason = 'Edge below configured run threshold.'
        confidence = 'LOW'
    elif ev < min_ev:
        should_bet = False
        reason = 'Expected value below configured threshold.'
        confidence = 'LOW'
    elif raw_kelly <= 0:
        should_bet = False
        reason = 'Kelly fraction is not positive after market price adjustment.'
        confidence = 'LOW'

    stake = round(bankroll * applied_kelly, 2) if should_bet else 0.0
    final_side = side if should_bet else BetSide.pass_bet

    return EdgeResult(
        game_id=game_id,
        side=final_side,
        model_total=round(float(model_total), 3),
        market_total=round(float(market_total), 3),
        market_price=int(market_price),
        edge_runs=round(edge_runs, 3),
        estimated_probability=round(estimated_prob, 4),
        break_even_probability=round(breakeven, 4),
        expected_value=round(ev, 4),
        full_kelly_fraction=round(raw_kelly, 5),
        applied_kelly_fraction=round(applied_kelly if should_bet else 0.0, 5),
        stake=stake,
        should_bet=should_bet,
        confidence=confidence,
        reason=reason,
    )


def build_signal(**kwargs) -> EdgeResult:
    """Backward-compatible wrapper for older API code."""
    return calculate_edge(**kwargs)
