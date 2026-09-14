from django.contrib.auth.decorators import login_required

from decimal import Decimal

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import DailyRecordForm, ExpenseForm, FuelDeliveryForm
from .models import DailyRecord, FuelDelivery, Product


# Create your views here.
# =========================
# LANDING PAGE
# =========================
def home(request):
    # Logged-in users go directly to the dashboard
    if request.user.is_authenticated:
        return redirect("dashboard")

    return render(request, "station/home.html")


# =========================
# DASHBOARD
# =========================
@login_required
def dashboard(request):

    today = timezone.localdate()

    # Get today's record
    today_record = DailyRecord.objects.filter(
        business=request.user.business,
        date=today
    ).first()

    # Determine today's status
    if not today_record:
        today_status = "Not Started"

    elif (
        today_record.nozzle_a_closing is None
        or today_record.nozzle_b_closing is None
    ):
        today_status = "In Progress"

    else:
        today_status = "Completed"


    # =========================
    # LATEST COMPLETED RECORD
    # =========================

    latest_record = DailyRecord.objects.filter(
        business=request.user.business,
        nozzle_a_closing__isnull=False,
        nozzle_b_closing__isnull=False
    ).order_by("-date").first()


    # =========================
    # DASHBOARD VALUES
    # =========================

    total_litres = Decimal("0.00")
    total_sales = Decimal("0.00")
    total_expenses = Decimal("0.00")
    amount_remaining = Decimal("0.00")


    # Calculate figures from the latest completed record
    if latest_record:

        total_litres = latest_record.total_litres()
        total_sales = latest_record.total_sales()
        total_expenses = latest_record.total_expenses()
        amount_remaining = latest_record.amount_remaining()


    # =========================
    # LAST 7 COMPLETED RECORDS
    # =========================

    completed_records = DailyRecord.objects.filter(
        business=request.user.business,
        nozzle_a_closing__isnull=False,
        nozzle_b_closing__isnull=False
    ).order_by("-date")[:7]


    # Reverse the records so the chart
    # displays oldest → newest
    completed_records = list(
        reversed(completed_records)
    )


    # Dates for the chart
    chart_dates = [
        record.date.strftime("%d %b")
        for record in completed_records
    ]


    # Sales values for the chart
    chart_sales = [
        float(record.total_sales())
        for record in completed_records
    ]

    # Expenses values for the chart
    chart_expenses = [
        float(record.total_expenses())
        for record in completed_records
    ]

    # =========================
    # 7-DAY PERFORMANCE
    # =========================

    period_sales = sum(
        record.total_sales()
        for record in completed_records
    )

    period_expenses = sum(
        record.total_expenses()
        for record in completed_records
    )

    period_litres = sum(
        record.total_litres()
        for record in completed_records
    )

    if completed_records:

        average_daily_sales = (
            period_sales / len(completed_records)
        )

        best_sales_record = max(
            completed_records,
            key=lambda record: record.total_sales()
        )

    else:

        average_daily_sales = Decimal("0.00")
        best_sales_record = None


    # =========================
    # CONTEXT
    # =========================

    context = {

        "today_record": today_record,
        "today_status": today_status,

        "latest_record": latest_record,

        "total_litres": total_litres,
        "total_sales": total_sales,
        "total_expenses": total_expenses,
        "amount_remaining": amount_remaining,

        "chart_dates": chart_dates,
        "chart_sales": chart_sales,
        "chart_expenses": chart_expenses,

        "period_sales": period_sales,
        "period_expenses": period_expenses,
        "period_litres": period_litres,
        "average_daily_sales": average_daily_sales,
        "best_sales_record": best_sales_record,
    }


    return render(
        request,
        "station/dashboard.html",
        context
    )


# =========================
# DAILY ENTRY
# =========================

