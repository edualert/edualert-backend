import base64
import hashlib
import json
import math
import time
import requests

from django.conf import settings
from django.utils import timezone


def send_sms(sms_to_send):
    from edualert.notifications.models import SentSms

    if not settings.SEND_SMS:
        return

    host = "https://www.web2sms.ro"
    url = "/prepaid/message"
    http_method = "POST"

    sent_sms = []
    for sms in sms_to_send:
        req_data = {
            "apiKey": settings.WEB2SMS_API_KEY,
            "sender": "",
            "recipient": sms[0],
            "message": sms[1],
            "scheduleDatetime": "",
            "validityDatetime": "",
            "callbackUrl": "",
            "visibleMessage": "",
            "userData": "",
            "nonce": str(math.floor(time.time()))
        }

        concatenated_data = req_data['apiKey'] + req_data['nonce'] + http_method + url + req_data['sender'] + req_data['recipient'] + \
                            req_data['message'] + req_data['visibleMessage'] + req_data['scheduleDatetime'] + req_data['validityDatetime'] + \
                            req_data['callbackUrl'] + settings.WEB2SMS_SECRET_KEY
        signature = hashlib.sha512(concatenated_data.encode('utf-8')).hexdigest()
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Basic " + base64.b64encode((settings.WEB2SMS_API_KEY + ':' + signature).encode('utf-8')).decode('ascii')
        }

        requests.post(host + url, data=json.dumps(req_data), headers=headers)
        sent_sms.append(SentSms(
            recipient=req_data['recipient'],
            message=req_data['message'],
            nonce=req_data['nonce'],
            sent_at=timezone.now(),
        ))

    SentSms.objects.bulk_create(sent_sms)
