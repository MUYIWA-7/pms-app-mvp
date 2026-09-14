from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render

from .forms import SignUpForm
from station.models import Business

from django.contrib.auth.models import User

# Create your views here.
def signup(request):
    # Handle signup form submission
    if request.method == "POST":
        form = SignUpForm(request.POST)

        if form.is_valid():
            # Create the user securely
            user = User(
                username=form.cleaned_data["username"],
                email=form.cleaned_data["email"]
            )
            # Set password securely
            user.set_password(form.cleaned_data["password"])
            user.save()

            # Create the business owned by this user
            Business.objects.create(
                name=form.cleaned_data["business_name"],
                owner=user
            )

            # Log the user in immediately after signup
            login(request, user)

            return redirect("dashboard")

    else:
        form = SignUpForm()

    return render(request, "accounts/signup.html", {"form": form})


def user_login(request):
    # Handle login form submission
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect("dashboard")

        return render(
            request,
            "accounts/login.html",
            {"error": "Invalid username or password."}
        )

    return render(request, "accounts/login.html")


def user_logout(request):
    # Log the user out
    logout(request)

    return redirect("login")