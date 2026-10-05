from django.conf import settings
from django.db import models


class Shareholder(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shareholder_records",
    )

    def __str__(self):
        return str(self.user)


class Contribution(models.Model):
    TYPE_CASH = "CASH"
    TYPE_IN_KIND = "INKIND"
    TYPE_TIME = "TIME"
    TYPE_WORK = "WORK"

    TYPE_CHOICES = [
        (TYPE_CASH, "Cash"),
        (TYPE_IN_KIND, "In-Kind"),
        (TYPE_TIME, "Time"),
        (TYPE_WORK, "Work Done"),
    ]

    shareholder = models.ForeignKey(
        Shareholder,
        on_delete=models.CASCADE,
        related_name="contributions",
    )
    contribution_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return (
            f"{self.shareholder} - "
            f"{self.get_contribution_type_display()} - "
            f"{self.amount}"
        )


class MyModel(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shareholders_mymodels",
    )

    def __str__(self):
        return str(self.user)