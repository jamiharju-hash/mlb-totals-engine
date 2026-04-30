from __future__ import annotations

import math
from dataclasses import dataclass

from app.schemas import BetSide


@dataclass(frozen=True)
class EVResult:
    side: BetSide
    edge_runs: float
    estimated_probability: float
    break_even_probability: float
    expected_value: float
    stake: float
    confidence: str
    reason: str


def american_to_decimal(price: int) -> float:
    if price == 0:
        raise ValueError('American odds cannot be zero')
    if price > 0:
        return 1 + price / 100
    return 1 + 100 / abs(price)


def break_even_probability(price: int) -> float:
    decimal_price = american_to_decimal(price)
    return 1 / decimal_price


def logistic_total_probability(edge_runs: float, sigma: float = 1.45) -> float:
    """Map total-runs edge to cover probability.

    This is intentionally conservative. It should be calibrated from historical
    prediction error distributions before staking real capital.
    """
    return 1 / (1 + math.exp(-edge_runs / sigma))


def expected_value(probability: float, price: int) -> float:
    decimal_price = american_to_decimal(price)
    return probability * decimal_price - 1


def kelly_stake(
    probability: float,
    price: int,
    bankroll: float,
    kelly_fraction: float,
    max_stake_pct: float,
) -> float:
    decimal_price = american_to_decimal(price)
    b = decimal_price - 1
    q = 1 - probability
    raw_kelly = ((b * probability) - q) / b
    clipped = max(0.0, min(raw_kelly * kelly_fraction, max_stake_pct))
    return round(bankroll * clipped, 2)


def build_signal(
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
) -> EVResult:
    edge_runs = model_total - market_total
    side = BetSide.over if edge_runs > 0 else BetSide.under
    abs_edge = abs(edge_runs)
    price = over_price if side == BetSide.over else under_price

    estimated_prob = logistic_total_probability(abs_edge)
    breakeven = break_even_probability(price)
    ev = expected_value(estimated_prob, price)

    if abs_edge < edge_threshold_runs:
        return EVResult(
            side=BetSide.pass_bet,
            edge_runs=round(edge_runs, 3),
            estimated_probability=round(estimated_prob, 4),
            break_even_probability=round(breakeven, 4),
            expected_value=round(ev, 4),
            stake=0.0,
            confidence='LOW',
            reason='Edge below configured run threshold.',
        )

    if ev < min_ev:
        return EVResult(
            side=BetSide.pass_bet,
            edge_runs=round(edge_runs, 3),
            estimated_probability=round(estimated_prob, 4),
            break_even_probability=round(breakeven, 4),
            expected_value=round(ev, 4),
            stake=0.0,
            confidence='LOW',
            reason='Expected value below configured threshold.',
        )

    confidence = 'HIGH' if abs_edge >= 0.75 and ev >= 0.04 else 'MEDIUM'
    stake = kelly_stake(estimated_prob, price, bankroll, kelly_fraction, max_stake_pct)
    return EVResult(
        side=side,
        edge_runs=round(edge_runs, 3),
        estimated_probability=round(estimated_prob, 4),
        break_even_probability=round(breakeven, 4),
        expected_value=round(ev, 4),
        stake=stake,
        confidence=confidence,
        reason='Model total exceeds market threshold with positive expected value.',
    )
