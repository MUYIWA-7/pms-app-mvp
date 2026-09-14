from django.urls import path
from . import views


# =========================
# STATION URLS
# =========================

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("daily/", views.daily_entry, name="daily"),
    path("records/", views.previous_records, name="records"),
    path("records/<int:record_id>/", views.record_detail, name="record_detail"),
    path("stock/", views.stock, name="stock"),
]