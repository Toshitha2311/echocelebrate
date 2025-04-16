import sys
import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from twilio.rest import Client
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import pytz

# Add Scripts folder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Scripts'))

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Replace with your real Twilio credentials
TWILIO_SID = 'ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'  # Replace with your Twilio SID
TWILIO_AUTH_TOKEN = 'your_auth_token'  # Replace with your Twilio Auth Token
TWILIO_PHONE_NUMBER = '+17756286910'  # Replace with your real Twilio phone number (in E.164 format)

client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Function to send SMS
def send_sms_to_user(name, phone, link):
    try:
        logger.debug(f"Sending SMS to {phone} with link: {link}")  # Log details about the SMS
        message = client.messages.create(
            body=f"Hi {name}, check this link: {link}",
            from_=TWILIO_PHONE_NUMBER,
            to=phone
        )
        logger.info(f"SMS sent to {phone}. SID: {message.sid}")
    except Exception as e:
        logger.error(f"Failed to send SMS to {phone}: {str(e)}")  # Log specific error

@app.route('/send-sms', methods=['POST'])
def send_sms():
    data = request.json
    name = data.get('name')
    phone = data.get('phone')
    link = data.get('link')
    schedule_time = data.get('schedule_time')

    logger.debug(f"Received data: {data}")  # Log the received data

    try:
        # Validate that all necessary data is present
        if not name or not phone or not link or not schedule_time:
            logger.error('Missing required fields.')
            return jsonify({'error': 'Missing required fields'}), 400

        # Parse the schedule time to a datetime object
        schedule_time = datetime.strptime(schedule_time, "%Y-%m-%dT%H:%M")  # Converts from string to datetime
        schedule_time = pytz.timezone('Asia/Kolkata').localize(schedule_time)  # Adjust timezone if needed
        logger.debug(f"Parsed schedule time: {schedule_time}")

        # Create a unique job identifier based on phone number and schedule time
        job_id = f"send_sms_{phone}_{schedule_time.strftime('%Y%m%d%H%M')}"

        # Check if job already exists
        if scheduler.get_job(job_id):
            logger.error(f"Job with ID {job_id} already exists.")
            return jsonify({'error': 'A job with this identifier already exists'}), 400

        # Schedule the SMS to be sent at the specified time with a unique job identifier
        scheduler.add_job(
            send_sms_to_user,
            'date',
            run_date=schedule_time,
            args=[name, phone, link],
            id=job_id  # Use the unique job ID
        )

        logger.info(f"Job scheduled: {job_id} at {schedule_time.strftime('%Y-%m-%d %H:%M:%S')}")
        return jsonify({'status': f'SMS will be sent to {phone} at {schedule_time.strftime("%Y-%m-%d %H:%M:%S")}'})

    except Exception as e:
        logger.error(f"Error while processing request: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
