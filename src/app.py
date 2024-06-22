#!/usr/bin/env python3
import os
import boto3
import logging
from flask import Flask, request, jsonify

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

# Add this new route to receive advice from the Spring Boot application
@app.route("/receive_advice", methods=["POST"])
def receive_advice():
    try:
        advice = request.json.get("advice")
        if advice:
            logging.debug(f"Received advice: {advice}")
            return jsonify({'message': advice})
        else:
            logging.error("No advice provided in the request")
            return jsonify({'message': 'No advice provided'}), 400
    except Exception as e:
        logging.error(f"Error in receive_advice: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5111)
