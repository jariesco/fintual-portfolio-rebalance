from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class Stock:
    """A tradable stock identified by its ticker symbol.

    Equality and hashing use only the symbol, so a Stock can be used
    as a dict key even if its price changes between snapshots.
    """

    symbol: str
    price: Decimal = field(compare=False)

    def __post_init__(self) -> None:
        if not self.symbol:
            raise ValueError("Stock symbol cannot be empty")
        if self.price <= 0:
            raise ValueError(f"Price for {self.symbol} must be positive")

    def current_price(self) -> Decimal:
        """Return the last available price for this stock."""
        return self.price