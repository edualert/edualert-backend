import time
from collections import Counter

from django.conf import settings
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
