from twilio.rest import Client
import os
import sys

from backend.settings import twilio_account_sid, twilio_auth, messaging_service_sid

client = Client(twilio_account_sid, twilio_auth)

def send_sms(number, body):
    """
    Send SMS message to input number with input body using Twilio messaging.
    """
    message = client.messages.create(
        messaging_service_sid=messaging_service_sid, body=body, to=number
    )
    return message.sid
