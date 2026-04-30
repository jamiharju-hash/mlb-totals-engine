from app.ev import american_to_decimal, build_signal
from app.schemas import BetSide


def test_american_to_decimal_negative_price():
    assert round(american_to_decimal(-110), 4) == 1.9091


def test_build_signal_passes_when_edge_too_small():
    signal = build_signal(
        game_id='1',
        model_total=8.6,
        market_total=8.5,
        over_price=-110,
        under_price=-110,
        edge_threshold_runs=0.25,
        min_ev=0.015,
        bankroll=10_000,
        kelly_fraction=0.25,
        max_stake_pct=0.02,
    )
    assert signal.side == BetSide.pass_bet
    assert signal.stake == 0


def test_build_signal_returns_over_when_edge_and_ev_clear():
    signal = build_signal(
        game_id='1',
        model_total=9.4,
        market_total=8.5,
        over_price=-105,
        under_price=-115,
        edge_threshold_runs=0.25,
        min_ev=0.015,
        bankroll=10_000,
        kelly_fraction=0.25,
        max_stake_pct=0.02,
    )
    assert signal.side == BetSide.over
    assert signal.expected_value > 0
    assert signal.stake > 0
