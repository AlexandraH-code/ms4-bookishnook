from django import forms

"""
Forms for newsletter subscription and contact messaging.
"""


class NewsletterForm(forms.Form):
    """
    Simple newsletter form that collects and normalizes an email address.

    Widgets:
        - Email input with bootstrap-friendly classes/placeholder.
    """

    email = forms.EmailField(widget=forms.EmailInput(attrs={
        "class": "form-control",
        "placeholder": "Your email address"
    }))

    def clean_email(self):
        """
        Normalize the email address by lowercasing and stripping whitespace.

        Returns:
            str: Cleaned email address.
        """

        return self.cleaned_data["email"].lower().strip()


class ContactForm(forms.Form):
    """
    Contact form with a honeypot field to deter basic spam bots.

    Fields:
        name (CharField)
        email (EmailField)
        message (CharField, textarea)
        website (CharField, hidden honeypot)
    """

    name = forms.CharField(max_length=120, widget=forms.TextInput(attrs={"placeholder": "Your name"}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={"placeholder": "your@email.com"}))
    message = forms.CharField(widget=forms.Textarea(attrs={"rows": 5, "placeholder": "How can we help?"}))
    website = forms.CharField(required=False, widget=forms.HiddenInput())  # honeypot

    def clean_website(self):
        """
        Validate the hidden honeypot field.

        If any value is present, treat the submission as spam.

        Raises:
            ValidationError: When the honeypot is filled.

        Returns:
            str: Always an empty string when valid.
        """

        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Spam detected.")
        return ""
