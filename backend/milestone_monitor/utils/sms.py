from twilio.rest import Client
import os
import sys

curr_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(curr_dir))
sys.path.insert(0, parent_dir)

from config import twilio_account_sid, twilio_auth, messaging_service_sid

client = Client(twilio_account_sid, twilio_auth)

def send_sms(number, body):
    """
    Send SMS message to input number with input body using Twilio messaging.
    """
    message = client.messages.create(
        messaging_service_sid=messaging_service_sid,
        body=body,
        to=number
    )
    return message.sid