@login_required
def daily_entry(request):
    business = request.user.business
    selected_date = request.GET.get("date")

    # ===== GET SELECTED RECORD =======

    if selected_date:
        record = DailyRecord.objects.filter(
            business=business,
            date=selected_date
        ).first()
    else:
        record = DailyRecord.objects.filter(
            business=business,
            date=timezone.now().date()
        ).first()

    # ==== DEFAULT FORMS =======

    daily_form = DailyRecordForm(instance=record)
    expense_form = ExpenseForm()

    # ======= HANDLE POST ============

    if request.method == "POST":

        action = request.POST.get("action")

        # ==== SAVE OPENING READING =====

        if action == "save_opening":

            # Opening can only be saved once.
            if record:
                messages.info(
                    request,
                    "Opening reading has already been saved."
                )

                return redirect(
                    f"{request.path}?date={record.date}"
                )

            daily_form = DailyRecordForm(request.POST)

            if daily_form.is_valid():

                new_record = daily_form.save(commit=False)

                new_record.business = business

                # Opening stage does not save closing readings.
                new_record.nozzle_a_closing = None
                new_record.nozzle_b_closing = None

                # Reconciliation starts at zero.
                new_record.cash_collected = Decimal("0.00")
                new_record.transfers_received = Decimal("0.00")

                new_record.save()

                messages.success(
                    request,
                    "Opening reading saved successfully."
                )

                return redirect(
                    f"{request.path}?date={new_record.date}"
                )

        # ===== SAVE CLOSING READING ========

        elif action == "save_closing":

            if not record:
                messages.error(
                    request,
                    "Please save the opening reading first."
                )

                return redirect(request.path)

            daily_form = DailyRecordForm(
                request.POST,
                instance=record
            )

            if daily_form.is_valid():

                closing_a = daily_form.cleaned_data.get(
                    "nozzle_a_closing"
                )

                closing_b = daily_form.cleaned_data.get(
                    "nozzle_b_closing"
                )

                # Both closing readings are required.
                if closing_a is None or closing_b is None:

                    messages.error(
                        request,
                        "Please enter both closing readings."
                    )

                # Closing A cannot be lower than opening A.
                elif closing_a < record.nozzle_a_opening:

                    messages.error(
                        request,
                        "Nozzle A closing reading cannot be less than its opening reading."
                    )

                # Closing B cannot be lower than opening B.
                elif closing_b < record.nozzle_b_opening:

                    messages.error(
                        request,
                        "Nozzle B closing reading cannot be less than its opening reading."
                    )

                else:

                    updated_record = daily_form.save(
                        commit=False
                    )

                    # Keep the original opening information.
                    updated_record.business = business
                    updated_record.date = record.date
                    updated_record.nozzle_a_opening = (
                        record.nozzle_a_opening
                    )
                    updated_record.nozzle_b_opening = (
                        record.nozzle_b_opening
                    )
                    updated_record.price_per_litre = (
                        record.price_per_litre
                    )

                    updated_record.save()

                    messages.success(
                        request,
                        "Closing reading saved successfully."
                    )

                    return redirect(
                        f"{request.path}?date={record.date}"
                    )

        # ===== ADD EXPENSE  =======

        elif action == "add_expense":

            if not record:
                messages.error(
                    request,
                    "Please save the opening reading first."
                )

                return redirect(request.path)

            expense_form = ExpenseForm(request.POST)

            if expense_form.is_valid():

                expense = expense_form.save(
                    commit=False
                )

                expense.daily_record = record
                expense.save()

                messages.success(
                    request,
                    "Expense added successfully."
                )

                return redirect(
                    f"{request.path}?date={record.date}"
                )

        # === SAVE CASH RECONCILIATION ========

        elif action == "save_cash":

            if not record:
                messages.error(
                    request,
                    "Please save the opening reading first."
                )

                return redirect(request.path)

            # Closing readings must exist before
            # cash reconciliation can be completed.
            if (
                record.nozzle_a_closing is None
                or record.nozzle_b_closing is None
            ):
                messages.error(
                    request,
                    "Please save the closing reading first."
                )

                return redirect(
                    f"{request.path}?date={record.date}"
                )

            daily_form = DailyRecordForm(
                request.POST,
                instance=record
            )

            if daily_form.is_valid():

                updated_record = daily_form.save(
                    commit=False
                )

                # Keep all original reading information.
                updated_record.business = business
                updated_record.date = record.date
                updated_record.nozzle_a_opening = (
                    record.nozzle_a_opening
                )
                updated_record.nozzle_b_opening = (
                    record.nozzle_b_opening
                )
                updated_record.nozzle_a_closing = (
                    record.nozzle_a_closing
                )
                updated_record.nozzle_b_closing = (
                    record.nozzle_b_closing
                )
                updated_record.price_per_litre = (
                    record.price_per_litre
                )

                updated_record.save()

                messages.success(
                    request,
                    "Cash reconciliation saved successfully."
                )

                return redirect(
                    f"{request.path}?date={record.date}"
                )

        # ===== UNKNOWN ACTION =============

        else:

            messages.error(
                request,
                "Invalid action."
            )

            return redirect(
                f"{request.path}?date={selected_date}"
                if selected_date
                else request.path
            )

    # ======= EXPENSES =========

    expenses = []

    if record:
        expenses = record.expenses.all()

    # ======= CONTEXT =======

    context = {
        "daily_form": daily_form,
        "expense_form": expense_form,
        "record": record,
        "expenses": expenses,
    }

    return render(
        request,
        "station/daily.html",
        context
    )

