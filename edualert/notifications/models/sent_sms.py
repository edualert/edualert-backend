from django.db import models
from django_extensions.db.models import TimeStampedModel


class SentSms(TimeStampedModel):
    recipient = models.TextField()
    message = models.TextField()
    nonce = models.TextField()
    sent_at = models.DateTimeField()

    objects = models.Manager()

    class Meta:
        ordering = ('-sent_at',)
        verbose_name_plural = 'sent sms'

    def __str__(self):
        return f"SentSms {self.id}"
