import functions_framework
from twilio.rest import Client

# Twilio Config
TWILIO_SID = "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
TWILIO_TOKEN = "02XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
TWILIO_FROM = "+1XXXXXX72082"
TWILIO_TO = "+91XXXXXXXX4"


def make_twilio_call(otp):
    client = Client(TWILIO_SID, TWILIO_TOKEN)


    twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">
        Dear Sandeep,
    </Say>
    <Pause length="1"/>
    <Say voice="alice">
        This call is on behalf of XYZ Bank.
    </Say>
    <Pause length="1"/>
    <Say voice="alice">
        We have detected some suspicious activity in your account.
    </Say>
    <Pause length="1"/>
    <Say voice="alice">
        No verification was done via email.
    </Say>
    <Pause length="1"/>
    <Say voice="alice">
        Please authenticate yourself now to continue using banking services.
    </Say>
    <Pause length="2"/>
</Response>"""


    call = client.calls.create(
        twiml=twiml,
        to=TWILIO_TO,
        from_=TWILIO_FROM
    )

    print("Twilio call initiated:", call.sid)
    return call.sid


@functions_framework.http
def verify_otp(request):
    """
    HTTP Cloud Function triggered by Cloud Task.
    Always initiates IVR call (non-blocking) since we can't pull Pub/Sub synchronously.
    """

    req = request.get_json(silent=True)
    if not req:
        return ("Invalid payload", 400)

    otp = req.get("otp")
    session_id = req.get("session_id", "N/A")

    print(f"Function B triggered for session: {session_id}")
    print(f"OTP to call: {otp}")

    # Directly make Twilio IVR call
    make_twilio_call(otp)

    return "IVR Call initiated (non-blocking)", 200
