# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

__author__ = 'ufian'

import os
import time
import logging
import datetime as dt
import json

from slackclient import SlackClient

from websocket import WebSocketConnectionClosedException
from socket import error as SocketError

try:
    from slackclient._client import \
        SlackNotConnected  # not actually used, see https://github.com/slackapi/python-slackclient/issues/36
    from slackclient._server import SlackConnectionError
except ImportError:
    SlackNotConnected = SocketError
    SlackConnectionError = SocketError

from bot import message_event, get_connect
import slackbot_settings as config

logger = logging.getLogger(__name__)


def handle(sc, events):
    for event in events:
        logging.info('Event: {0}'.format(json.dumps(event, indent=2)))
        event_type = event.get('type', 'None')
        if event_type == 'message':
            reply = handle_message(sc, event)

            if reply is not None:
                logging.warning("Send message {}:\n{}".format(event.get('channel'), reply))
                sc.api_call(
                    "chat.postMessage",
                    channel=event.get('channel'),
                    text=reply
                )


def handle_message(sc, event):
    reply = message_event(sc, event)

    return reply


def main():
    log_level = os.getenv("LOG_LEVEL", "INFO") or "INFO"
    logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=log_level)

    slack_token = getattr(config, "API_TOKEN", os.getenv("SLACK_TOKEN", ""))
    logging.info("token: {}".format(slack_token))

    while True:
        try:
            sc = SlackClient(slack_token)

            get_connect()

            if sc.rtm_connect():
                sc.api_call(
                    "chat.postMessage",
                    channel=u'D9VF86DHT',
                    text='Restarted {0}'.format(dt.datetime.now())
                )

                counter = 0

                while True:
                    try:
                        handle(sc, sc.rtm_read())
                        counter = 0
                    except Exception as e:
                        logging.exception('Problem: ' + str(e))
                        if counter < 5:
                            counter += 1
                        else:
                            raise
                    time.sleep(1)
            else:
                logging.error("Connection Failed, invalid token?")
        except (SocketError, WebSocketConnectionClosedException, SlackConnectionError, SlackNotConnected) as e:
            if not SlackClient(slack_token).rtm_connect():
                logging.exception('Global reconnect problem: ' + str(e))
        except Exception as e:
            logging.exception('Global problem. Recreate app, error:' + str(e))
            time.sleep(1)


if __name__ == "__main__":
    main()
