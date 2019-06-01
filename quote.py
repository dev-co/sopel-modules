"""
quote.py - A simple quotes module for willie
Copyright (C) 2014  Andy Chung - iamchung.com
Copyright (C) 2014  Luis Uribe - acme@eviled.org

iamchung.com

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

from __future__ import unicode_literals
import sopel
from sopel import module
from sopel.module import commands, example

import sqlite3
import random
import codecs # TODO in python3, codecs.open isn't needed since the default open does encoding.
import re

@commands('quote')
def quote(bot, trigger):
    filename = bot.config.quote.filename
    raw_args = trigger.group(2)
    output = ''
    if raw_args is None or raw_args == '':
        # display random quote
        output = get_random_quote(bot, trigger.sender)
    else:
        # get subcommand
        command_parts = raw_args.split(' ', 1)
        if len(command_parts) < 2:
            output = trigger.nick + ': nah nah'
        else:
            subcommand = command_parts[0]
            data = command_parts[1]

            # perform subcommand
            if subcommand == 'add':
                output = add_quote(bot, trigger.sender, data)
            elif subcommand == 'search':
                for quote in search_quote(bot, trigger.sender, data):
                    bot.say(quote)
            else:
                output = 'invalid subcommand'
    bot.say(output)

def get_random_quote(bot, channel):
    db  = None
    cur = None
    db  = connect_db(bot)
    cur = db.cursor()

    try:
        cur.execute('SELECT quote FROM quotes WHERE channel = ? ORDER BY RANDOM() LIMIT 1;', (channel,))
        res = cur.fetchone()
        if res is None:
            msg = 'We have no data'
        else:
            msg = res[0]
    except Exception as e:
        msg = "Error looking for quotes"
    finally:
        db.close()
    return msg

def add_quote(bot, channel, search):
    db  = None
    cur = None
    db  = connect_db(bot)
    cur = db.cursor()

    try:
        bot.memory['chan_messages'][channel]
    except:
        msg = "There's no history for this channel."
        return msg

    for line in reversed(bot.memory['chan_messages'][channel]):
        if re.search(search, line) is not None:
            try:
                cur.execute('INSERT INTO quotes (quote, channel) VALUES (?, ?);', (line, channel))
                db.commit()
                msg = "Quote added: " + line
            except Exception as e:
                raise e
                msg = "Error adding quote"
            finally:
                db.close()
            return msg

    msg = "What are you doing, moron?"
    return msg


def search_quote(bot, channel, search):
    db = connect_db(bot)
    cur = db.cursor()

    msg = ['Quote not found.']
    try:
        cur.execute('SELECT quote FROM quotes WHERE quote LIKE ? and channel = ? ORDER BY RANDOM() LIMIT 5', ('%' + search + '%', channel))
        msg = [quote[0] for quote in cur.fetchall()]
    except Exception as e:
        msg = ['Error looking for quotes']
    return msg


def setup(bot):
    bot.memory['chan_messages'] = {}
    bot.memory['chan_quotes'] = {}

def connect_db(willie):
    conn = sqlite3.connect(DB_FILE)
    return conn

#save everything it's said on the channels
@module.rule('^[^\.].*')
def log_chan_message(bot, trigger):
    try:
        bot.memory['chan_messages'][trigger.sender].append(trigger.nick + ': ' +trigger)
    except:
        bot.memory['chan_messages'][trigger.sender] = []
        bot.memory['chan_messages'][trigger.sender].append(trigger.nick + ': ' +trigger)
