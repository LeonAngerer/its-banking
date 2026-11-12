from django.db import models
from account.dto import CustomerAccounts

class Bank(models.Model):
    """The banking institution."""

    name = models.CharField(max_length=255)
    plz = models.CharField(max_length=20)
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    bic = models.CharField(max_length=11, unique=True)

    def __str__(self):
        return self.name


class BankBranch(models.Model):
    """A physical location belonging to one bank institution."""

    bank = models.ForeignKey(Bank, on_delete=models.PROTECT, related_name="branches")
    name = models.CharField(max_length=255)
    plz = models.CharField(max_length=20)
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.bank.name})"


class Person(models.Model):
    """Shared identity data for customers and employees."""

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    plz = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    street = models.CharField(max_length=255)
    bank = models.ForeignKey(
        Bank,
        on_delete=models.PROTECT,
        related_name="%(class)s_set",
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Employee(Person):
    salary = models.DecimalField(max_digits=12, decimal_places=2)
    employee_number = models.PositiveIntegerField(unique=True)


class Customer(Person):
    salary = models.DecimalField(max_digits=12, decimal_places=2)
    customer_number = models.PositiveIntegerField(unique=True)

    def getAllAccounts(self) -> CustomerAccounts:
        from account.dto import CustomerAccounts
        from account.models import CheckingAccount, CustodyAccount, SavingsAccount

        return CustomerAccounts(
            checking_accounts=list(
                CheckingAccount.objects.filter(customerNumber=self.customer_number)
            ),
            savings_accounts=list(
                SavingsAccount.objects.filter(customerNumber=self.customer_number)
            ),
            custody_accounts=list(
                CustodyAccount.objects.filter(customerNumber=self.customer_number)
            ),
        )
    
    def openAccoount(self, accountType : str) -> bool:
        ...
