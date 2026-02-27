from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
import re

from .models import Comment, UserPost


# =========================
# SIGNUP FORM
# =========================
class BlogSignupForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ("username", "email")

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if not re.match(r"^[A-Za-z0-9_]+$", username):
            raise forms.ValidationError(
                "Username can contain only letters, numbers, and underscores."
            )
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email:
            raise forms.ValidationError("Email is required.")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email is already registered.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")

        if p1 and p2:
            if p1 != p2:
                raise forms.ValidationError("Passwords do not match.")
            validate_password(p1)

        return cleaned_data


# =========================
# COMMENT FORM
# =========================
class BlogCommentForm(forms.ModelForm):
    content = forms.CharField(
        label="",
        widget=forms.Textarea(attrs={
            "rows": 4,
            "placeholder": "Write your comment (Markdown supported)...",
            "class": "w-full border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary"
        })
    )

    class Meta:
        model = Comment
        fields = ("content",)


# =========================
# USER POST FORM (NEW)
# =========================
class UserPostForm(forms.ModelForm):
    class Meta:
        model = UserPost
        fields = ("title", "category", "description", "image", "video")


        widgets = {
            "title": forms.TextInput(attrs={
                "class": "w-full rounded-lg border px-4 py-2",
                "placeholder": "Post title"
            }),
            "category": forms.Select(attrs={
                "class": "w-full rounded-lg border px-4 py-2"
            }),
            "description": forms.Textarea(attrs={
                "rows": 5,
                "class": "w-full rounded-lg border px-4 py-3",
                "placeholder": "Write your post..."
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        image = cleaned_data.get("image")
        video = cleaned_data.get("video")

        if image and video:
            raise forms.ValidationError(
                "Upload either an image or a video, not both."
            )

        if not image and not video:
            raise forms.ValidationError(
                "Please upload an image or a video."
            )

        if image and image.size > 2 * 1024 * 1024:
            raise forms.ValidationError("Image must be under 2MB.")

        if video and video.size > 10 * 1024 * 1024:
            raise forms.ValidationError("Video must be under 10MB.")

        return cleaned_data
