#!/usr/bin/env python3
import requests
from flask import Flask, request

app = Flask(__name__)


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
    response = requests.get("https://api.adviceslip.com/advice")

    if response.status_code == 200:
        advice_data = response.json()
        advice = advice_data.get("slip", {}).get("advice", "No advice available.")
    else:
        advice = "Failed to retrieve advice."

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
                <p>Your advice for today is:</p>
                <blockquote>{advice}</blockquote>
                <a href="/">Get another advice</a>
            </div>
        </body>
    </html>
    '''
