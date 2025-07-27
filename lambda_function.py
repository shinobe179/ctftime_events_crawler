import datetime as dt
import json
import math
import os
import sys
import logging
import boto3
import requests

# ロガーの設定
logger = logging.getLogger(__name__)
log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
logger.setLevel(getattr(logging, log_level))

# ログのフォーマット設定
formatter = logging.Formatter('%(asctime)s - %(funcName)s:%(lineno)d - %(levelname)s - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

# 定数
JST = dt.timezone(dt.timedelta(hours=+9), 'JST')
NOW = dt.datetime.now(JST)
NOW_EPOCTIME = math.floor(dt.datetime.timestamp(NOW))
LIMIT = 5
CTFTIME_ICON_URL = 'http://ctftime.org/static/images/ctftime-logo-avatar.png'
SLACK_ENDPOINT_URL = 'https://slack.com/api/chat.postMessage'

# Secrets Managerからの認証情報取得
def get_slack_credentials():
    secret_arn = os.environ['SLACK_CREDENTIALS_SECRET_ARN']
    session = boto3.session.Session()
    client = session.client('secretsmanager')
    
    try:
        response = client.get_secret_value(SecretId=secret_arn)
        secret = json.loads(response['SecretString'])
        return secret['slack_oauth_token'], secret['target_channel_id']
    except Exception as e:
        logger.error("Failed to get Slack credentials from Secrets Manager: %s", str(e))
        raise


def lambda_handler(event, context):
    logger.info("Lambda function started at %s JST", NOW.strftime("%Y/%m/%d %H:%M:%S"))
    try:
        # Slack認証情報の取得
        slack_oauth_token, target_channel_id = get_slack_credentials()
        logger.info("Successfully retrieved Slack credentials")

        logger.info("Fetching %d most recent CTFTime events", LIMIT)
        events = get_events(LIMIT)
        
        logger.info("Shaping %d events data", len(events))
        events = shape_events(events)
        
        headline = '{} 以降に行われるCTFのうち、直近の{}個です。'.format(
            NOW.strftime("%Y/%m/%d %H:%M:%S"), LIMIT)
        logger.info("Creating Slack message blocks with headline: %s", headline)
        blocks = create_slack_blocks(events, headline=headline)
        
        logger.info("Sending message to Slack")
        resp = send_slack_message(SLACK_ENDPOINT_URL, blocks, slack_oauth_token, target_channel_id, icon_url=CTFTIME_ICON_URL)
        logger.info("Successfully sent message to Slack")

        return resp
    except Exception as e:
        logger.error("Error in lambda_handler: %s", str(e), exc_info=True)
        raise

def get_events(limit):
    CTFTIME_API_URL = 'https://ctftime.org/api/v1/events/'
    params = {
        'limit': limit,
    }
    headers = {'User-Agent': 'weekly_ctftime_events_catcher'}
    
    logger.info("Making request to CTFTime API with params: %s", params)
    try:
        resp = requests.get(CTFTIME_API_URL, params=params, headers=headers)
        resp.raise_for_status()  # Raises HTTPError for 4XX/5XX status codes
    except requests.exceptions.RequestException as e:
        logger.error("Failed to fetch events from CTFTime API: %s", str(e))
        sys.exit(1)

    events = resp.json()
    logger.info("Successfully fetched %d events from CTFTime API", len(events))
    logger.debug("Fetched events: %s", json.dumps(events, indent=2))
    return events


def shape_events(events, onsite=None, is_votable_now=None, restrictions=None, event_format=None, public_votable=None):
    logger.info("Shaping events with filters: onsite=%s, is_votable_now=%s, restrictions=%s, format=%s, public_votable=%s",
                onsite, is_votable_now, restrictions, event_format, public_votable)
    
    conditions = {
        'onsite': onsite,
        'is_votable_now': is_votable_now,
        'restrictions': restrictions,
        'format': event_format,
        'public_votable': public_votable
    }

    original_count = len(events)
    for i in range(len(events)):
        event = events[i]
        for k,v in conditions.items():
            if v is None:
                continue
            if (type(v) != bool and not v in event[k]) or (type(v) == bool and not v is event[k]):
                events[i] = 'removed'
                break
    
    events = [e for e in events if e != 'removed']
    filtered_count = len(events)
    logger.info("Filtered events: %d -> %d events", original_count, filtered_count)
    return events


def create_slack_blocks(events, headline=None):
    logger.info("Creating Slack blocks for %d events", len(events))
    blocks = []
    divider_block = {'type': 'divider'}
    footer_block = {
        'type': 'section',
        'text': {
            'type': 'mrkdwn',
            'text': '(全 {} 件)'.format(str(len(events)))
        }
    }

    if headline != None:
        header_block = {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': headline
            }
        }
        blocks.append(header_block)

    for event in events:
        logger.debug("Processing event: %s", event['title'])
        event_format = (
            '*{title}*\n'
            'onsite: {onsite}\n'
            'format: {event_format}\n'
            'start: {start}\n'
            'finish: {finish}\n'
            'duration: {duration_days} days {duration_hours} hours\n'
            'URL: {url}\n'
            'CTFTIME URL: {ctftime_url}\n'
            'more detail: https://ctftime.org/api/v1/events/{event_id}/'
        ).format(
            title=event['title'],
            onsite=event['onsite'],
            event_format=event['format'],
            start=event['start'],
            finish=event['finish'],
            duration_days=event['duration']['days'],
            duration_hours=event['duration']['hours'],
            url=event['url'],
            ctftime_url=event['ctftime_url'],
            event_id=event['id'],
        )

        event_block = {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': event_format
            }
        }

        blocks.append(divider_block)
        blocks.append(event_block)

    blocks.append(divider_block)
    blocks.append(footer_block)

    logger.info("Created %d Slack blocks", len(blocks))
    return blocks


def send_slack_message(url, blocks, oauth_token, channel_id, username=None, icon_url=None):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {oauth_token}'
    }
    data = {
        'channel': channel_id,
        'username': 'CTFTIME',
        'icon_url': icon_url,
        'blocks': blocks
    }
    
    logger.info("Sending message to Slack channel %s with %d blocks", channel_id, len(blocks))
    try:
        resp = requests.post(url, headers=headers, data=json.dumps(data))
        resp.raise_for_status()  # Raises HTTPError for 4XX/5XX status codes
    except requests.exceptions.RequestException as e:
        logger.error("Failed to send message to Slack: %s", str(e))
        sys.exit(1)

    logger.info("Successfully sent message to Slack, status code: %d", resp.status_code)
    logger.debug("Slack response: %s", json.dumps(resp.json(), indent=2))
    return resp.status_code


if __name__ == '__main__':
    lambda_handler('', '')
