from django import forms


class NewsletterForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        "class": "form-control",
        "placeholder": "Your email address"
    }))

    def clean_email(self):
        return self.cleaned_data["email"].lower().strip()


class ContactForm(forms.Form):
    name = forms.CharField(max_length=120, widget=forms.TextInput(attrs={"placeholder":"Your name"}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={"placeholder":"your@email.com"}))
    message = forms.CharField(widget=forms.Textarea(attrs={"rows":5, "placeholder":"How can we help?"}))
    website = forms.CharField(required=False, widget=forms.HiddenInput())  # honeypot

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Spam detected.")
        return ""

