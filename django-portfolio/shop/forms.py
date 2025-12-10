from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Profile

class CustomUserCreationForm(UserCreationForm):
    # Make phone REQUIRED for signup
    email = forms.EmailField(required=True, help_text="Required. Enter a valid email address.")
    phone = forms.CharField(required=True, max_length=20, help_text="Required. Add mobile number (Digits only).")

    class Meta:
        model = User
        fields = ("username", "email", "phone", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email:
            raise ValidationError("Please enter an email address.")
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()
        if not phone:
            raise ValidationError("Please enter a mobile number.")
        if not phone.isdigit():
            raise ValidationError("Phone number should contain digits only.")
        # optional: add length check
        if len(phone) < 6 or len(phone) > 15:
            raise ValidationError("Enter a valid phone number (6-15 digits).")
        return phone

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone']
        widgets = {
            'phone': forms.TextInput(attrs={'placeholder': 'e.g. 9876543210'})
        }
