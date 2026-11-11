from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import CheckingAccount, CustodyAccount, SavingsAccount


@dataclass
class CustomerAccounts:
    """All account types belonging to one customer, grouped by model."""

    checking_accounts: list[CheckingAccount] = field(default_factory=list)
    savings_accounts: list[SavingsAccount] = field(default_factory=list)
    custody_accounts: list[CustodyAccount] = field(default_factory=list)

    @property
    def all_accounts(self) -> list[CheckingAccount | SavingsAccount | CustodyAccount]:
        return [*self.checking_accounts, *self.savings_accounts, *self.custody_accounts]
