from django.db import models

# Create your models here.
class Food(models.Model):
    name = models.CharField(max_length=100)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    supplier = models.CharField(max_length=100, null=True, blank=True)
    quantity = models.IntegerField(default=0)
    date_added = models.DateField(auto_now_add=True)




class OverBoughtSold(models.Model):
    id = models.AutoField(primary_key=True)
    symbol = models.CharField(max_length=255, null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    last = models.CharField(max_length=255, null=True, blank=True)
    volume = models.CharField(max_length=255, null=True, blank=False)
    rsi = models.CharField(max_length=255, null=True, blank=True)
    eps = models.CharField(max_length=255, null=True, blank=True)
    pe = models.CharField(max_length=255, null=True, blank=True)
    rank = models.CharField(max_length=255, null=True, blank=True)
    profit_margin = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    condition_integer = models.IntegerField(null=True, blank=True)

    def calculate_condition_integer(self):
        try:
            rsi_value = float(self.rsi)
        except (ValueError, TypeError):
            return None

        if rsi_value > 70:
            return 1
        elif rsi_value < 30:
            return -1
        else:
            return 0

    def condition_label(self):
        mapping = {
            1: "Overbought",
            0: "Neutral",
            -1: "Oversold"
        }
        return mapping.get(self.condition_integer, "Unknown")

    def save(self, *args, **kwargs):
        self.condition_integer = self.calculate_condition_integer()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.symbol or 'Unknown Symbol'} - {self.condition_label()}"
