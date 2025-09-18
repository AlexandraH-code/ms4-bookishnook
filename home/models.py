from django.db import models


# Create your models here.
class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # för framtiden:
    confirmed = models.BooleanField(default=True)  # sätt True nu; använd för dubbel opt-in senare

    def __str__(self):
        return self.email
