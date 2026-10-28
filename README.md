# Portfolio Rebalance

Solution to Fintual's technical task: a `Portfolio` class that holds stocks,
has a target allocation (e.g. 40% META, 60% AAPL), and calculates which
stocks to buy and sell to match that allocation.

## How to run

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv run python -m pytest -v
```

## Usage

```python
from decimal import Decimal as D
from portfolio import Portfolio, Stock

meta = Stock("META", D("500"))
aapl = Stock("AAPL", D("200"))

portfolio = Portfolio(
    holdings={meta: D("10"), aapl: D("20")},      # shares owned
    allocation={meta: D("0.4"), aapl: D("0.6")},  # target weights
)

portfolio.rebalance()
# [Trade(symbol='AAPL', action=BUY,  quantity=7,   amount=1400),
#  Trade(symbol='META', action=SELL, quantity=2.8, amount=1400)]
```

## Approach

1. Compute the total portfolio value at current prices.
2. For every stock in the holdings **or** the allocation:
   - `target_value = weight × total` (weight is 0 if the stock is not allocated)
   - `current_value = quantity × price` (quantity is 0 if the stock is not held)
   - `diff = target_value − current_value` → buy if positive, sell if negative.
3. Convert each money difference into shares: `quantity = |diff| / price`.

Using the union of holdings and allocation means the same loop handles the
two edge cases: stocks held but not allocated are sold entirely, and
allocated stocks not yet held are bought from zero.

Since the target values add up to the current total, money from sales
always equals money spent on purchases: rebalancing needs no extra cash.

## Design decisions

- **`rebalance()` returns trades instead of executing them.** It is easier
  to test, keeps the portfolio unchanged, and mirrors how a real system
  would work: propose orders first, execute them separately.
- **One price snapshot per rebalance.** `current_price()` is called once per
  stock, so the total and every trade use the same prices even if they
  came from a live feed.
- **`Decimal` instead of `float`** for money and weights, to avoid rounding
  errors (e.g. `0.1 + 0.2 != 0.3` with floats).
- **Stocks are equal by symbol.** `Stock` is an immutable dataclass whose
  price does not take part in equality, so it can be used as a dict key.
- **Validation in the constructor.** An invalid portfolio (weights not
  summing to 1, negative weights or quantities, non-positive prices)
  cannot be created, so `rebalance()` can trust its data.
- **Deterministic output.** Trades are sorted by symbol.

## Assumptions and limitations

- **Fractional shares are allowed**, as in most modern investment apps.
  With whole shares only, quantities would need rounding and a small
  leftover difference would remain.
- **No commissions, taxes or cash balance.** The rebalance only
  redistributes the current value. An empty portfolio returns no trades.
- **Weights must sum to exactly 1.** This works well with `Decimal`
  inputs like `"0.4"`, but an allocation such as one third cannot be
  expressed exactly. A small tolerance would solve that if needed.
- **Prices come from `Stock.current_price()`**, which here returns a
  stored value. In a real app it would query a price provider without
  changes to `Portfolio`.

## Tests

Besides specific examples (including the one above), two tests check
properties that must always hold: total bought equals total sold, and
applying the trades leaves the portfolio exactly at its target allocation.

## Use of LLMs

I worked through this task with Claude. I defined the design decisions
(language, fractional shares, returning trades instead of executing them,
which edge cases to cover), reviewed every part of the code and validated
it with the tests. The full conversations are in `conversations/`.