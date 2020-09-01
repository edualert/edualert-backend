import hashlib
import hmac

from django.conf import settings
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db import models
from django.utils import timezone
from oauthlib.common import generate_token


class AccessKey(models.Model):
    """
    An AccessKey instance represents the actual access token to
    access user's resources, as in :rfc:`5`.

    Fields:

    * :attr:`user` The Django user representing resources' owner
    * :attr:`token` Access token - hash value actually
    * :attr:`expires` Date and time of token expiration, in DateTime format
    """
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, db_index=True, unique=True)
    expires = models.DateTimeField()

    objects = models.Manager()

    def is_expired(self):
        """
        Check token expiration with timezone awareness
        Note that this will return true if expiration time is less than 5 minutes away,
        in order to minimize the chances that errors will be presented to users after they input their new password.
        """
        return timezone.now() >= self.expires - timezone.timedelta(minutes=5)

    def expire(self):
        """Sets this token to expired. Sets it's expiry datetime to the current datetime"""
        self.expires = timezone.now()
        self.save()

    @staticmethod
    def create_key(user, **kwargs):
        """Creates an AccessKey with a random token which it then returns
        Can gen either an expiry date as the kwargs expires, or an availability which is a timedelta to calculate the
        expiry date from the current moment.
        """
        availability = kwargs.get('availability', None)
        expires = kwargs.get('expires', None)
        if availability is None and expires is None:
            raise ValueError('either expires or availability have to be non-null')
        if expires is not None and availability is not None:
            raise ValueError('availability and expires can not be both non-null')
        if availability is not None:
            expires = timezone.now() + availability

        token_ok = False
        generated_token = None
        while not token_ok:
            generated_token = generate_token()
            digest = hmac.new(settings.SECRET_KEY.encode(), msg=generated_token.encode(), digestmod=hashlib.sha256).hexdigest()
            token_ok = True
            try:
                AccessKey.objects.create(user=user, expires=expires, token=digest)
            except IntegrityError:
                token_ok = False  # token duplicate

        return generated_token

    @staticmethod
    def get_by_token(token):
        """Gets the access key which the give token corresponds to"""
        digest = hmac.new(settings.SECRET_KEY.encode(), msg=token.encode(), digestmod=hashlib.sha256).hexdigest()
        return AccessKey.objects.get(token=digest)

    @staticmethod
    def delete_expired():
        """Deletes all expired entries from the database"""
        return AccessKey.objects.filter(expires__lt=timezone.now()).delete()

    def __str__(self):
        return self.token
