from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


class RegexValidatorWrapper(object):
    """
    Returns a validator class that is compatible with DRF serializer fields and calls the Django RegexValidator.
    Behaviour is configured using the regex and message attributes.
    """
    regex = None
    message = None

    def __init__(self, value):
        validator = RegexValidator(regex=self.regex, message=self.message)
        validator(value)


class PhoneNumberValidator(RegexValidatorWrapper):
    regex = r'^\+?\d{10,20}$'
    message = _('Invalid format. Must be minimum 10, maximum 20 digits or +.')


class PersonalIdNumberValidator(RegexValidatorWrapper):
    regex = r'^\d{13}$'
    message = _('Invalid format. Must be 13 digits, no spaces allowed.')


class FileNameValidator(RegexValidatorWrapper):
    regex = r'^[\w\-_ ]+\.[\w\-_ ]+$'
    message = _('Invalid file name.')


class EmailValidator(RegexValidatorWrapper):
    regex = r'[^@]+@[^@]+\.[^@]+'
    message = _('Invalid format. Must be 150 characters at most and in the format username@domain.domainextension')


class PasswordValidator(RegexValidatorWrapper):
    regex = r'^\S{6,128}$'
    message = _('Invalid format. Must be minimum 6, maximum 128 characters, no spaces allowed.')
