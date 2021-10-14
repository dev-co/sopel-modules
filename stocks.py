import sopel
import requests

def symbol_lookup(symb):
    url = "https://rest.yahoofinanceapi.com/v6/finance/quote"
    querystring = {"symbols": symb}
    headers = {'x-api-key': "FAKE_API_KEY"}
    response = requests.request("GET", url, headers=headers, params=querystring)
    return response.json()['quoteResponse']['result'][0]

@sopel.module.commands('dji','stocks','stock')
def stocks(bot,trigger):
    if trigger.group(2):
        name = symbol_lookup(trigger.group(2))
    else:
        return bot.say("Please use a valid symbol")

    change = '{0:.2f}'.format(float(name['regularMarketChange']))
    percent = '{0:.2f}'.format(float(name['regularMarketChangePercent']))

    return bot.say("{0}: {1} ({2}/{3})".format(name['longName'], name['regularMarketPrice'],"\x0304"+change+"\x0F" if float(change) < 0 else "\x0303"+change+"\x0F","\x0304"+percent+"%\x0F" if float(percent) < 0 else "\x0303+"+percent+"%\x0F",str(name['regularMarketOpen'])))
