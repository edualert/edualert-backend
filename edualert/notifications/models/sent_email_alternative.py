from django.db import models
from django_extensions.db.models import TimeStampedModel


class SentEmailAlternative(TimeStampedModel):
    from_email = models.TextField()
    subject = models.TextField()
    cc = models.TextField()
    bcc = models.TextField()

    mime_type = models.TextField()
    content = models.TextField()
    sent_at = models.DateTimeField()

    objects = models.Manager()

    class Meta:
        ordering = ('-sent_at',)

    def __str__(self):
        return f"SentEmailAlternative {self.id}"
