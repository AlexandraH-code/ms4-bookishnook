import secrets
from django.db import models


# Create your models here.
class NewsletterSubscriber(models.Model):
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
        return self.email

    def ensure_tokens(self, save=False):
        if not self.confirm_token:
            self.confirm_token = secrets.token_urlsafe(32)
        if not self.unsubscribe_token:
            self.unsubscribe_token = secrets.token_urlsafe(32)
        if save:
            self.save(update_fields=["confirm_token", "unsubscribe_token"])
