# coding=utf-8
# Copyright 2017-2019, Luis Uribe <acme@riseup.net>
# Based in some work 
from __future__ import unicode_literals, absolute_import, print_function, division

import json
import xmltodict
import re

from sopel import web
from sopel.module import commands, example, NOLIMIT

base_url = 'https://openexchangerates.org/api/latest.json?app_id=API_KEY&base=USD'

regex = re.compile(r'''
    (\d+(?:\.\d+)?)        # Decimal number
    \s*([a-zA-Z]{3})       # 3-letter currency code
    \s+(?:in|as|of|to)\s+  # preposition
    ([a-zA-Z]{3})          # 3-letter currency code
    ''', re.VERBOSE)


def get_rate(code):
    code = code.upper()
    data = json.loads(web.get(base_url))

    return float(data['rates'][code]), code

@commands('cur', 'currency', 'exchange')
@example('.cur 20 EUR in USD')
def exchange(bot, trigger):
    """Show the exchange rate between two currencies"""
    if not trigger.group(2):
        return bot.reply("No search term. An example: .cur 20 EUR in USD")
    match = regex.match(trigger.group(2))
    if not match:
        # It's apologetic, because it's using Canadian data.
        bot.reply("Sorry, I didn't understand the input.")
        return NOLIMIT

    amount, of, to = match.groups()
    try:
        amount = float(amount)
    except:
        bot.reply("Sorry, I didn't understand the input.")
    display(bot, amount, of, to)


def display(bot, amount, of, to):

    if not amount:
        bot.reply("Zero is zero, no matter what country you're in.")
    try:
        of_rate, of_name = get_rate(of)
        if not of_name:
            bot.reply("Unknown currency: %s" % of)
            return
        to_rate, to_name = get_rate(to)
        if not to_name:
            bot.reply("Unknown currency: %s" % to)
            return
    except Exception:
        bot.reply("Something went wrong while I was getting the exchange rate.")
        return NOLIMIT

    result = amount / of_rate * to_rate
    bot.say("{} {} ({}) = {} {} ({})".format(amount, of.upper(), of_name,
                                             result, to.upper(), to_name))


