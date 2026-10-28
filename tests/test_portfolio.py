from decimal import Decimal as D

import pytest

from portfolio import Action, Portfolio, Stock

META = Stock("META", D("500"))
AAPL = Stock("AAPL", D("200"))
TSLA = Stock("TSLA", D("250"))


def trades_by_symbol(portfolio):
    return {t.symbol: t for t in portfolio.rebalance()}


def apply_trades(portfolio, trades):
    """Simulate executing the trades and return the resulting holdings."""
    stocks = {s.symbol: s for s in set(portfolio.holdings) | set(portfolio.allocation)}
    holdings = {stocks[s.symbol]: q for s, q in portfolio.holdings.items()}
    for t in trades:
        stock = stocks[t.symbol]
        sign = 1 if t.action == Action.BUY else -1
        holdings[stock] = holdings.get(stock, D("0")) + sign * t.quantity
    return holdings


# --- rebalance -------------------------------------------------------------

def test_example_from_statement():
    p = Portfolio({META: D("10"), AAPL: D("20")}, {META: D("0.4"), AAPL: D("0.6")})
    trades = trades_by_symbol(p)

    assert trades["META"].action == Action.SELL
    assert trades["META"].quantity == D("2.8")
    assert trades["AAPL"].action == Action.BUY
    assert trades["AAPL"].quantity == D("7")


def test_balanced_portfolio_needs_no_trades():
    # META 2 * 500 = 1000, AAPL 5 * 200 = 1000 -> already 50/50
    p = Portfolio({META: D("2"), AAPL: D("5")}, {META: D("0.5"), AAPL: D("0.5")})
    assert p.rebalance() == []


def test_sells_everything_of_a_stock_not_in_allocation():
    p = Portfolio({META: D("2"), TSLA: D("4")}, {META: D("1")})
    trades = trades_by_symbol(p)

    assert trades["TSLA"].action == Action.SELL
    assert trades["TSLA"].quantity == D("4")


def test_buys_a_stock_not_currently_held():
    p = Portfolio({META: D("2")}, {META: D("0.5"), AAPL: D("0.5")})
    trades = trades_by_symbol(p)

    assert trades["AAPL"].action == Action.BUY
    assert trades["AAPL"].amount == D("500")


def test_total_bought_equals_total_sold():
    p = Portfolio(
        {META: D("3"), AAPL: D("1"), TSLA: D("7")},
        {META: D("0.2"), AAPL: D("0.5"), TSLA: D("0.3")},
    )
    trades = p.rebalance()
    bought = sum(t.amount for t in trades if t.action == Action.BUY)
    sold = sum(t.amount for t in trades if t.action == Action.SELL)
    assert bought == sold


def test_portfolio_matches_allocation_after_applying_trades():
    p = Portfolio(
        {META: D("3"), AAPL: D("1"), TSLA: D("7")},
        {META: D("0.2"), AAPL: D("0.5"), TSLA: D("0.3")},
    )
    total = p.total_value()
    new_holdings = apply_trades(p, p.rebalance())

    for stock, weight in p.allocation.items():
        assert new_holdings[stock] * stock.current_price() == pytest.approx(weight * total)


def test_empty_portfolio_returns_no_trades():
    p = Portfolio({}, {META: D("1")})
    assert p.rebalance() == []


# --- validation ------------------------------------------------------------

def test_weights_must_sum_to_one():
    with pytest.raises(ValueError, match="sum to 1"):
        Portfolio({META: D("1")}, {META: D("0.5"), AAPL: D("0.4")})


def test_negative_weight_is_rejected():
    with pytest.raises(ValueError, match="negative"):
        Portfolio({META: D("1")}, {META: D("1.2"), AAPL: D("-0.2")})


def test_negative_quantity_is_rejected():
    with pytest.raises(ValueError, match="negative"):
        Portfolio({META: D("-1")}, {META: D("1")})


def test_price_must_be_positive():
    with pytest.raises(ValueError, match="positive"):
        Stock("META", D("0"))


def test_stocks_are_equal_by_symbol():
    assert Stock("META", D("500")) == Stock("META", D("510"))