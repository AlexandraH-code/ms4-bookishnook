from django import forms
from .models import Profile, Address


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["full_name","phone","newsletter_opt_in"]


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ["kind","full_name","phone","line1","line2","postal_code","city","country","is_default"]
        widgets = {
            "kind": forms.Select(attrs={"class":"form-control"}),
        }
