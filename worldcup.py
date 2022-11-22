import sopel
import requests
from datetime import datetime, timedelta

@sopel.module.commands('wc','mundial')
def worldcup(bot,trigger):
    if trigger.group(2) == "today":
        get_todays_matches(bot)
    else:
        get_current_match(bot)

def get_todays_matches(bot):
    url = "https://copa22.medeiro.tech/matches/today"
    try:
        response = requests.request("GET", url)
        try:
            matches = response.json()
        except:
            return bot.say("An error ocurred, decoding json.")
    except requests.exceptions.RequestException as e:
        return bot.say("An error ocurred")

    bot.reply("Today's matches: ")
    for match in matches:
        if match['status'] == "completed":
            bot.reply("{0} ({1}) Vs {2} ({3}) :: Finished".format(match['homeTeam']['name'], match['homeTeam']['goals'], match['awayTeam']['name'], match['awayTeam']['goals']))
        elif match['status'] == "in_progress":
            bot.reply("{0} ({1}) Vs {2} ({3}) :: In progress".format(match['homeTeam']['name'], match['homeTeam']['goals'], match['awayTeam']['name'], match['awayTeam']['goals']))

        elif match['status'] == "scheduled":
            match['date'] = match['date'][:-5]
            match_date = datetime.strptime(match['date'], "%Y-%m-%dT%H:%M:%S")
            final_time = match_date - timedelta(hours=5)
            bot.reply("{0} Vs {1}  at: {2}".format(match['homeTeam']['name'], match['awayTeam']['name'], final_time))

def get_current_match(bot):
    url = "https://copa22.medeiro.tech/matches/current"
    try:
        response = requests.request("GET", url)
        try:
            match = response.json()
        except:
            return bot.say("An error ocurred, decoding json.")
    except requests.exceptions.RequestException as e:
        return bot.say("An error ocurred")

    if response.status_code == '400' :
        return bot.say("There is not match in progress right now. Try .wc today")

    return bot.reply("{0} ({1}) Vs {2} ({3}) :: In progress".format(match['homeTeam']['name'], match['homeTeam']['goals'], match['awayTeam']['name'], match['awayTeam']['goals']))
