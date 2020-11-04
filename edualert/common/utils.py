import unicodedata
from copy import deepcopy

import pytz
from django.conf import settings
from django.utils import timezone


def date(year=None, month=None, day=None, date_format=settings.DATE_FORMAT):
    return timezone.datetime(
        year=year or timezone.datetime.now().year,
        month=month or timezone.datetime.now().month,
        day=day or timezone.datetime.now().day
    ).strftime(date_format)


def datetime(year=None, month=None, day=None, hour=None, minute=None, second=None, datetime_format=settings.DATETIME_FORMAT):
    return timezone.datetime(
        year=year or timezone.datetime.now().year,
        month=month or timezone.datetime.now().month,
        day=day or timezone.datetime.now().day,
        hour=hour or timezone.datetime.now().hour,
        minute=minute or timezone.datetime.now().minute,
        second=second or timezone.datetime.now().second
    ).strftime(datetime_format)


def check_date_range_overlap(start1, end1, start2, end2):
    """
    Checks if two range of dates have any overlap (if there is at least a common day)
    :param start1: The start date of the first range
    :param end1: The end date of the first range
    :param start2: The start date of the second range
    :param end2: The end date of the second range
    :return: True/Fale
    """

    return end1 >= start2 and end2 >= start1


def clone_object_and_override_fields(obj, save=False, **overrides):
    clone = deepcopy(obj)
    clone.id = None

    for field, value in overrides.items():
        setattr(clone, field, value)

    if save:
        clone.save()

    return clone


def convert_datetime_to_timezone(datetime_obj, tz='Europe/Bucharest'):
    # Currently, this app is used only in Romania.
    # If one wants to use a different timezone, it can be passed in the request via a header/parameter.
    try:
        return datetime_obj.astimezone(tz=pytz.timezone(tz))
    except pytz.exceptions.UnknownTimeZoneError:
        return datetime_obj


def strip_diacritics(s):
    # Warning!
    # This may significantly change the meaning of the text.
    #
    # Copied from: https://stackoverflow.com/a/518232
    #
    # Documentation for unicodedata.normalize is here:
    # https://docs.python.org/3/library/unicodedata.html?highlight=unicodedata#unicodedata.normalize
    #
    # More information (with pictures) regarding unicode normalization forms can be found here:
    # https://unicode.org/reports/tr15/#Norm_Forms
    #
    # Code point categories are listed here:
    # https://www.unicode.org/versions/Unicode13.0.0/ch04.pdf
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
