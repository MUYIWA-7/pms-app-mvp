from django.db import models
from django.db.models import UniqueConstraint
from django.contrib.auth.models import User


# =========================
# BUSINESS
# =========================

class Business(models.Model):
    # Business/station name
    name = models.CharField(max_length=150)

    # Each user owns one business
    owner = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name


# =========================
# DAILY RECORD
# =========================

class DailyRecord(models.Model):
    # Business this record belongs to
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="daily_records"
    )

    # Date of the daily reading
    date = models.DateField()

    # Nozzle A readings
    nozzle_a_opening = models.DecimalField(max_digits=10, decimal_places=2)
    nozzle_a_closing = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Nozzle B readings
    nozzle_b_opening = models.DecimalField(max_digits=10, decimal_places=2)
    nozzle_b_closing = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # PMS selling price per litre
    price_per_litre = models.DecimalField(max_digits=10, decimal_places=2)

    # Cash collected
    cash_collected = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Transfers received
    transfers_received = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Time the record was created
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["business", "date"],
                name="unique_business_daily_record"
            )
        ]

    def nozzle_a_litres(self):
        """Calculate litres sold through nozzle A."""
        if self.nozzle_a_closing is None:
            return 0

        return self.nozzle_a_closing - self.nozzle_a_opening


    def nozzle_b_litres(self):
        """Calculate litres sold through nozzle B."""
        if self.nozzle_b_closing is None:
            return 0

        return self.nozzle_b_closing - self.nozzle_b_opening


    def total_litres(self):
        """Calculate total litres sold through both nozzles."""
        return self.nozzle_a_litres() + self.nozzle_b_litres()


    def total_sales(self):
        """Calculate total PMS sales for the day."""
        return self.total_litres() * self.price_per_litre

    def total_expenses(self):
        """Calculate the total expenses for the day."""
        return sum(expense.amount for expense in self.expenses.all())

    def amount_remaining(self):
        """Calculate sales after subtracting daily expenses."""
        return self.total_sales() - self.total_expenses()

    def actual_received(self):
        return self.cash_collected + self.transfers_received

    def reconciliation_difference(self):
        return self.actual_received() - self.amount_remaining()

        if difference == 0:
            return "Balanced"
        elif difference < 0:
            return "Short"
        else:
            return "Over"

    def __str__(self):
        return str(self.date)


# =========================
# EXPENSE
# =========================

class Expense(models.Model):
    # The daily record this expense belongs to
    daily_record = models.ForeignKey(
        DailyRecord,
        on_delete=models.CASCADE,
        related_name="expenses"
    )

    # Expense information
    category = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    # Time the expense was created
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category} - ₦{self.amount}"


# =========================
# PRODUCT
# =========================

class Product(models.Model):
    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=20, default="litres")

    def __str__(self):
        return self.name


# =========================
# FUEL / STOCK INFO 
# =========================

class FuelDelivery(models.Model):

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="fuel_deliveries"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="deliveries"
    )

    quantity_received = models.DecimalField(max_digits=12, decimal_places=2)

    delivery_date = models.DateField()

    cost_per_unit = models.DecimalField(max_digits=12, decimal_places=2)

    supplier = models.CharField(max_length=150)

    reference = models.CharField(max_length=255, blank=True)

    physical_tank_reading = models.DecimalField(max_digits=12, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.delivery_date}"