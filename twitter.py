# coding=utf-8
from __future__ import unicode_literals, absolute_import, division, print_function

from datetime import datetime
import json
import re

import requests

from sopel import module, tools
from sopel.tools import time
from sopel.config.types import StaticSection, ValidatedAttribute, NO_DEFAULT
from sopel.logger import get_logger

logger = get_logger(__name__)


class TwitterSection(StaticSection):
    bearer_token = "CHANGEME"

def bearer_oauth(r):
    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2TweetLookupPython"
    return r

@module.url(r'https?://twitter\.com/(?P<user>[^/]+)(?:$|/status/(?P<status>\d+)).*')
@module.url(r'https?://twitter\.com/i/web/status/(?P<status>\d+).*')
def get_url(bot, trigger, match):
    things = match.groupdict()
    user = things.get('user', None)
    status = things.get('status', None)

    if status:
        output_status(bot, trigger, status)
    elif user:
        output_user(bot, trigger, user)
    else:
        # don't know how to handle this link; silently fail
        # explicit is better than implicit
        return


def output_status(bot, trigger, id_):
    ids = "ids="+str(id_)
    tweet_fields = "tweet.fields=lang,author_id"
    url = "https://api.twitter.com/2/tweets?{}&{}".format(ids, tweet_fields)
    response = requests.request("GET", url, auth=bearer_oauth)

    if response.status_code != 200:
        logger.error('%s error reaching the twitter API for status ID %s',
                     response.status_code, id_)
        fuck_elon = json.loads(response.content.decode('utf-8'))
        bot.say("[Twitter] Elon did it again: " + fuck_elon['title'] + ": " + fuck_elon['detail'])
        return

    # tweet = json.loads(content.decode('utf-8'))
    tweet = json.loads(response.content.decode('utf-8'))
    bot.say("[Twitter] " + tweet['data'][0]['text'])
