from unittest.mock import patch, MagicMock

from ddt import ddt
from django.utils import timezone
from django.utils.timezone import utc

from edualert.common.api_tests import CommonAPITestCase
from edualert.notifications.models import SentEmailAlternative
from edualert.notifications.utils import send_mail, send_mass_mail


@ddt
class SentMailTestCase(CommonAPITestCase):
    def test_sent_mail(self):
        with patch('edualert.notifications.utils.emails.EmailMultiAlternatives.send') as patched_send:
            send_mail("Test subject", {
                'text/plain': 'Test content'
            }, 'from@example.com', ["to-bcc@example.com"], ["to-cc@example.com"])
            self.assertEqual(1, patched_send.call_count)

        alternatives = SentEmailAlternative.objects.all()
        self.assertEqual(1, len(alternatives))
        self.assert_sent_email_alternative(
            alternatives[0],
            from_addr='from@example.com',
            subject='Test subject',
            bcc='to-bcc@example.com',
            cc='to-cc@example.com',
            mime_type='text/plain',
            content='Test content',
        )

    def test_sent_mail_without_cc(self):
        with patch('edualert.notifications.utils.emails.EmailMultiAlternatives.send') as patched_send:
            send_mail("Test subject", {
                'text/plain': 'Test content'
            }, 'from@example.com', ["to-bcc@example.com"])
            self.assertEqual(1, patched_send.call_count)

        alternatives = SentEmailAlternative.objects.all()
        self.assertEqual(1, len(alternatives))
        self.assert_sent_email_alternative(
            alternatives[0],
            from_addr='from@example.com',
            subject='Test subject',
            bcc='to-bcc@example.com',
            cc='',
            mime_type='text/plain',
            content='Test content',
        )

    def test_sent_mail_multiple_cc(self):
        with patch('edualert.notifications.utils.emails.EmailMultiAlternatives.send') as patched_send:
            send_mail("Test subject", {
                'text/plain': 'Test content'
            }, 'from@example.com', ["to-bcc@example.com"], ["to-cc1@example.com", "to-cc2@example.com"])
            self.assertEqual(1, patched_send.call_count)

        alternatives = SentEmailAlternative.objects.all()
        self.assertEqual(1, len(alternatives))
        self.assert_sent_email_alternative(
            alternatives[0],
            from_addr='from@example.com',
            subject='Test subject',
            bcc='to-bcc@example.com',
            cc='to-cc1@example.com,to-cc2@example.com',
            mime_type='text/plain',
            content='Test content',
        )

    def test_sent_mail_multiple_bcc(self):
        with patch('edualert.notifications.utils.emails.EmailMultiAlternatives.send') as patched_send:
            send_mail("Test subject", {
                'text/plain': 'Test content'
            }, 'from@example.com', ["to-bcc1@example.com", "to-bcc2@example.com"], ["to-cc@example.com"])
            self.assertEqual(1, patched_send.call_count)

        alternatives = SentEmailAlternative.objects.all()
        self.assertEqual(1, len(alternatives))
        self.assert_sent_email_alternative(
            alternatives[0],
            from_addr='from@example.com',
            subject='Test subject',
            bcc='to-bcc1@example.com,to-bcc2@example.com',
            cc='to-cc@example.com',
            mime_type='text/plain',
            content='Test content',
        )

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 8, 13).replace(tzinfo=utc))
    def test_sent_mail_multiple_bodies(self, _):
        with patch('edualert.notifications.utils.emails.EmailMultiAlternatives.send') as patched_send:
            send_mail("Test subject", {
                'text/plain': 'Test plain content',
                'text/html': 'Test html content',
            }, 'from@example.com', ["to-bcc@example.com"], ["to-cc@example.com"])
            self.assertEqual(1, patched_send.call_count)

        alternatives = SentEmailAlternative.objects.all()
        sent_at = timezone.datetime(2020, 8, 13).replace(tzinfo=utc)
        self.assertEqual(2, len(alternatives))
        self.assert_sent_email_alternative(
            alternatives[0],
            from_addr='from@example.com',
            subject='Test subject',
            bcc='to-bcc@example.com',
            cc='to-cc@example.com',
            mime_type='text/plain',
            content='Test plain content',
            sent_at=sent_at,
        )
        self.assert_sent_email_alternative(
            alternatives[1],
            from_addr='from@example.com',
            subject='Test subject',
            bcc='to-bcc@example.com',
            cc='to-cc@example.com',
            mime_type='text/html',
            content='Test html content',
            sent_at=sent_at,
        )

    def test_sent_mass_mail(self):
        timezone_now_mock = create_timezone_now_mock([
            timezone.datetime(2020, 9, 13).replace(tzinfo=utc),
            timezone.datetime(2020, 8, 13).replace(tzinfo=utc),
        ])
        mock_connection = type('Connection', (object,), {
            'send_messages': MagicMock()
        })

        with patch('django.utils.timezone.now', new=timezone_now_mock):
            send_mass_mail([
                ("Test subject 1", {'text/plain': 'Test content 1'}, 'from@example.com', ["to-bcc-1@example.com"], ["to-cc-1@example.com"]),
                ("Test subject 2", {'text/plain': 'Test content 2'}, 'from@example.com', ["to-bcc-2@example.com"], ["to-cc-2@example.com"]),
            ], connection=mock_connection)
            self.assertEqual(1, mock_connection.send_messages.call_count)

        alternatives = SentEmailAlternative.objects.all()
        self.assertEqual(2, len(alternatives))
        self.assert_sent_email_alternative(
            alternatives[0],
            from_addr='from@example.com',
            subject='Test subject 1',
            bcc='to-bcc-1@example.com',
            cc='to-cc-1@example.com',
            mime_type='text/plain',
            content='Test content 1',
            sent_at=timezone.datetime(2020, 9, 13).replace(tzinfo=utc),
        )
        self.assert_sent_email_alternative(
            alternatives[1],
            from_addr='from@example.com',
            subject='Test subject 2',
            bcc='to-bcc-2@example.com',
            cc='to-cc-2@example.com',
            mime_type='text/plain',
            content='Test content 2',
            sent_at=timezone.datetime(2020, 8, 13).replace(tzinfo=utc),
        )

    def assert_sent_email_alternative(self, obj, from_addr, subject, bcc, cc, mime_type, content, sent_at=None):
        self.assertEqual(from_addr, obj.from_email)
        self.assertEqual(subject, obj.subject)
        self.assertEqual(bcc, obj.bcc)
        self.assertEqual(cc, obj.cc)
        self.assertEqual(mime_type, obj.mime_type)
        self.assertEqual(content, obj.content)

        if sent_at:
            self.assertEqual(obj.sent_at, sent_at)


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
