from django import forms
from .models import Profile, Address

"""
Forms for editing Profile data and creating/updating saved addresses.
"""


class ProfileForm(forms.ModelForm):
    """
    ModelForm for editing a user's Profile.
    """

    class Meta:
        model = Profile
        fields = ["full_name", "phone", "newsletter_opt_in"]


class AddressForm(forms.ModelForm):
    """
    ModelForm for creating or updating a user Address.

    Notes:
        Adds a Bootstrap-friendly widget for the 'kind' select to match the UI.
    """

    class Meta:
        model = Address
        fields = ["kind", "full_name", "phone", "line1", "line2", "postal_code", "city", "country", "is_default"]
        widgets = {
            "kind": forms.Select(attrs={"class": "form-control"}),
        }
