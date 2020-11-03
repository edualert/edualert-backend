import json
import logging

from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from edualert.academic_calendars.utils import get_current_academic_calendar, generate_next_year_academic_calendar
from edualert.academic_programs.utils import generate_next_year_academic_programs
from edualert.profiles.constants import FAILING_1_SUBJECT_LABEL, FAILING_2_SUBJECTS_LABEL, EXEMPTED_SPORT_LABEL, EXEMPTED_RELIGION_LABEL
from edualert.profiles.models import Label, UserProfile


@shared_task
def generate_next_study_year_task():
    current_calendar = get_current_academic_calendar()
    if not current_calendar:
        return

    last_event = current_calendar.school_events.order_by('-ends_at').first()
    if last_event and timezone.now().date() == last_event.ends_at + timezone.timedelta(days=1):
        generate_next_year_academic_calendar()
        generate_next_year_academic_programs()
        remove_students_from_study_classes()


def remove_students_from_study_classes():
    labels_to_be_removed = [label for label in Label.objects.filter(text__in=[FAILING_1_SUBJECT_LABEL, FAILING_2_SUBJECTS_LABEL,
                                                                              EXEMPTED_SPORT_LABEL, EXEMPTED_RELIGION_LABEL])]
    students_to_update = []
    for student in UserProfile.objects.filter(user_role=UserProfile.UserRoles.STUDENT, student_in_class__isnull=False):
        student.labels.remove(*labels_to_be_removed)
        student.student_in_class = None
        students_to_update.append(student)
    UserProfile.objects.bulk_update(students_to_update, ['student_in_class'], batch_size=100)


@shared_task()
def send_request_log_to_cloud_watch_task():
    """
    Dispatch logs to Cloud Watch Logs.

    The name of the log group in which to put the logs is retrieved from `settings.REQUEST_LOG`.
    The name of the log stream is composed from the current month and year in the MM-YYYY format.

    Requires permission to execute the following AWS actions:
    - logs:DescribeLogGroups
    - logs:DescribeLogStreams
    - logs:CreateLogGroup
    - logs:CreateLogStream
    - logs:PutLogEvents

    Warning!
    From the requirements of posting events to a stream which are listed here:
    https://docs.aws.amazon.com/AmazonCloudWatchLogs/latest/APIReference/API_PutLogEvents.html
    only a couple are handled by this function. Namely the size in bytes, the chronological order and the maximum
    number of events.
    """
    import boto3
    from botocore.config import Config

    # check we are using the expected redis client because we rely on a specific function from it to iterate through
    # the cache keys
    if settings.CACHES['default']['BACKEND'] != "django_redis.cache.RedisCache" or \
            (not hasattr(cache, 'iter_keys') or not callable(cache.iter_keys)):
        logging.error("Expected 'default' cache to be django-redis and have a function `iter_keys`.")
        return

    log_group_name = settings.REQUEST_LOG['LOG_GROUP_NAME']
    log_group_region_name = settings.REQUEST_LOG['REGION_NAME']
    client = boto3.client('logs', config=Config(region_name=log_group_region_name))

    # lookup log group; create it if we can't find it
    try:
        log_group = _retrieve_track_request_log_group(client, log_group_name)
    except IndexError:
        client.create_log_group(logGroupName=log_group_name)
        log_group = _retrieve_track_request_log_group(client, log_group_name)

    # lookup log stream; create it if we can't find it
    now = timezone.now()
    log_stream_name = '{}-{}'.format(now.month, now.year)
    try:
        log_stream = _retrieve_track_request_log_stream(client, log_group, log_stream_name)
    except IndexError:
        client.create_log_stream(logGroupName=log_group['logGroupName'], logStreamName=log_stream_name)
        log_stream = _retrieve_track_request_log_stream(client, log_group, log_stream_name)

    # `max_batch_size_bytes`, `log_event_extra_bytes` and `max_batch_size` are taken from here:
    # https://docs.aws.amazon.com/AmazonCloudWatchLogs/latest/APIReference/API_PutLogEvents.html
    max_batch_size_bytes = 1_048_576  # 1MB
    log_event_extra_bytes = 26
    max_batch_size = 10_000
    batch = []
    batch_size_bytes = 0
    sequence_token = log_stream['uploadSequenceToken'] if 'uploadSequenceToken' in log_stream else None


    for cache_key in cache.iter_keys("track_request_*"):
        # extract log from cache
        log_str = cache.get(cache_key)
        cache.set(cache_key, '', timeout=0)
        # extract timestamp from log
        log = json.loads(log_str)
        log_timestamp = log['timestamp_ms']

        log_bytes = len(log_str.encode('utf-8')) + log_event_extra_bytes
        if log_bytes > max_batch_size_bytes:
            # If any log is bigger than the permitted batch size, send the current batch, truncate the response body
            # and send the log on it's own

            sequence_token = _dispatch_batch(client, log_group, log_stream, sequence_token, batch)

            # Truncate the response body by a multiple of 4, to be sure we don't break utf-8 and send it
            extra_bytes = log_bytes - max_batch_size_bytes
            extra_bytes_reminder = extra_bytes % 4
            bytes_to_truncate = extra_bytes - extra_bytes_reminder
            log_str = json.dumps({
                'timestamp_ms': log['timestamp_ms'],
                'user_id': log['user_id'],
                'method': log['method'],
                'path': log['path'],
                'status_code': log['status_code'],
                'request_body': log['request_body'][:-bytes_to_truncate],
            })
            sequence_token = _dispatch_batch(client, log_group, log_stream, sequence_token, [{
                'timestamp': log_timestamp,
                'message': log_str,
            }])
        else:
            # Send current bach to Cloud Watch Logs if we reached the maximum size of the batch OR before we exceed the
            # maximum size of the batch in bytes.
            if len(batch) == max_batch_size or batch_size_bytes + log_bytes > max_batch_size_bytes:
                sequence_token = _dispatch_batch(client, log_group, log_stream, sequence_token, batch)
                batch = []
                batch_size_bytes = 0

            batch.append({
                'timestamp': log_timestamp,
                'message': log_str,
            })
            batch_size_bytes += log_bytes

    # Dispatch batch if there are any logs left
    if len(batch) > 0:
        _dispatch_batch(client, log_group, log_stream, sequence_token, batch)


