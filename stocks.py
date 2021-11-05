import sopel
import requests

@sopel.module.commands('dji','stocks','stock')
def stocks(bot,trigger):
    if trigger.group(2):
        url = "https://yfapi.net/v6/finance/quote"
        querystring = {"symbols": trigger.group(2)}
        headers = {'x-api-key': "FAKE_API_KEY"}
        try:
            response = requests.request("GET", url, headers=headers, params=querystring)
            # sometimes we get a 200 but with no json, eg: when the URL has changed
            try:
                stock = response.json()['quoteResponse']['result'][0]
            except:
                return bot.say("An error ocurred, decoding json")   
        except requests.exceptions.RequestException as e:
            return bot.say("An error ocurred")
    else:
        return bot.say("Please use a valid symbol")

    change = '{0:.2f}'.format(float(stock['regularMarketChange']))
    percent = '{0:.2f}'.format(float(stock['regularMarketChangePercent']))

    return bot.say("{0}: {1} ({2}/{3})".format(stock['longName'], stock['regularMarketPrice'],"\x0304"+change+"\x0F" if float(change) < 0 else "\x0303"+change+"\x0F","\x0304"+percent+"%\x0F" if float(percent) < 0 else "\x0303+"+percent+"%\x0F",str(stock['regularMarketOpen'])))
