from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from email.mime.text import MIMEText
import base64
import requests
import time

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.compose']


def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('gmail', 'v1', http=creds.authorize(Http()))

    message = create_message(EMAIL_FROM, EMAIL_TO, EMAIL_SUBJECT, EMAIL_CONTENT)
    sent = send_message(service, 'me', message)


def create_message(sender, to, subject, message_text):
    """Create a message for an email.

    Args:
    sender: Email address of the sender.
    to: Email address of the receiver.
    subject: The subject of the email message.
    message_text: The text of the email message.

    Returns:
    An object containing a base64url encoded email object.
    """
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    return {'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()}


def send_message(service, user_id, message):
    """Send an email message.

    Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    message: Message to be sent.

    Returns:
    Sent Message.
    """
    message = (service.users().messages().send(userId=user_id, body=message).execute())
    print('Message Id: %s' % message['id'])
    return message


def getTriggered():
    """Return a list of tickers that meet a criteria

    Returns:
    A list of tickers that meet a criteria.
    """
    # Create full list from file, delete header and remove duplicates
    ticker_list = []
    for line in open("constituents_csv.csv", "r+"):
        ticker_list.append(line.split(",")[0].lower())
    del (ticker_list[0])
    ticker_list = set(ticker_list)

    # Instantiate final list, iterate through universe to get data, calculate indicators, and add to final list if criteria met
    triggered = []
    iter = 0
    for ticker in ticker_list:
        url = "https://api.iextrading.com/1.0/stock/" + ticker.lower() + "/chart/1y?filter=close"
        sma1L = 13
        sma2L = 34
        f = requests.get(url).json()
        closes = [day['close'] for day in f]
        sma1a = sum(closes[-1 - sma1L:-1:]) / sma1L
        sma2a = sum(closes[-1 - sma2L:-1:]) / sma2L
        diff_a = sma1a - sma2a
        sma1b = sum(closes[-sma1L::]) / sma1L
        sma2b = sum(closes[-sma2L::]) / sma2L
        diff_b = sma1b - sma2b

        if not diff_a > 0 and diff_b > 0:
            triggered.append(ticker)
        iter += 1
        print("Progress: " + str(100 * iter / len(ticker_list)) + "%")
        
        # To prevent IP throttle
        time.sleep(0.03)
    return triggered

# Email Parts
EMAIL_FROM = 'pspetev@gmail.com'
EMAIL_TO = 'stoyanpetev@gmail.com'
EMAIL_SUBJECT = 'Stock Alert'
EMAIL_CONTENT = 'Here are the Stocks that meet your criteria:'
stocks = getTriggered()
for stock in stocks:
    EMAIL_CONTENT = EMAIL_CONTENT + "\n" + stock
# Send Email
main()

