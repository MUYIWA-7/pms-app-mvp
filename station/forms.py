from django import forms
from .models import DailyRecord, Expense, FuelDelivery


# =========================
# DAILY RECORD FORM
# =========================

class DailyRecordForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):

        # Get the existing record, if one exists
        instance = kwargs.get("instance")

        super().__init__(*args, **kwargs)

        # Cash reconciliation is entered when completing the day's record.
        self.fields["cash_collected"].required = False
        self.fields["transfers_received"].required = False

        # If a record already exists, its opening readings should not be changed during the evening update.
        if instance and instance.pk:

            self.fields["nozzle_a_opening"].disabled = True
            self.fields["nozzle_b_opening"].disabled = True

            self.fields["date"].disabled = True
            self.fields["price_per_litre"].disabled = True

    class Meta:
        model = DailyRecord

        fields = [
            "date",
            "nozzle_a_opening",
            "nozzle_a_closing",
            "nozzle_b_opening",
            "nozzle_b_closing",
            "price_per_litre",
            "cash_collected",
            "transfers_received",
        ]

        widgets = {
            "date": forms.DateInput(
                attrs={"type": "date"}
            ),

            "nozzle_a_opening": forms.NumberInput(
                attrs={"step": "0.01"}
            ),

            "nozzle_a_closing": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "placeholder": "Enter closing reading later"
                }
            ),

            "nozzle_b_opening": forms.NumberInput(
                attrs={"step": "0.01"}
            ),

            "nozzle_b_closing": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "placeholder": "Enter closing reading later"
                }
            ),

            "price_per_litre": forms.NumberInput(
                attrs={"step": "0.01"}
            ),

            "cash_collected": forms.NumberInput(
                attrs={"step": "0.01", "placeholder": "0.00"}
            ),

            "transfers_received": forms.NumberInput(
                attrs={"step": "0.01", "placeholder": "0.00"}
            ),
        }

# =========================
# EXPENSE FORM
# =========================

class ExpenseForm(forms.ModelForm):

    class Meta:
        model = Expense
        fields = [
            "category",
            "description",
            "amount",
        ]

        widgets = {
            "category": forms.TextInput(
                attrs={
                    "placeholder": "e.g. Generator"
                }
            ),

            "description": forms.TextInput(
                attrs={
                    "placeholder": "Optional description"
                }
            ),

            "amount": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "placeholder": "0.00"
                }
            ),
        }

    # Validate expense amount
    def clean_amount(self):

        amount = self.cleaned_data.get("amount")

        if amount is not None and amount <= 0:
            raise forms.ValidationError(
                "Expense amount must be greater than zero."
            )

        return amount


# =========================
#  FUEL DELIVERY FORM
# =========================
class FuelDeliveryForm(forms.ModelForm):

    class Meta:
        model = FuelDelivery
        fields = [
            "product",
            "quantity_received",
            "delivery_date",
            "cost_per_unit",
            "supplier",
            "reference",
            "physical_tank_reading",
        ]

        widgets = {
            "delivery_date": forms.DateInput(
                attrs={"type": "date"}
            ),

            "quantity_received": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "placeholder": "0.00"
                }
            ),

            "cost_per_unit": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "placeholder": "0.00"
                }
            ),

            "supplier": forms.TextInput(
                attrs={
                    "placeholder": "Supplier name"
                }
            ),

            "reference": forms.TextInput(
                attrs={
                    "placeholder": "Optional reference or notes"
                }
            ),

            "physical_tank_reading": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "placeholder": "0.00"
                }
            ),
        }

    def clean_quantity_received(self):
        quantity = self.cleaned_data.get("quantity_received")

        if quantity is not None and quantity <= 0:
            raise forms.ValidationError(
                "Quantity received must be greater than zero."
            )

        return quantity

    def clean_cost_per_unit(self):
        cost = self.cleaned_data.get("cost_per_unit")

        if cost is not None and cost <= 0:
            raise forms.ValidationError(
                "Cost / price must be greater than zero."
            )

        return cost

    def clean_physical_tank_reading(self):
        reading = self.cleaned_data.get("physical_tank_reading")

        if reading is not None and reading < 0:
            raise forms.ValidationError(
                "Physical tank reading cannot be negative."
            )

        return reading


