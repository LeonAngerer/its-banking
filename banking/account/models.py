from django.db import models
from decimal import Decimal

# Create your models here.
class Account(models.Model):
    id = models.BigAutoField(primary_key=True)
    iban = models.CharField(max_length=34)
    accountNumber = models.CharField(max_length=34)
    label = models.CharField(max_length=255)
    creationDate = models.DateField()
    customerNumber = models.IntegerField()

    # no Account table is created
    # abstract fields are added to individual child tables
    class Meta:
        abstract = True

class CheckingAccount(Account):
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0.00"))
    overdraftLimit = models.DecimalField(max_digits=15, decimal_places=2)

    def getAvailableFunds(self) -> Decimal:
        ...

    def canDebit(self, amount : Decimal) -> bool:
        ...

    def debit(self, amount : Decimal) -> None:
        ...

    def credit(self, amount : Decimal) -> None:
        ...

class SavingsAccount(Account):
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0.00"))
    refCheckAcc = models.ForeignKey(
        "CheckingAccount",
        on_delete=models.PROTECT,
        related_name="savings_accounts"
    )

    def canDebit(self, amount : Decimal) -> bool:
        ...

    def getRefAccount(self) -> CheckingAccount:
        ...

    def debit(self, amount : Decimal) -> None:
            ...
    
    def credit(self, amount : Decimal) -> None:
        ...

class CustodyAccount(Account):
    refCheckAcc = models.ForeignKey(
        "CheckingAccount",
        on_delete=models.PROTECT,
        related_name="custody_accounts",
    )
    stocks = models.ManyToManyField(
        Stock,
        through="Holding",
        related_name="custody_accounts",
        blank=True,
    )

class PurchasedStock(models.Model):
    id = models.BigAutoField(primary_key=True)
    custody_account = models.ForeignKey(
        CustodyAccount,
        on_delete=models.CASCADE,
        related_name="purchased_stocks",
    )
    stock = models.ForeignKey(
        "stockmarket.Stock",
        on_delete=models.PROTECT,
        related_name="purchase_lots",
    )

    purchase_date = models.DateTimeField()
    purchase_price = models.DecimalField(max_digits=15, decimal_places=4)
    purchase_quantity = models.PositiveIntegerField()
    remaining_quantity = models.PositiveIntegerField()
    
    def getRemainingCost(self) -> Decimal:
        ...
        
    def getMarketValue(self) -> Decimal:
        ...
        
    def reduceQuantity(self, quantity : int) -> None:
        ...
    
    def increaseQuantity(self, quantity : int) -> None:
        ...
