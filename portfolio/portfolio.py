from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from portfolio.stock import Stock


class Action(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

@dataclass(frozen=True)
class Trade:
    """An order needed to move the portfolio towards its target allocation.

    quantity: number of shares (fractional shares allowed)
    amount:   money value of the order at current prices
    """

    symbol: str
    action: Action
    quantity: Decimal
    amount: Decimal

class Portfolio:
    """A collection of stock holdings plus a target allocation.

    holdings:   stock -> number of shares currently owned
    allocation: stock -> target weight (e.g. Decimal("0.4") for 40%)
    """

    def __init__(
        self,
        holdings: dict[Stock, Decimal],
        allocation: dict[Stock, Decimal],
    ) -> None:
        self._validate_holdings(holdings)
        self._validate_allocation(allocation)
        # Copy the dicts so later changes by the caller don't affect us.
        self.holdings = dict(holdings)
        self.allocation = dict(allocation)

    def total_value(self) -> Decimal:
        """Market value of all holdings at current prices."""
        return sum(
            (quantity * stock.current_price() for stock, quantity in self.holdings.items()),
            Decimal("0"),
        )

    @staticmethod
    def _validate_holdings(holdings: dict[Stock, Decimal]) -> None:
        for stock, quantity in holdings.items():
            if quantity < 0:
                raise ValueError(f"Quantity for {stock.symbol} cannot be negative")

    @staticmethod
    def _validate_allocation(allocation: dict[Stock, Decimal]) -> None:
        if not allocation:
            raise ValueError("Allocation cannot be empty")
        for stock, weight in allocation.items():
            if weight < 0:
                raise ValueError(f"Weight for {stock.symbol} cannot be negative")
        total = sum(allocation.values(), Decimal("0"))
        if total != Decimal("1"):
            raise ValueError(f"Allocation weights must sum to 1, got {total}")

    def rebalance(self) -> list[Trade]:
        """Return the trades needed to match the target allocation.

        Algorithm:
        1. Take a single price snapshot so every calculation uses the
            same prices (a real price feed could change mid-calculation).
        2. total = sum(quantity * price) over current holdings.
        3. For each stock in holdings OR allocation:
            target_value  = weight * total   (weight is 0 if not allocated)
            current_value = quantity * price (quantity is 0 if not held)
            diff = target_value - current_value
            diff > 0 -> BUY, diff < 0 -> SELL, diff == 0 -> nothing.

        Trades are only calculated, not executed: the portfolio is not
        modified. Total bought always equals total sold, so no extra cash
        is needed.
        """
        all_stocks = set(self.holdings) | set(self.allocation)
        prices = {stock: stock.current_price() for stock in all_stocks}

        total = sum(
            (quantity * prices[stock] for stock, quantity in self.holdings.items()),
            Decimal("0"),
        )
        if total == 0:
            # Nothing to redistribute: buying would require new cash,
            # which is out of scope.
            return []

        trades = []
        for stock in all_stocks:
            current_value = self.holdings.get(stock, Decimal("0")) * prices[stock]
            target_value = self.allocation.get(stock, Decimal("0")) * total
            diff = target_value - current_value
            if diff == 0:
                continue
            trades.append(
                Trade(
                    symbol=stock.symbol,
                    action=Action.BUY if diff > 0 else Action.SELL,
                    quantity=abs(diff) / prices[stock],
                    amount=abs(diff),
                )
            )
        # Sells first (they free up the cash for buys), then buys; each group by symbol.
        return sorted(trades, key=lambda t: (t.action == Action.BUY, t.symbol))