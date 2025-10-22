from twilio.rest import Client
# Twilio credentials
account_sid = "ACcbc75d147cf1520dfa533d94a851856b"
auth_token = "cc49339cc44325ed0150f41a398df924"
client = Client(account_sid, auth_token)
# Fetch all calls from a specific number
calls = client.calls.list(from_="+17473024240", page_size=2000)
for call in calls:
     print(
        call.sid,
        call.from_formatted,
        call.to_formatted,
        call.status,
        call.start_time,
        call.duration  # duration in seconds (string or None if not completed)
    )






