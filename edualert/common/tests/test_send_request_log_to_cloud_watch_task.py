import json
import logging
from contextlib import ExitStack
from datetime import datetime
from unittest.mock import patch, Mock, call

from django.test import SimpleTestCase, override_settings

from edualert.common.tasks import send_request_log_to_cloud_watch_task, _provide_log_group, _provide_log_stream, \
    _dispatch_batch


@override_settings(CACHES={'default': {'BACKEND': 'django_redis.cache.RedisCache'}})
class SendRequestLogToCloudWatchTestCase(SimpleTestCase):
    @override_settings(REQUEST_LOG={'LOG_GROUP_NAME': 'dummy-group-name', 'REGION_NAME': 'dummy-region'})
    def test_cache(self):
        client = type('DummyClient', (object,), {})
        new_client_mock = Mock(return_value=client)
        log_group = {}
        log_stream = {}

        def new_settings(max_batch_size=None, max_batch_size_bytes=None):
            settings = {'LOG_GROUP_NAME': 'dummy-group-name', 'REGION_NAME': 'dummy-region'}
            if max_batch_size:
                settings['MAX_BATCH_SIZE'] = max_batch_size
            if max_batch_size_bytes:
                settings['MAX_BATCH_SIZE_BYTES'] = max_batch_size_bytes
            return settings

        def create_cache_obj(timestamp_ms=None, request_body=None):
            return {
                'timestamp_ms': timestamp_ms or 0,
                'user_id': 0,
                'method': 'POST',
                'path': '/',
                'status_code': 200,
                'request_body': request_body or None,
            }

        def create_batch_obj(cache_obj):
            return {
                'timestamp': cache_obj['timestamp_ms'],
                'message': json.dumps(cache_obj)
            }

        def setup_default_context(exit_stack):
            exit_stack.enter_context(patch('edualert.common.tasks.cache', new=cache_mock))
            exit_stack.enter_context(patch('edualert.common.tasks.boto3.client', new=new_client_mock))
            exit_stack.enter_context(patch('edualert.common.tasks._provide_log_group', new=lambda _c, _l: log_group))
            exit_stack.enter_context(patch('edualert.common.tasks._provide_log_stream', new=lambda _c, _l: log_stream))
            exit_stack.enter_context(patch('edualert.common.tasks._dispatch_batch', new=_dispatch_batch_mock))

        # when there are no cache keys, make sure we don't call `_dispatch_batch_mock`
        cache_mock = type('DummyCache', (object,), {})
        cache_mock.iter_keys = Mock(return_value=[])
        _dispatch_batch_mock = Mock()
        with ExitStack() as stack:
            setup_default_context(stack)
            send_request_log_to_cloud_watch_task()
            _dispatch_batch_mock.assert_not_called()

        # when there are cache keys less than `MAX_BATCH_SIZE` make sure we call `_dispatch_batch_mock` once
        cache_objects = [create_cache_obj()]
        cache_mock = type('DummyCache', (object,), {})
        cache_mock.get = Mock(side_effect=[json.dumps(c) for c in cache_objects])
        cache_mock.set = Mock()
        cache_mock.iter_keys = Mock(return_value=['cache_key_01'])
        _dispatch_batch_mock = Mock()
        with ExitStack() as stack:
            setup_default_context(stack)
            # override `MAX_BATCH_SIZE`
            stack.enter_context(override_settings(REQUEST_LOG=new_settings(max_batch_size=2)))
            send_request_log_to_cloud_watch_task()
            _dispatch_batch_mock.assert_called_once_with(client, log_group, log_stream, None, [
                create_batch_obj(cache_objects[0])])

        # when there are more cache keys than `MAX_BATCH_SIZE` make sure we call `_dispatch_batch_mock` multiple times
        log_stream = {'uploadSequenceToken': 'sequence_1'}
        cache_objects = [create_cache_obj(), create_cache_obj(timestamp_ms=1), create_cache_obj(timestamp_ms=2)]
        cache_mock = type('DummyCache', (object,), {})
        cache_mock.get = Mock(side_effect=[json.dumps(c) for c in cache_objects])
        cache_mock.set = Mock()
        cache_mock.iter_keys = Mock(return_value=['cache_key_01', 'cache_key_02', 'cache_key_03'])
        _dispatch_batch_mock = Mock(return_value='sequence_2')
        with ExitStack() as stack:
            setup_default_context(stack)
            # override `MAX_BATCH_SIZE`
            stack.enter_context(override_settings(REQUEST_LOG=new_settings(max_batch_size=2)))
            send_request_log_to_cloud_watch_task()
            _dispatch_batch_mock.assert_has_calls([
                call(client, log_group, log_stream, 'sequence_1', [
                    create_batch_obj(cache_objects[0]),
                    create_batch_obj(cache_objects[1])
                ]),
                call(client, log_group, log_stream, 'sequence_2', [create_batch_obj(cache_objects[2])])
            ])

        # the following tests make assumptions regarding the size of a cache object with an empty body
        default_cache_obj_size = len(json.dumps(create_cache_obj(request_body='')).encode('utf-8'))
        self.assertEqual(106, default_cache_obj_size)
        log_event_extra_bytes = 26

        # before a group of keys would exceed `MAX_BATCH_SIZE_BYTES`, make a call to `_dispatch_batch_mock` and then
        # continue iteration
        log_stream = {'uploadSequenceToken': 'sequence_1'}
        missing_bytes = 128 - (default_cache_obj_size + log_event_extra_bytes)
        cache_objects = [
            create_cache_obj(request_body='a' * missing_bytes),
            create_cache_obj(timestamp_ms=1, request_body='a' * missing_bytes),
            create_cache_obj(timestamp_ms=2, request_body='a' * missing_bytes)
        ]
        cache_mock = type('DummyCache', (object,), {})
        cache_mock.get = Mock(side_effect=[json.dumps(c) for c in cache_objects])
        cache_mock.set = Mock()
        cache_mock.iter_keys = Mock(return_value=['cache_key_01', 'cache_key_02', 'cache_key_03'])
        _dispatch_batch_mock = Mock(return_value='sequence_2')
        with ExitStack() as stack:
            setup_default_context(stack)
            # override `MAX_BATCH_SIZE_BYTES`
            stack.enter_context(override_settings(REQUEST_LOG=new_settings(max_batch_size_bytes=300)))
            send_request_log_to_cloud_watch_task()
            _dispatch_batch_mock.assert_has_calls([
                call(client, log_group, log_stream, 'sequence_1', [
                    create_batch_obj(cache_objects[0]),
                    create_batch_obj(cache_objects[1])
                ]),
                call(client, log_group, log_stream, 'sequence_2', [create_batch_obj(cache_objects[2])])
            ])

        # when a log is greater than `MAX_BATCH_SIZE_BYTES`, the current batch should be sent and then the big log
        # should have it's `request_body` truncated and sent as well
        log_stream = {'uploadSequenceToken': 'sequence_1'}
        cache_objects = [
            create_cache_obj(request_body='a' * missing_bytes),
            create_cache_obj(timestamp_ms=1, request_body='0123456789_0123456789_0123456789_0123456789'),
            create_cache_obj(timestamp_ms=2, request_body='a' * missing_bytes)
        ]
        cache_mock = type('DummyCache', (object,), {})
        cache_mock.get = Mock(side_effect=[json.dumps(c) for c in cache_objects])
        cache_mock.set = Mock()
        cache_mock.iter_keys = Mock(return_value=['cache_key_01', 'cache_key_02', 'cache_key_03'])
        _dispatch_batch_mock = Mock(return_value='sequence_2')
        with ExitStack() as stack:
            setup_default_context(stack)
            # override `MAX_BATCH_SIZE_BYTES`
            stack.enter_context(override_settings(REQUEST_LOG=new_settings(max_batch_size_bytes=150)))
            send_request_log_to_cloud_watch_task()
            _dispatch_batch_mock.assert_has_calls([
                call(client, log_group, log_stream, 'sequence_1', [create_batch_obj(cache_objects[0])]),
                call(client, log_group, log_stream, 'sequence_2', [create_batch_obj({
                    **cache_objects[1],
                    # override `request_body` with the expected truncated version
                    'request_body': '0123456789_012345',
                })]),
                call(client, log_group, log_stream, 'sequence_2', [create_batch_obj(cache_objects[2])]),
            ])

    def test_cache_error_msg(self):
        logging.disable(logging.NOTSET)  # allow logging

        # Check we get expected error for a different cache backend
        with override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}):
            with self.assertLogs(level='ERROR') as logs:
                send_request_log_to_cloud_watch_task()
            self.assertEqual(logs.output, [
                'ERROR:root:Expected \'default\' cache to be django-redis and have a function `iter_keys`.'])

        # Check we get expected error when the cache object is missing a specific function
        with patch('edualert.common.tasks.cache', new=type(object)):
            with self.assertLogs(level='ERROR') as logs:
                send_request_log_to_cloud_watch_task()
            self.assertEqual(logs.output, [
                'ERROR:root:Expected \'default\' cache to be django-redis and have a function `iter_keys`.'])

        # Check we get expected error when the cache object has the attribute we are looking for but it's not callable
        with patch('edualert.common.tasks.cache', new=type('DummyCache', (object,), {'iter_keys': '<not callable>'})):
            with self.assertLogs(level='ERROR') as logs:
                send_request_log_to_cloud_watch_task()
            self.assertEqual(logs.output, [
                'ERROR:root:Expected \'default\' cache to be django-redis and have a function `iter_keys`.'])

    def test_settings_error_msg(self):
        logging.disable(logging.NOTSET)  # allow logging

        # Check we get expected error when missing settings
        with self.assertLogs(level='ERROR') as logs:
            send_request_log_to_cloud_watch_task()
        self.assertEqual(logs.output, [
            "ERROR:root:Expected 'LOG_GROUP_NAME' and 'REGION_NAME' to be present in settings.REQUEST_LOG"])

        # Check we get expected error when missing settings
        with override_settings(REQUEST_LOG=''):
            with self.assertLogs(level='ERROR') as logs:
                send_request_log_to_cloud_watch_task()
            self.assertEqual(logs.output, [
                "ERROR:root:Expected 'LOG_GROUP_NAME' and 'REGION_NAME' to be present in settings.REQUEST_LOG"])

        # Check we get expected error when missing key in settings
        with override_settings(REQUEST_LOG={}):
            with self.assertLogs(level='ERROR') as logs:
                send_request_log_to_cloud_watch_task()
            self.assertEqual(logs.output, [
                "ERROR:root:Expected 'LOG_GROUP_NAME' and 'REGION_NAME' to be present in settings.REQUEST_LOG"])

        # Check we get expected error when missing key in settings
        with override_settings(REQUEST_LOG={'LOG_GROUP_NAME': ''}):
            with self.assertLogs(level='ERROR') as logs:
                send_request_log_to_cloud_watch_task()
            self.assertEqual(logs.output, [
                "ERROR:root:Expected 'LOG_GROUP_NAME' and 'REGION_NAME' to be present in settings.REQUEST_LOG"])

        # Check we get expected error when missing key in settings
        with override_settings(REQUEST_LOG={'REGION_NAME': ''}):
            with self.assertLogs(level='ERROR') as logs:
                send_request_log_to_cloud_watch_task()
            self.assertEqual(logs.output, [
                "ERROR:root:Expected 'LOG_GROUP_NAME' and 'REGION_NAME' to be present in settings.REQUEST_LOG"])

    def test__provide_log_group(self):
        log_group_name = 'DummyLogGroup'
        client = type('DummyClient', (object,), {})

        # when one log group is returned check that it will be returned by the function
        log_group = {}
        client.describe_log_groups = Mock(return_value={'logGroups': [log_group]})
        result = _provide_log_group(client, log_group_name)
        client.describe_log_groups.assert_called_once_with(logGroupNamePrefix=log_group_name)
        self.assertEqual(log_group, result)

        # when no log group is returned on the first call, check that we attempt to create one and then return it
        log_group = {}
        client.describe_log_groups = Mock(side_effect=[
            {'logGroups': []},
            {'logGroups': [log_group]}
        ])
        client.create_log_group = Mock()
        result = _provide_log_group(client, log_group_name)
        self.assertEqual(log_group, result)
        client.create_log_group.assert_called_once_with(logGroupName=log_group_name)
        client.describe_log_groups.assert_has_calls([
            call(logGroupNamePrefix=log_group_name), call(logGroupNamePrefix=log_group_name)])

        # when multiple log groups are returned check that we return the latest created one
        log_group_01 = {'creationTime': 0}
        log_group_02 = {'creationTime': 1}
        client.describe_log_groups = Mock(return_value={'logGroups': [log_group_01, log_group_02]})
        result = _provide_log_group(client, log_group_name)
        client.describe_log_groups.assert_called_once_with(logGroupNamePrefix=log_group_name)
        self.assertEqual(log_group_02, result)

    @patch('edualert.common.tasks.timezone.now', new=lambda: datetime(2020, 1, 1))
    def test__provide_log_stream(self):
        log_stream_name = '1-2020'
        log_group = {'logGroupName': 'DummyLogGroup'}
        client = type('DummyClient', (object,), {})

        # when one log stream is returned check that it will be returned by the function
        log_stream = {}
        client.describe_log_streams = Mock(return_value={'logStreams': [log_stream]})
        result = _provide_log_stream(client, log_group)
        client.describe_log_streams.assert_called_once_with(
            logGroupName=log_group['logGroupName'], logStreamNamePrefix=log_stream_name)
        self.assertEqual(log_stream, result)

        # when no log stream is returned on the first call, check that we attempt to create one and then return it
        log_stream = {}
        client.describe_log_streams = Mock(side_effect=[
            {'logStreams': []},
            {'logStreams': [log_stream]}
        ])
        client.create_log_stream = Mock()
        result = _provide_log_stream(client, log_group)
        client.create_log_stream.assert_called_once_with(
            logGroupName=log_group['logGroupName'], logStreamName=log_stream_name)
        client.describe_log_streams.assert_has_calls([
            call(logGroupName=log_group['logGroupName'], logStreamNamePrefix=log_stream_name),
            call(logGroupName=log_group['logGroupName'], logStreamNamePrefix=log_stream_name)
        ])
        self.assertEqual(log_stream, result)

        # when multiple log streams are returned check that we return the latest created one
        log_stream_01 = {'creationTime': 0}
        log_stream_02 = {'creationTime': 1}
        client.describe_log_streams = Mock(return_value={'logStreams': [log_stream_01, log_stream_02]})
        result = _provide_log_stream(client, log_group)
        client.describe_log_streams.assert_called_once_with(
            logGroupName=log_group['logGroupName'], logStreamNamePrefix=log_stream_name)
        self.assertEqual(log_stream_02, result)

    def test__dispatch_batch(self):
        logging.disable(logging.NOTSET)  # allow logging
        log_group = {'logGroupName': 'DummyLogGroup'}
        log_stream = {'logStreamName': 'DummyLogStream'}
        client = type('DummyClient', (object,), {})

        # when `sequence_token` is None it shouldn't be passed to `put_log_events`
        sequence_token = None
        batch = []
        client.put_log_events = Mock(return_value={'nextSequenceToken': 'dummySequence'})
        result = _dispatch_batch(client, log_group, log_stream, sequence_token, batch)
        client.put_log_events.assert_called_once_with(logGroupName=log_group['logGroupName'],
                                                      logStreamName=log_stream['logStreamName'], logEvents=batch)
        self.assertEqual('dummySequence', result)

        # when `sequence_token` is NOT None it should be passed to `put_log_events`
        sequence_token = 'dummy-sequence'
        batch = []
        client.put_log_events = Mock(return_value={'nextSequenceToken': 'dummySequence'})
        _dispatch_batch(client, log_group, log_stream, sequence_token, batch)
        client.put_log_events.assert_called_once_with(logGroupName=log_group['logGroupName'],
                                                      logStreamName=log_stream['logStreamName'],
                                                      logEvents=batch, sequenceToken=sequence_token)
        self.assertEqual('dummySequence', result)

        # batches should be ordered by `timestamp`
        sequence_token = None
        log_01 = {'timestamp': 1}
        log_02 = {'timestamp': 0}
        batch = [log_01, log_02]
        sorted_batch = [log_02, log_01]
        client.put_log_events = Mock(return_value={'nextSequenceToken': 'dummySequence'})
        _dispatch_batch(client, log_group, log_stream, sequence_token, batch)
        client.put_log_events.assert_called_once_with(logGroupName=log_group['logGroupName'],
                                                      logStreamName=log_stream['logStreamName'], logEvents=sorted_batch)
        self.assertEqual('dummySequence', result)

        # when an exception is thrown, log the exception and the batch and return the sequence token
        sequence_token = None
        batch = [{'timestamp': 0}]
        client.put_log_events = Mock(side_effect=Exception('Dummy exception'))
        with self.assertLogs(level='ERROR') as logs:
            _dispatch_batch(client, log_group, log_stream, sequence_token, batch)
        self.assertEqual(1, len(logs.output))
        self.assertTrue(logs.output[0].startswith("ERROR:root:Failed to send log events batch to Cloud Watch\n"
                                                  "Batch: [{'timestamp': 0}]"))
        client.put_log_events.assert_called_once_with(logGroupName=log_group['logGroupName'],
                                                      logStreamName=log_stream['logStreamName'], logEvents=batch)
        self.assertEqual('dummySequence', result)
