import uuid
from datetime import date
from decimal import Decimal

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q


class StandingOrder(models.Model):
    """A recurring transfer instruction from checking to checking or savings."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    srcAcc = models.ForeignKey(
        "account.CheckingAccount",
        on_delete=models.PROTECT,
        related_name="standing_orders",
    )

    # Account is abstract, so Django cannot create a regular FK to it. A generic
    # relation represents the diagram's Account target while allowing only the
    # two supported concrete target types in model validation.
    targetContentType = models.ForeignKey(
        ContentType,
        on_delete=models.PROTECT,
        limit_choices_to=Q(
            app_label="account",
            model__in=("checkingaccount", "savingsaccount"),
        ),
    )
    targetObjectId = models.PositiveBigIntegerField()
    targetAcc = GenericForeignKey("targetContentType", "targetObjectId")

    amount = models.DecimalField(max_digits=15, decimal_places=2)
    frequency = models.PositiveIntegerField(help_text="Interval in months (minimum 1).")
    nextExecDate = models.DateField()
    endDate = models.DateField(null=True, blank=True)
    isActive = models.BooleanField(default=True)
    firstExecDate = models.DateField()

    class Meta:
        indexes = [
            models.Index(fields=("targetContentType", "targetObjectId")),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=Decimal("0.00")), name="standing_order_amount_positive"),
            models.CheckConstraint(condition=Q(frequency__gte=1), name="standing_order_frequency_months_gte_1"),
            models.CheckConstraint(condition=Q(nextExecDate__gte=F("firstExecDate")), name="standing_order_next_after_first"),
            models.CheckConstraint(
                condition=Q(endDate__isnull=True) | Q(endDate__gte=F("firstExecDate")),
                name="standing_order_end_after_first",
            ),
        ]

    def clean(self):
        ...
        '''
        super().clean()

        if self.targetAcc is None:
            raise ValidationError({"targetAcc": "Select a checking or savings account."})

        from account.models import CheckingAccount, SavingsAccount

        if not isinstance(self.targetAcc, (CheckingAccount, SavingsAccount)):
            raise ValidationError({"targetAcc": "A standing order cannot target a custody account."})

        if isinstance(self.targetAcc, SavingsAccount) and self.targetAcc.refCheckAcc_id != self.srcAcc_id:
            raise ValidationError({"targetAcc": "The savings account must reference the source checking account."})
        '''

    def isDue(self, on: date) -> bool:
        """Return whether this active order is due on the supplied date."""
        return (
            self.isActive
            and self.nextExecDate <= on
            and (self.endDate is None or on <= self.endDate)
        )

    def changeSchedule(
        self,
        amount: Decimal,
        frequency: int,
        nextDate: date,
        endDate: date | None = None,
    ) -> None:
        self.amount = amount
        self.frequency = frequency
        self.nextExecDate = nextDate
        self.endDate = endDate
        self.full_clean()
        self.save(update_fields=("amount", "frequency", "nextExecDate", "endDate"))

    def activate(self) -> None:
        self.isActive = True
        self.save(update_fields=("isActive",))

    def deactivate(self) -> None:
        self.isActive = False
        self.save(update_fields=("isActive",))

    def advanceNextExecution(self, nextDate: date) -> None:
        self.nextExecDate = nextDate
        self.full_clean()
        self.save(update_fields=("nextExecDate",))

    def __str__(self) -> str:
        return f"Standing order {self.id}: {self.amount} every {self.frequency} month(s)"
