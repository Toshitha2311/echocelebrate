from flask import Flask, request, jsonify
from flask_cors import CORS
from twilio.rest import Client
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import pytz
import time

app = Flask(__name__)
CORS(app)

# Replace with your real Twilio credentials
TWILIO_SID = 'AC5c1fd95b233da4b96353d70e156285e1'
TWILIO_AUTH_TOKEN = '65b1c1711a5717f3c1867ee7e1cb45d9'
TWILIO_PHONE_NUMBER = '+17756286910'  # <-- Replace this with your real Twilio number in E.164 format

client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Function to send SMS
def send_sms_to_user(name, phone, link):
    try:
        message = client.messages.create(
            body=f"Hi {name}, check this link: {link}",
            from_=TWILIO_PHONE_NUMBER,
            to=phone
        )
        print(f"SMS sent to {phone}. SID: {message.sid}")
    except Exception as e:
        print(f"Failed to send SMS: {str(e)}")

@app.route('/send-sms', methods=['POST'])
def send_sms():
    data = request.json
    name = data.get('name')
    phone = data.get('phone')
    link = data.get('link')
    schedule_time = data.get('schedule_time')

    try:
        # Parse the schedule time to a datetime object
        schedule_time = datetime.strptime(schedule_time, "%Y-%m-%dT%H:%M")  # Converts from string to datetime
        schedule_time = pytz.timezone('Asia/Kolkata').localize(schedule_time)  # Adjust timezone if needed

        # Create a unique job identifier based on phone number and schedule time
        job_id = f"send_sms_{phone}_{schedule_time.strftime('%Y%m%d%H%M')}"

        # Check if job already exists
        if scheduler.get_job(job_id):
            return jsonify({'error': 'A job with this identifier already exists'}), 400

        # Schedule the SMS to be sent at the specified time with a unique job identifier
        scheduler.add_job(
            send_sms_to_user,
            'date',
            run_date=schedule_time,
            args=[name, phone, link],
            id=job_id  # Use the unique job ID
        )

        return jsonify({'status': f'SMS will be sent to {phone} at {schedule_time.strftime("%Y-%m-%d %H:%M:%S")}'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
