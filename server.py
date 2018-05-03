import boto3
import json
import requests
from botocore.exceptions import ClientError


def do_get(url, params=None):
    r = requests.get(url, params)
    print(f'status code {r.status_code}')
    print(f'{r.text}')
    return r.status_code, json.loads(r.text)


def get_ticker(currency_id):
    url = f'https://api.coinmarketcap.com/v1/ticker/{currency_id}'
    status_code, data = do_get(url)
    return status_code, data


def get_percent_changes(currency_id):
    status_code, data = get_ticker(currency_id)
    if status_code != 200:
        print('Got nothing')
        return None
    data = data[0]
    changes = {
        '1h': float(data['percent_change_1h']),
        '24h': float(data['percent_change_24h']),
        '7d': float(data['percent_change_7d']),
    }
    return changes


def send_email(p_change):
    to = 'muchprivacy@tuta.io'
    sender = 'muchprivacy@tuta.io'
    client = boto3.client('ses')
    charset = "UTF-8"
    subject = f"Much Substantial! So time to act!"
    body_text = (f"""{p_change['currency']}\n
                 Changes in percent:
                 1h - {p_change['1h']}
                 24h - {p_change['24h']}
                 7d - {p_change['7d']}"""
                 )
    try:
        response = client.send_email(
            Destination={
                'ToAddresses': [to, ],
            },
            Message={
                'Body': {
                    'Text': {
                        'Charset': charset,
                        'Data': body_text,
                    },
                },
                'Subject': {
                    'Charset': charset,
                    'Data': subject,
                },
            },
            Source=sender,
        )
    except ClientError as e:
        raise ClientError
    else:
        print("Email sent! Message ID:"),
        print(response['ResponseMetadata']['RequestId'])


def should_i_know(p_change, modifier):
    if abs(p_change['1h']) > 10 * modifier or abs(p_change['24h']) > 25 * modifier or abs(p_change['7d']) > 50 * modifier:
        return True
    return False


def serve_alerts(id, modifier=1):
    percent_change = get_percent_changes(id)
    if should_i_know(percent_change, modifier):
        percent_change['currency'] = id
        send_email(percent_change)


def lambda_handler(event, context):
    serve_alerts('bitcoin')
    serve_alerts('ethereum', modifier=1.5)
