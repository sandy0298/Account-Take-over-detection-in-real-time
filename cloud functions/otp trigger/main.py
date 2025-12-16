import base64
import functions_framework
import smtplib
import random
from email.mime.text import MIMEText
from google.cloud import tasks_v2
import json
import datetime

# ---------- EMAIL CONFIG ----------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "XXXXXXai@gmail.com"
SENDER_PASSWORD = "XXXX XXXX XXXX XXXX"  # Gmail App Password
RECEIVER_EMAIL = "XXXXXXXXXX@gmail.com"  # Can be dynamic if needed

# ---------- CLOUD TASKS CONFIG ----------
PROJECT_ID = "liquid-XXXX-XXXX-e3"
QUEUE_ID = "otp-checker-queue"
REGION = "us-central1"
FUNCTION_B_URL = "https://twillioXXXXX-XXXXXXX.us-central1.run.app"  # HTTP trigger of Function B


def send_email(otp):
    subject = "Important: Unusual Activity Detected on Your Account"

    body = f"""
Dear Sandeep,

Our security systems have identified unusual activity associated with your account.
As part of our verification process, please confirm whether this activity was
performed by you.

To complete verification, use the following one-time passcode (OTP):

OTP: {otp}

If you did not initiate any recent activity, please review your account settings
and recent actions for your safety.

Thank you,
Your Financial Service – Security Team
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
    server.quit()


def schedule_task(otp):
    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(PROJECT_ID, REGION, QUEUE_ID)

    payload = json.dumps({
        "otp": otp
    }).encode()

    schedule_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=15)

    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": FUNCTION_B_URL,
            "headers": {"Content-Type": "application/json"},
            "body": payload,
        },
        "schedule_time": schedule_time
    }

    client.create_task(parent=parent, task=task)
    print("Cloud Task scheduled for OTP check")


@functions_framework.cloud_event
def hello_pubsub(cloud_event):
    """Triggered by Pub/Sub message"""
    raw_message = base64.b64decode(
        cloud_event.data["message"]["data"]
    ).decode("utf-8")

    print("Received Pub/Sub message:", raw_message)

    # Generate OTP
    otp = random.randint(100000, 999999)
    print("Generated OTP:", otp)

    # 1️⃣ Send email
    send_email(otp)

    # 2️⃣ Schedule Cloud Task to call Function B after 30 seconds
    schedule_task(otp)

    return "Email sent and Cloud Task scheduled"
