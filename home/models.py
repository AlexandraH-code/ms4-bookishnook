import secrets
from django.db import models

"""
Models for newsletter subscription with double opt-in and unsubscribe tokens.
"""


class NewsletterSubscriber(models.Model):
    """
    Represents a single newsletter subscription with double opt-in.

    Fields:
        email (EmailField, unique): Subscriber email.
        created_at (DateTimeField): When the record was created.

        confirmed (BooleanField): Whether the email has been confirmed via token.
        confirm_token (CharField): Token used to confirm the subscription.
        confirm_sent_at (DateTimeField): When we last sent a confirmation message.
        confirmed_at (DateTimeField): When the user confirmed.

        unsubscribed (BooleanField): Whether the user has opted out.
        unsubscribe_token (CharField): Token used to one-click unsubscribe.
    """

    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Double opt-in
    confirmed = models.BooleanField(default=False)
    confirm_token = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    confirm_sent_at = models.DateTimeField(blank=True, null=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)

    # Unsubscribe
    unsubscribed = models.BooleanField(default=False)
    unsubscribe_token = models.CharField(max_length=64, blank=True, null=True, db_index=True)

    def __str__(self):
        """
        Return the subscriber's email for admin readability.
        """
        return self.email

    def ensure_tokens(self, save=False):
        """
        Ensure both confirmation and unsubscribe tokens exist.

        Args:
            save (bool): If True, persist the updated tokens to the database.

        Side effects:
            Optionally saves the model with updated token fields.
        """

        if not self.confirm_token:
            self.confirm_token = secrets.token_urlsafe(32)
        if not self.unsubscribe_token:
            self.unsubscribe_token = secrets.token_urlsafe(32)
        if save:
            self.save(update_fields=["confirm_token", "unsubscribe_token"])
