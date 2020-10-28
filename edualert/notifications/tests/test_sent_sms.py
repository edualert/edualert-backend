from unittest.mock import patch, MagicMock

from ddt import ddt
from django.test import override_settings
from django.utils import timezone
from django.utils.timezone import utc

from edualert.common.api_tests import CommonAPITestCase
from edualert.notifications.models import SentSms
from edualert.notifications.utils import send_sms


@ddt
class SentSmsTestCase(CommonAPITestCase):
    @override_settings(SEND_SMS=True)
    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 8, 13).replace(tzinfo=utc))
    def test_sent_sms(self, _):
        with patch('edualert.notifications.utils.sms.requests.post') as patched_post:
            send_sms([('0123456789', 'Test sms')])
            self.assertEqual(1, patched_post.call_count)

        sms = SentSms.objects.all()
        sent_at = timezone.datetime(2020, 8, 13).replace(tzinfo=utc)
        self.assertEqual(1, len(sms))
        self.assert_sent_sms(
            sms[0],
            recipient='0123456789',
            message='Test sms',
            sent_at=sent_at,
        )

    @override_settings(SEND_SMS=True)
    @patch('time.time', return_value=123456789.123456789)
    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 8, 13).replace(tzinfo=utc))
    def test_sent_sms_nonce(self, _time, _now):
        with patch('edualert.notifications.utils.sms.requests.post') as patched_post:
            send_sms([('0123456789', 'Test sms')])
            self.assertEqual(1, patched_post.call_count)

        sms = SentSms.objects.all()
        sent_at = timezone.datetime(2020, 8, 13).replace(tzinfo=utc)
        self.assertEqual(1, len(sms))
        self.assert_sent_sms(
            sms[0],
            recipient='0123456789',
            message='Test sms',
            sent_at=sent_at,
            nonce='123456789',
        )

    @override_settings(SEND_SMS=True)
    def test_sent_sms_multiple(self):
        # mock: django.utils.timezone.now
        # We only mock the call for the first 2 times. Afterwards we call the original function.
        # Assuming the other calls come from the 'created' and 'modified' fields on the models.
        timezone_now_mock = create_timezone_now_mock([
            timezone.datetime(2020, 9, 13).replace(tzinfo=utc),
            timezone.datetime(2020, 8, 13).replace(tzinfo=utc),
        ])
        time_time_mock = MagicMock(side_effect=[123456789.123456789, 234567891.234567891])

        with patch('edualert.notifications.utils.sms.requests.post') as patched_post:
            with patch('django.utils.timezone.now', new=timezone_now_mock):
                with patch('time.time', new=time_time_mock):
                    send_sms([('0123456789', 'Test sms 1'), ('1234567890', 'Test sms 2')])
            self.assertEqual(2, patched_post.call_count)

        sms = SentSms.objects.all()
        self.assertEqual(2, len(sms))
        self.assert_sent_sms(
            sms[0],
            recipient='0123456789',
            message='Test sms 1',
            sent_at=timezone.datetime(2020, 9, 13).replace(tzinfo=utc),
            nonce='123456789',
        )
        self.assert_sent_sms(
            sms[1],
            recipient='1234567890',
            message='Test sms 2',
            sent_at=timezone.datetime(2020, 8, 13).replace(tzinfo=utc),
            nonce='234567891',
        )

    def assert_sent_sms(self, obj, recipient, message, sent_at=None, nonce=None):
        self.assertEqual(recipient, obj.recipient)
        self.assertEqual(message, obj.message)

        if sent_at:
            self.assertEqual(obj.sent_at, sent_at)

        if nonce:
            self.assertEqual(obj.nonce, nonce)


def create_timezone_now_mock(return_values):
    timezone_now_index = 0
    original_timezone_now = timezone.now

    def timezone_now():
        nonlocal timezone_now_index

        if timezone_now_index < len(return_values):
            value = return_values[timezone_now_index]
        else:
            value = original_timezone_now()
        timezone_now_index += 1
        return value

    return MagicMock(side_effect=timezone_now)
