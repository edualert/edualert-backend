import csv
import datetime
import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import DatabaseError
from django.utils import timezone
from django.utils.translation import gettext as _, pgettext

from edualert.common.validators import PhoneNumberValidator, PersonalIdNumberValidator, EmailValidator
from edualert.profiles.models import UserProfile
from edualert.profiles.serializers import BaseUserProfileDetailSerializer, BIRTH_DATE_IN_THE_PAST_ERROR, \
    DISALLOWED_USER_ROLE_ERROR, USERNAME_UNIQUE_ERROR

logger = logging.getLogger(__name__)


class UserProfileImporter:
    report = {
        "errors": {}
    }
    file = None
    number_of_users = 0
    request_user_profile = None
    language = 'en'

    def __init__(self, file, request_user_profile, language):
        self.report = {'errors': {}}
        self.file = file
        self.request_user_profile = request_user_profile
        self.school_unit = self.request_user_profile.school_unit
        self.language = language
        self.number_of_users = 0

    def import_users_and_get_report(self):
        users = self._fetch_from_csv()
        self._save(users)
        self._update_report_with_statistics()
        return self.report

    def _fetch_from_csv(self):
        return csv.DictReader(self.file)

    def _handle_user_role_translation(self, user_role):
        # Choices will be translated according to the request language
        romanian_translation = {
            'administrator': UserProfile.UserRoles.ADMINISTRATOR,
            'director de scoala': UserProfile.UserRoles.PRINCIPAL,
            'profesor': UserProfile.UserRoles.TEACHER,
            'parinte': UserProfile.UserRoles.PARENT,
            'elev': UserProfile.UserRoles.STUDENT
        }
        english_translation = {
            'administrator': UserProfile.UserRoles.ADMINISTRATOR,
            'school principal': UserProfile.UserRoles.PRINCIPAL,
            'teacher': UserProfile.UserRoles.TEACHER,
            'parent': UserProfile.UserRoles.PARENT,
            'student': UserProfile.UserRoles.STUDENT
        }

        if self.language == 'ro':
            return romanian_translation.get(user_role)
        return english_translation.get(user_role)

    def _handle_boolean_translation(self, user_role):
        romanian_translation = {
            'da': True,
            'nu': False
        }
        english_translation = {
            'yes': True,
            'no': False
        }

        if self.language == 'ro':
            return romanian_translation.get(user_role)
        return english_translation.get(user_role)

    def _handle_header_translation(self, value, reverse=False):
        romanian_translation = {
            "nume": "full_name",
            "foloseste telefon ca nume utilizator": "use_phone_as_username",
            "rol utilizator": "user_role",
            "adresa email": "email",
            "numar telefon": "phone_number",
            "adresa": "address",
            "cnp": "personal_id_number",
            "data nasterii": "birth_date",
            "nume pedagog": "educator_full_name",
            "numar telefon pedagog": "educator_phone_number",
            "adresa email pedagog": "educator_email"
        }
        english_translation = {
            "name": "full_name",
            "use phone as username": "use_phone_as_username",
            "user role": "user_role",
            "email address": "email",
            "phone number": "phone_number",
            "address": "address",
            "personal id number": "personal_id_number",
            "birth date": "birth_date",
            "educator name": "educator_full_name",
            "educator phone number": "educator_phone_number",
            "educator email address": "educator_email"
        }

        dictionary = romanian_translation if self.language == 'ro' else english_translation
        if reverse:
            for key, translation in dictionary.items():
                if translation == value:
                    return key

        if self.language == 'ro':
            return romanian_translation.get(value)

        return english_translation.get(value)

    def _save(self, user_data):
        for index, user_dict in enumerate(user_data):
            self.number_of_users += 1
            user_dict = self._validate_and_clean_user(user_dict)
            errors = user_dict.pop('errors', None)
            if errors:
                self._add_row_to_report(index + 1, errors)
            else:
                try:
                    user = User.objects.create(username=user_dict['username'])
                    user_dict['user_id'] = user.id
                    UserProfile.objects.create(**user_dict)
                except DatabaseError as e:
                    logger.error(e)
                    self._add_row_to_report(index + 1, {'general_errors': _('An error occurred while creating the user.')})

    def _validate_and_clean_user(self, user):
        # Translate header rows
        user = {
            self._handle_header_translation(key.lower()): value
            for key, value in user.items()
            if self._handle_header_translation(key.lower())
        }

        # Validates user data and returns only the fields that are accepted
        errors = {}
        required_field_error = _('This field is required.')
        role = self._handle_user_role_translation(user.get('user_role', '').lower())
        user['user_role'] = role

        if not role:
            errors['user_role'] = _('Must be one of the following options: Administrator, Principal, Teacher, Parent or Student.')
        elif not BaseUserProfileDetailSerializer.is_allowed_to_edit(getattr(self.request_user_profile, 'user_role', None), role):
            errors['user_role'] = DISALLOWED_USER_ROLE_ERROR

        accepted_fields = ['full_name', 'use_phone_as_username', 'email', 'phone_number', 'user_role']
        required_fields = ['full_name', 'use_phone_as_username']
        if role == UserProfile.UserRoles.STUDENT:
            accepted_fields += ['address', 'personal_id_number', 'birth_date', 'educator_full_name', 'educator_email', 'educator_phone_number']

            if user.get('educator_full_name') and not (user.get('educator_email') or user.get('educator_phone_number')):
                errors['educator_full_name'] = _('Either email or phone number is required for the educator.')

            birth_date = user.get('birth_date')
            if birth_date:
                try:
                    date = datetime.datetime.strptime(birth_date, settings.DATE_FORMAT).date()
                    if date >= timezone.now().date():
                        errors['birth_date'] = BIRTH_DATE_IN_THE_PAST_ERROR
                    user['birth_date'] = date
                except ValueError:
                    errors['birth_date'] = _('Invalid date format. Must be DD-MM-YYYY.')

            personal_id_number = user.get('personal_id_number')
            if personal_id_number:
                try:
                    PersonalIdNumberValidator(personal_id_number)
                except ValidationError:
                    errors['personal_id_number'] = PersonalIdNumberValidator.message
        elif role == UserProfile.UserRoles.PARENT:
            accepted_fields += ['address', ]

        use_phone_as_username = self._handle_boolean_translation(user.get('use_phone_as_username'))
        if use_phone_as_username:
            required_fields += ['phone_number']
        elif use_phone_as_username is False:
            required_fields += ['email']
        else:
            errors['use_phone_as_username'] = _('Must be either yes or no.')

        for field in required_fields:
            if not user.get(field):
                errors[field] = required_field_error

        user['use_phone_as_username'] = use_phone_as_username
        username = user.get('phone_number') if user['use_phone_as_username'] else user.get('email')
        if self.request_user_profile.user_role == UserProfile.UserRoles.PRINCIPAL:
            username = '{}_{}'.format(self.school_unit.id, username)
            accepted_fields += ['school_unit', ]
            user['school_unit'] = self.school_unit

        if username and (UserProfile.objects.filter(username=username).exists() or
                         User.objects.filter(username=username).exists()):
            error_key = 'phone_number' if use_phone_as_username else 'email'
            errors[error_key] = USERNAME_UNIQUE_ERROR

        user['username'] = username
        accepted_fields += ['username']

        for phone_number in ['phone_number', 'educator_phone_number']:
            number = user.get(phone_number)
            if number:
                try:
                    PhoneNumberValidator(number)
                except ValidationError:
                    errors[phone_number] = PhoneNumberValidator.message

        for email in ['email', 'educator_email']:
            email_address = user.get(email)
            if email_address:
                try:
                    EmailValidator(email_address)
                except ValidationError:
                    errors[email] = EmailValidator.message

        max_lengths = {
            "full_name": 180,
            "email": 150,
            "address": 100,
            "educator_email": 150,
            "educator_full_name": 180
        }
        for key, value in max_lengths.items():
            if len(user.get(key, '')) > value:
                errors[key] = _('Write maximum {} characters.').format(value)

        cleaned_user = {
            key: value.strip() if isinstance(value, str) else value
            for key, value in user.items() if key in accepted_fields and value
        }
        translated_errors = {
            self._handle_header_translation(key, reverse=True).capitalize(): value
            for key, value in errors.items() if self._handle_header_translation(key, reverse=True)
        }
        cleaned_user['errors'] = translated_errors

        return cleaned_user

    def _add_row_to_report(self, row_number, error_details):
        self.report['errors'][row_number] = error_details

    def _update_report_with_statistics(self):
        actual_saved_users = self.number_of_users - len(self.report['errors'])
        self.report['report'] = pgettext(
            'users', '{} out of {} {} saved successfully.'
        ).format(actual_saved_users, self.number_of_users, _('user') if self.number_of_users == 1 else _('users'))
