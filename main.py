import requests
import os
import datetime as dt
import smtplib
from email.mime.text import MIMEText

ALERT_PERCENT_AMOUNT = 5  # Set this to the percentage difference you want the alert to be triggered by.

STOCK = "TSLA"
COMPANY_NAME = "Tesla Inc"

#  Date Calculations
yesterday = dt.datetime.today().date() - dt.timedelta(days=1)  # Gets today's date and subtracts 1
day_before = dt.datetime.today().date() - dt.timedelta(days=2)

#  Alpha Advantage Stock Price API
ALPHA_ADVANTAGE_API_KEY = os.environ.get("ALPHA_ADVANTAGE_API_KEY")
alpha_advantage_endpoint = "https://www.alphavantage.co/query"
stock_parameters = {
    "function": "TIME_SERIES_DAILY",
    "symbol": STOCK,
    "apikey": ALPHA_ADVANTAGE_API_KEY,
    "outputsize": 2
}
stock_response = requests.get(url=alpha_advantage_endpoint, params=stock_parameters)
stock_response.raise_for_status()
stock_data = stock_response.json()

#  Stock price calculation
yesterday_close_stock_price = float(stock_data["Time Series (Daily)"][str(yesterday)]["4. close"])
day_before_close_stock_price = float(stock_data["Time Series (Daily)"][str(day_before)]["4. close"])
percentage_difference = round(((abs(day_before_close_stock_price - yesterday_close_stock_price) /
                                day_before_close_stock_price) * 100), 2)

#  News API. An email will be sent only if the percentage difference between the close yesterday and the day before
#  is greater than the constant ALERT_PERCENT_AMOUNT.
if percentage_difference >= ALERT_PERCENT_AMOUNT:
    NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
    news_api_endpoint = "https://newsapi.org/v2/everything"
    news_parameters = {
        "q": COMPANY_NAME,
        "apikey": NEWS_API_KEY,
        "searchin": "title,description"
    }
    news_response = requests.get(url=news_api_endpoint, params=news_parameters)
    news_response.raise_for_status()
    news_data_articles = news_response.json()["articles"][:3]  # Gets the first three articles containing Tesla

    stock_alert_list = [
        f"Headline: {entry['title']}\nBrief: {entry['description']}\n\n" for entry in news_data_articles
    ]
    stock_alert_string = ''.join(stock_alert_list).encode("utf-8")

    #  Getting
    EMAIL = os.environ.get("EMAIL")
    PASSWORD = os.environ.get("PASSWORD")

    #  Create a MIMEText object with the encoded text
    msg = MIMEText(stock_alert_string, 'plain', 'utf-8')

    #  Setting Up Subject 🔻 if going down, else 🔺 if price going up
    if day_before_close_stock_price > yesterday_close_stock_price:
        msg['Subject'] = f"{STOCK}: 🔻{percentage_difference}%"
    else:
        msg['Subject'] = f"{STOCK}: 🔺{percentage_difference}%"

    # Setting up remaining email parameters
    msg['From'] = EMAIL
    msg['To'] = EMAIL

    with smtplib.SMTP("smtp.gmail.com", 587) as connection:
        connection.starttls()
        connection.login(user=EMAIL, password=PASSWORD)
        connection.send_message(msg)
