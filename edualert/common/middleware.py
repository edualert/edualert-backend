import json
import logging
import time
import uuid
from collections import Counter

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import MiddlewareNotUsed
from django.db import connection
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin


class UpdateLastOnlineMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated and getattr(request.user, 'user_profile', None):
            request.user.user_profile.last_online = timezone.now()
            request.user.user_profile.save()

        return response


class SQLPrintingMiddleware(MiddlewareMixin):
    """
    Middleware which prints out a list of all SQL queries done
    for each view that is processed. This is only useful for debugging.

    Original code was taken from http://djangosnippets.org/snippets/290/
    with improvements like:
    - print URL from what queries was
    - don't show queries from static URLs (MEDIA_URL and STATIC_URL, also for /favicon.ico).
    - Used only If DEBUG is False
    - Remove guessing of terminal width (This breaks the rendered SQL)
    """

    def __init__(self, get_response):
        # One-time configuration and initialization.
        if not getattr(settings, 'DEBUG', False):
            raise MiddlewareNotUsed

        super().__init__(get_response)

    def process_response(self, request, response):
        WHITE = '\033[0m'
        RED = '\033[1;31m'
        YELLOW = '\033[1;32m'
        BLUE = '\033[1;34m'
        PURPLE = '\033[1;35m'

        start = time.time()
        if (len(connection.queries) == 0 or
                request.path_info.startswith('/favicon.ico') or
                request.path_info.startswith(settings.STATIC_URL) or
                request.path_info.startswith(settings.MEDIA_URL)):
            return response

        indentation = 2
        raw_queries = []
        print("\n\n{}{}[SQL Queries for]{} {} {}{}\n".format(" " * indentation, PURPLE, BLUE, request.method, request.path_info, WHITE))
        total_time = 0.0
        for query in connection.queries:
            # if query['sql'].startswith('SELECT'):
            #     continue
            nice_sql = query['sql'].replace('"', '').replace(',', ', ')
            sql = "{}[{}]{} {}".format(RED, query['time'], WHITE, nice_sql)

            print("{}{}\n".format(" " * indentation, sql))

            total_time = total_time + float(query['time'])
            raw_queries.append(nice_sql)

        replace_tuple = (" " * indentation, YELLOW, str(total_time), str(len(connection.queries)), WHITE)
        print("{}{}[TOTAL TIME: {} seconds ({} queries)]{}\n".format(*replace_tuple))

        duplicate_count = Counter(raw_queries)
        if duplicate_count:
            print('{}{}Duplicates:{}\n'.format(" " * indentation, RED, WHITE))
            for key, value in duplicate_count.items():
                if value > 1:
                    print(" " * indentation + key)
                    print('{}Duplicated {}[{}]{} times\n'.format(RED, " " * indentation, value, WHITE))

        end = time.time()
        replace_tuple = (" " * indentation, YELLOW, str(end - start), WHITE)
        print("{}{}[MIDDLWARE OVERHEAD: {} seconds]{}\n".format(*replace_tuple))

        return response


class RequestActivityTrackerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # read body before it's read by `rest_framework.Request` so that it's saved on the `django.http.HttpRequest`
        # object, this will allows us to read it again after the response is retrieved
        _ = request.body

        # pass the request down the middleware chain
        response = self.get_response(request)

        try:
            _process_request(request, response)
        except Exception:
            # regardless of error do not obstruct the requests
            logging.exception('Failed to log request')

        return response


def _process_request(request, response):
    # Filter request by method
    if request.method in ['OPTIONS', 'HEAD', 'GET']:
        return response

    # Only track requests for identifiable users
    user = request.user
    if not user or user.is_anonymous or not user.id:
        return response

    # Save request information in cache to be extracted and saved to a persistent storage
    cache_value_raw = {
        'timestamp_ms': int(time.time() * 1000),
        'user_id': request.user.id,
        'method': request.method,
        'path': request.get_full_path_info(),
        'status_code': response.status_code,
        'request_body': _get_request_body(request),
    }
    cache_key = 'track_request_{}'.format(uuid.uuid4())
    cache_value = json.dumps(cache_value_raw)
    cache.set(cache_key, cache_value, timeout=None)


def _get_request_body(request):
    """
    Return a json object when content type is 'application/json'. Sensitive fields in the object are replaced.
    """
    request_body = None

    if request.content_type and request.content_type == 'application/json':
        # return masked content if it's json
        request_body_json = json.loads(request.body)

        # mask sensitive fields
        _replace_fields_recursively(request_body_json, [
            'password', 'new_password', 'current_password', 'email', 'phone_number', 'educator_email',
            'educator_phone_number'
        ])
        request_body = request_body_json

    return request_body


def _replace_fields_recursively(obj, keys, value='<masked>'):
    def replace(o, k, _):
        if k in keys:
            o[k] = value

    _iter_dict(obj, replace)


def _iter_dict(obj, func):
    """
    Call `func` for every key/value pair we can find in the provided `dict`.
    """
    if not isinstance(obj, dict):
        return

    for key, val in obj.items():
        # iterate dictionaries recursively
        if isinstance(val, dict):
            _iter_dict(val, func)
        # iterate over list values
        elif isinstance(val, list):
            for item in val:
                _iter_dict(item, func)
        else:
            func(obj, key, val)
