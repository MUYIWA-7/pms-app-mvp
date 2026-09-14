from django import forms
from django.contrib.auth.models import User


class SignUpForm(forms.Form):
    # User information
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    # Business information
    business_name = forms.CharField(max_length=150)

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data

    def clean_username(self):
        username = self.cleaned_data["username"]

        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")

        return username

    def clean_email(self):
        email = self.cleaned_data["email"]

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")

        return email