# =========================
# PREVIOUS DAILY RECORDS
# =========================
@login_required
def previous_records(request):

    records = DailyRecord.objects.filter(
        business=request.user.business
    ).prefetch_related("expenses").order_by("-date")

    context = {
        "records": records,
    }

    return render(
        request,
        "station/records.html",
        context
    )


# =========================
# RECORD DETAILS
# =========================

@login_required
def record_detail(request, record_id):

    record = get_object_or_404(
        DailyRecord.objects.prefetch_related("expenses"),
        id=record_id,
        business=request.user.business
    )

    return render(
        request,
        "station/record_detail.html",
        {"record": record}
    )


# =========================
# STOCK DETAILS
# =========================

@login_required
def stock(request):

    if request.method == "POST":

        delivery_form = FuelDeliveryForm(request.POST)

        if delivery_form.is_valid():

            delivery = delivery_form.save(commit=False)
            delivery.business = request.user.business
            delivery.save()

            messages.success(
                request,
                "Fuel delivery recorded successfully."
            )

            return redirect("stock")

    else:
        delivery_form = FuelDeliveryForm()

    # Get all deliveries for this business
    deliveries = FuelDelivery.objects.filter(
        business=request.user.business
    ).select_related("product").order_by(
        "-delivery_date",
        "-id"
    )

    # Get the PMS product
    pms = Product.objects.filter(
        name="PMS"
    ).first()

    latest_delivery = None
    estimated_sold = Decimal("0.00")
    estimated_remaining = Decimal("0.00")

    if pms:

        # Get the most recent PMS delivery
        latest_delivery = FuelDelivery.objects.filter(
            business=request.user.business,
            product=pms
        ).order_by(
            "-delivery_date",
            "-id"
        ).first()

        if latest_delivery:

            # Get completed PMS daily records
            records = DailyRecord.objects.filter(
                business=request.user.business,
                date__gte=latest_delivery.delivery_date,
                nozzle_a_closing__isnull=False,
                nozzle_b_closing__isnull=False
            )

            estimated_sold = sum(
                record.total_litres()
                for record in records
            )

            estimated_remaining = (
                latest_delivery.physical_tank_reading
                - estimated_sold
            )

    context = {
        "delivery_form": delivery_form,
        "deliveries": deliveries,
        "latest_delivery": latest_delivery,
        "estimated_sold": estimated_sold,
        "estimated_remaining": estimated_remaining,
    }

    return render(
        request,
        "station/stock.html",
        context
    )


