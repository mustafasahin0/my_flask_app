#!/usr/bin/env python3
import os
import boto3
import logging
from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import requests

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Configure AWS SQS
sqs_client = boto3.client(
    'sqs',
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
    region_name=os.environ.get('AWS_REGION')
)
request_queue_url = 'https://sqs.us-east-2.amazonaws.com/975050009455/advice-request'
response_queue_url = 'https://sqs.us-east-2.amazonaws.com/975050009455/advice-response'

# Spring Boot endpoint for fetching feedback
spring_boot_feedback_url = 'http://3.139.92.152:8080/api/v1/feedback'

@app.route("/")
def main():
    return '''
    <html>
        <head>
            <title>Get Your Daily Advice</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #f0f0f0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }
                .container {
                    background-color: #fff;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    text-align: center;
                }
                .container input[type="text"], .container input[type="submit"] {
                    padding: 10px;
                    margin: 10px 0;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                }
                .container input[type="submit"] {
                    background-color: #007BFF;
                    color: white;
                    border: none;
                    cursor: pointer;
                }
                .container input[type="submit"]:hover {
                    background-color: #0056b3;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Get Your Daily Advice</h1>
                <form action="/echo_user_input" method="POST">
                    <label for="user_input">Enter your name:</label><br>
                    <input id="user_input" name="user_input" type="text" placeholder="Your Name"><br>
                    <input type="submit" value="Submit!">
                </form>
            </div>
        </body>
    </html>
    '''

@app.route("/echo_user_input", methods=["POST"])
def echo_input():
    input_text = request.form.get("user_input", "")

    # Send message to SQS request queue
    logging.debug(f"Sending message to SQS request queue: {input_text}")
    response = sqs_client.send_message(
        QueueUrl=request_queue_url,
        MessageBody=input_text
    )

    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        message = "Message sent to SQS successfully."
        logging.debug("Message sent to SQS request queue successfully.")
    else:
        message = "Failed to send message to SQS."
        logging.error("Failed to send message to SQS request queue.")

    return f'''
    <html>
        <head>
            <title>Your Advice</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f0f0f0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }}
                .container {{
                    background-color: #fff;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Hi {input_text},</h1>
                <p>{message}</p>
                <p>Waiting for advice...</p>
                <script>
                    setTimeout(function() {{
                        fetch('/get_advice')
                            .then(response => response.json())
                            .then(data => {{
                                document.querySelector('.container').innerHTML = `
                                    <h1>Hi {input_text},</h1>
                                    <p>${{data.message}}</p>
                                    <form action="/submit_feedback" method="POST">
                                        <input type="hidden" name="name" value="{input_text}">
                                        <input type="hidden" name="advice" value="${{data.message}}">
                                        <label for="feedback">How did this advice make you feel?</label><br>
                                        <button type="submit" name="feedback" value="happy">Happy</button>
                                        <button type="submit" name="feedback" value="neutral">Neutral</button>
                                        <button type="submit" name="feedback" value="sad">Sad</button>
                                    </form>
                                    <a href="/">Get another advice</a>
                                `;
                            }});
                    }}, 5000);  // Wait 5 seconds before fetching advice
                </script>
            </div>
        </body>
    </html>
    '''

@app.route("/get_advice", methods=["GET"])
def get_advice():
    logging.debug("Polling SQS for messages.")
    # Fetch the latest message from SQS response queue
    response = sqs_client.receive_message(
        QueueUrl=response_queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=10  # Long polling for 10 seconds
    )

    if 'Messages' in response:
        message = response['Messages'][0]
        advice = message['Body']
        logging.debug(f"Received advice: {advice}")
        # Delete received message from queue
        sqs_client.delete_message(
            QueueUrl=response_queue_url,
            ReceiptHandle=message['ReceiptHandle']
        )
        return jsonify({'message': advice})
    else:
        logging.debug("No messages found in SQS.")
        return jsonify({'message': 'No advice available at the moment'}), 404

@app.route("/submit_feedback", methods=["POST"])
def submit_feedback():
    name = request.form.get("name")
    advice = request.form.get("advice")
    feedback = request.form.get("feedback")
    timestamp = datetime.now()

    # Send feedback to Spring Boot application
    feedback_data = {
        'name': name,
        'advice': advice,
        'feedback': feedback,
        'timestamp': timestamp.isoformat()
    }

    spring_boot_url = 'http://3.139.92.152:8080/api/v1/feedback'
    try:
        requests.post(spring_boot_url, json=feedback_data)
    except Exception as e:
        logging.error(f"Failed to send feedback to Spring Boot application: {str(e)}")

    return f'''
    <html>
        <head>
            <title>Thank You!</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f0f0f0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }}
                .container {{
                    background-color: #fff;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Thank you for your feedback!</h1>
                <p>We appreciate your input.</p>
                <a href="/">Get another advice</a>
            </div>
        </body>
    </html>
    '''

@app.route("/feedback_analytics", methods=["GET"])
def feedback_analytics():
    # Fetch feedback from Spring Boot application
    try:
        response = requests.get(spring_boot_feedback_url)
        response.raise_for_status()
        feedback_data = response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch feedback from Spring Boot application: {str(e)}")
        feedback_data = []

    # Basic analytics
    total_feedback = len(feedback_data)
    happy_count = sum(1 for feedback in feedback_data if feedback['feedback'] == 'happy')
    neutral_count = sum(1 for feedback in feedback_data if feedback['feedback'] == 'neutral')
    sad_count = sum(1 for feedback in feedback_data if feedback['feedback'] == 'sad')

    return render_template_string('''
    <html>
        <head>
            <title>Feedback Analytics</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #f0f0f0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }
                .container {
                    background-color: #fff;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    text-align: center;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Feedback Analytics</h1>
                <p>Total feedbacks received: {{ total_feedback }}</p>
                <p>Happy feedbacks: {{ happy_count }}</p>
                <p>Neutral feedbacks: {{ neutral_count }}</p>
                <p>Sad feedbacks: {{ sad_count }}</p>
            </div>
        </body>
    </html>
    ''', total_feedback=total_feedback, happy_count=happy_count, neutral_count=neutral_count, sad_count=sad_count)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5111)
