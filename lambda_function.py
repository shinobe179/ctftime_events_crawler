import datetime as dt
import json
import math
import os
import sys

import requests

JST = dt.timezone(dt.timedelta(hours=+9), 'JST')
NOW = dt.datetime.now(JST)
NOW_EPOCTIME = math.floor(dt.datetime.timestamp(NOW))
#DURATION_WEEKS = 2
LIMIT = 5
SLACK_ENDPOINT_URL = os.environ['SLACK_ENDPOINT_URL']
CTFTIME_ICON_URL = 'http://ctftime.org/static/images/ctftime-logo-avatar.png'


def lambda_handler(event, context):
    #period = NOW + dt.timedelta(weeks=DURATION_WEEKS)
    #period_epoctime = math.floor(dt.datetime.timestamp(period))
    #events = get_events(NOW_EPOCTIME, period_epoctime)
    events = get_events(LIMIT)
    events = shape_events(events)
    blocks = create_slack_blocks(events, headline='{} 以降に行われるCTFのうち、直近の{}個です。'.format(NOW.strftime("%Y/%m/%d %H:%M:%S"), LIMIT))
    resp = send_slack_message(SLACK_ENDPOINT_URL, blocks, icon_url=CTFTIME_ICON_URL)

    return resp

#def get_events(start, finish, limit=LIMIT):
def get_events(limit):
    CTFTIME_API_URL = 'https://ctftime.org/api/v1/events/'
    params = {
        'limit': limit,
        #'start': start,
        #'finish': finish
    }
    headers = {'User-Agent': 'weekly_ctftime_events_catcher'}
    resp = requests.get(CTFTIME_API_URL, params=params, headers=headers)

    if resp.status_code != 200:
        print('[x] Getting events is failed. code:{}, text:{}'.format(resp.status_code, resp_text))
        sys.exit(1)

    events = resp.json()

    return events


def shape_events(events, onsite=None, is_votable_now=None, restrictions=None, event_format=None, public_votable=None):
    conditions = {
        'onsite': onsite,
        'is_votable_now': is_votable_now,
        'restrictions': restrictions,
        'format': event_format,
        'public_votable': public_votable
    }

    for i in range(len(events)):
        event = events[i]
        for k,v in conditions.items():
            if v is None:
                continue
            if (type(v) != bool and not v in event[k]) or (type(v) == bool and not v is event[k]):
                events[i] = 'removed'
                break
    
    events = [e for e in events if not e is 'removed']            
    return events


def create_slack_blocks(events, headline=None):
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

    return blocks


def send_slack_message(url, blocks, username=None, icon_url=None):
    headers = {'Content-Type': 'application/json'}
    data = {
        'username': 'CTFTIME',
        'icon_url': icon_url,
        'blocks': blocks
    }
    resp = requests.post(url, headers=headers, data=json.dumps(data))
    if resp.status_code != 200:
        print('[x] Sending a message is failed. code:{}, text:{}'.format(resp.status_code, resp.text))
        sys.exit(1)

    return resp.status_code
