#!/usr/bin/env python3
import os
import boto3
import requests
from flask import Flask, request

app = Flask(__name__)

# Configure AWS SQS
sqs_client = boto3.client(
    'sqs',
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
    region_name=os.environ.get('AWS_REGION')
)
queue_url = 'https://sqs.us-east-2.amazonaws.com/975050009455/advice-queue'


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

    # Send message to SQS
    response = sqs_client.send_message(
        QueueUrl=queue_url,
        MessageBody=input_text
    )

    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        message = "Message sent to SQS successfully."
    else:
        message = "Failed to send message to SQS."

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
                <a href="/">Get another advice</a>
            </div>
        </body>
    </html>
    '''


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5111)