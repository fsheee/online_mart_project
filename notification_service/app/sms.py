def send_sms(phone_number: str, message: str):
    # Simulate SMS sending
    print(f"Sending SMS to {phone_number}: {message}")
    return {"status": 200, "message": f"SMS sent to {phone_number}"}