def _dispatch_batch(client, log_group, log_stream, sequence_token, batch):
    try:
        sorted_batch = sorted(batch, key=lambda x: x['timestamp'])
        params = {
            'logGroupName': log_group['logGroupName'],
            'logStreamName': log_stream['logStreamName'],
            'logEvents': sorted_batch,
        }
        if sequence_token:
            params['sequenceToken'] = sequence_token
        response = client.put_log_events(**params)
        return response['nextSequenceToken']
    except Exception as error:
        # in case the request fails log the error and the batch and return the sequence_token
        logging.error('Failed to send log events batch to Cloud Watch. Exception: {}\nBatch: {}', error, batch)
        return sequence_token


def _retrieve_track_request_log_stream(client, log_group, stream_name):
    """
    Try to retrieve the track requests log stream.

    When multiple log streams matching the stream name are found, the recently created one is returned.
    When no log streams are found an IndexError exception is raised.
    """
    response = client.describe_log_streams(logGroupName=log_group['logGroupName'], logStreamNamePrefix=stream_name)
    log_streams = response['logStreams']
    log_streams_count = len(log_streams) != 1
    if log_streams_count > 1:
        # return the most recently created log group
        return sorted(log_streams, key=lambda x: x['creationTime'], reverse=True)[0]
    return log_streams[0]


def _retrieve_track_request_log_group(client, log_group_name):
    """
    Try to retrieve the track requests log group.

    When multiple log groups matching the track request prefix are found, the recently created one is returned.
    When no log groups are found an IndexError exception is raised.
    """
    response = client.describe_log_groups(logGroupNamePrefix=log_group_name)
    log_groups = response['logGroups']
    log_groups_count = len(log_groups) != 1
    if log_groups_count > 1:
        # return the most recently created log group
        return sorted(log_groups, key=lambda x: x['creationTime'], reverse=True)[0]
    return log_groups[0]
