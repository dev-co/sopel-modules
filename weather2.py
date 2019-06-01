# coding=utf-8
# Copyright 2008, Sean B. Palmer, inamidst.com
# Copyright 2012, Elsie Powell, embolalia.com
# Licensed under the Eiffel Forum License 2.
# A modification of sopel's weather.py after it was broken by yahoo's requirement for oauth authentication, and with much more features
# This module requires api keys for darksky.net, google location api, and bitly url shortener api.

from __future__ import unicode_literals, absolute_import, print_function, division
import requests
import json
from sopel.module import commands, example, NOLIMIT
from datetime import datetime
from pytz import timezone

forecastapi = 'AA`' # https://darksky.net/dev
glocation = 'XX' # https://developers.google.com/maps/documentation/geocoding/get-api-key
bitlyapi = 'CC' # http://dev.bitly.com/get_started.html  ##using the generic access token and not Oauth2, make sure to create an actual account and not use gmail login, or things get weird on their website
aqapi = '' #https://www.airnowapi.org/

def geo_lookup(location):
    response = requests.get("https://maps.googleapis.com/maps/api/geocode/json", params={
            "address": location,
            "key": glocation
        }).json()["results"]
    if response:
        if "geometry" in response[0]:
            return response[0]
        else:
            return
    else:
        return

def get_short_url(gurl):
    global bitlyapi
    short_url_service = 'https://api-ssl.bitly.com/v3/shorten?access_token={}&longUrl={}'.format(bitlyapi,requests.compat.quote_plus(gurl))
    r = requests.get(short_url_service)
    return r.json()['data']['url']

def get_temp(forecast):
    try:
        temp = round(forecast.json()['currently']['temperature'])
        app_temp = round(forecast.json()['currently']['apparentTemperature'])
    except (KeyError, ValueError):
        return 'unknown'
    high = round(forecast.json()['daily']['data'][0]['temperatureMax'])
    low = round(forecast.json()['daily']['data'][0]['temperatureMin'])
    if temp == app_temp:
        return (u'{0}\u00B0{1} (H:{2}|L:{3})'.format(temp, 'F' if forecast.json()['flags']['units']=='us' else 'C', high, low))
    else:
        return (u'{0}\u00B0{1}, (App:{2}, H:{3}|L:{4})'.format(temp, 'F' if forecast.json()['flags']['units']=='us' else 'C', app_temp, high, low))

def get_uv(forecast):
    currentuv = forecast.json()['currently']['uvIndex']
    maxuv = forecast.json()['daily']['data'][0]['uvIndex']
    if currentuv or currentuv == 0:
        if currentuv <3:
            color = "\x0303"
        elif (currentuv >=3) and (currentuv < 6):
            color = "\x0308"
        elif (currentuv >=6) and (currentuv < 8):
            color = "\x0307"
        elif (currentuv >=8) and (currentuv < 11):
            color = "\x0304"
        else:
            color = "\x0306"
        if maxuv <3:
            maxcolor = "\x0303"
        elif (maxuv >=3) and (maxuv < 6):
            maxcolor = "\x0308"
        elif (maxuv >=6) and (maxuv < 8):
            maxcolor = "\x0307"
        elif (maxuv >=8) and (maxuv < 11):
            maxcolor = "\x0304"
        else:
            maxcolor = "\x0306"
        return ", UV:{}{}\x0F|{}{}\x0F".format(color,currentuv,maxcolor,maxuv)
    else:
        return ''

def get_wind(forecast):
    try:
        if forecast.json()['flags']['units'] == 'us':
            wind_data = forecast.json()['currently']['windSpeed']
            kph = float(wind_data / 0.62137)
            m_s = float(round(wind_data, 1))
            speed = int(round(kph / 1.852, 0))
            unit = 'mph'
        elif forecast.json()['flags']['units'] == 'si':
            wind_data = forecast.json()['currently']['windSpeed']
            m_s = float(wind_data)
            kph = float(m_s * 3.6)
            speed = int(round(kph / 1.852, 0))
            unit = 'm/s'
        elif forecast.json()['flags']['units'] == 'ca':
            wind_data = forecast.json()['currently']['windSpeed']
            kph = float(wind_data)
            m_s = float(round(kph / 3.6, 1))
            speed = int(round(kph / 1.852, 0))
            unit = 'm/s'
        else:
            wind_data = forecast.json()['currently']['windSpeed']
            kph = float(wind_data / 0.62137)
            m_s = float(round(wind_data, 1))
            speed = int(round(kph / 1.852, 0))
            unit = 'mph'
        degrees = int(forecast.json()['currently']['windBearing'])
    except (KeyError, ValueError):
        return 'unknown'
    if speed < 1:
        description = 'Calm'
    elif speed < 4:
        description = 'Light air'
    elif speed < 7:
        description = 'Light breeze'
    elif speed < 11:
        description = 'Gentle breeze'
    elif speed < 16:
        description = 'Moderate breeze'
    elif speed < 22:
        description = 'Fresh breeze'
    elif speed < 28:
        description = 'Strong breeze'
    elif speed < 34:
        description = 'Near gale'
    elif speed < 41:
        description = 'Gale'
    elif speed < 48:
        description = 'Strong gale'
    elif speed < 56:
        description = 'Storm'
    elif speed < 64:
        description = 'Violent storm'
    else:
        description = 'Hurricane'
    if (degrees <= 22.5) or (degrees > 337.5):
        degrees = u'\u2193'
    elif (degrees > 22.5) and (degrees <= 67.5):
        degrees = u'\u2199'
    elif (degrees > 67.5) and (degrees <= 112.5):
        degrees = u'\u2190'
    elif (degrees > 112.5) and (degrees <= 157.5):
        degrees = u'\u2196'
    elif (degrees > 157.5) and (degrees <= 202.5):
        degrees = u'\u2191'
    elif (degrees > 202.5) and (degrees <= 247.5):
        degrees = u'\u2197'
    elif (degrees > 247.5) and (degrees <= 292.5):
        degrees = u'\u2192'
    elif (degrees > 292.5) and (degrees <= 337.5):
        degrees = u'\u2198'
    return description + ' ' + str(m_s) + unit + '(' + degrees + ')'

def get_alert(forecast):
    try:
        fullalerts = []
        uris = []
        if forecast.json()['alerts'][0]:
            for alerts in forecast.json()['alerts']:
                if alerts['uri'] not in uris:
                    title = alerts['title']
                    uris.append(alerts['uri'])
                    alert = get_short_url(alerts['uri'])
                    fullalerts.append("{} {}".format(title, alert))
            return ' | Alert: {}'.format(", ".join(fullalerts))
        else:
            return ''
    except:
        return ''

def get_forecast(bot,trigger,location=None):
    global forecastapi
    forecast,wloc,body,first_result,alert,result,error = '','','','','','',''
    if not location:
      wloc = bot.db.get_nick_value(trigger.nick, 'wloc')
      if not wloc:
        bot.msg(trigger.sender, "I don't know where you live.  Give me a location, like .weather London, or tell me where you live by saying .setlocation London, for example.")
        error = 'yes'
        return location, forecast, error
      geo_object = geo_lookup(wloc)
      geo_loc = geo_object["geometry"]["location"]
      longlat = "{0},{1}".format(geo_loc["lat"], geo_loc["lng"])
    else:
      if len(location) == 4:
        url = "http://iatageo.com/getICAOLatLng/" + location.upper()
        icao_loc = requests.get(url)
        if "error" in icao_loc.json():
          pass
        else:
          location = icao_loc.json()["latitude"] + " " + icao_loc.json()["longitude"]
      elif len(location) == 3:
        url = "http://iatageo.com/getLatLng/" + location.upper()
        iata_loc = requests.get(url)
        if "error" in iata_loc.json():
          pass
        else:
          location = iata_loc.json()["latitude"] + " " + iata_loc.json()["longitude"]
      geo_object = geo_lookup(location)
      if not geo_object:
        bot.reply("I don't know where that is.")
        error = 'yes'
        return location, forecast, error
      geo_loc = geo_object["geometry"]["location"]
      longlat = "{0},{1}".format(geo_loc["lat"], geo_loc["lng"])
    units = bot.db.get_nick_value(trigger.nick, 'units')
    if not units:
      units = 'auto'
    forecast = requests.get('https://api.darksky.net/forecast/{0}/{1}?units={2}'.format(forecastapi,longlat,units))
    location = geo_object["formatted_address"]
    if location[-3:] == 'USA':
      location =', '.join([b['short_name'] for b in geo_object['address_components'] if b['types'][0] == 'locality' or b['types'][0] == 'administrative_area_level_1'])
    return location, forecast, error

def get_sun(tz, forecast):
    if 'sunriseTime' not in forecast:
        return ""
    sunrise = datetime.fromtimestamp(forecast['sunriseTime'], tz=timezone(tz)).strftime('%H:%M')
    sunset = datetime.fromtimestamp(forecast['sunsetTime'], tz=timezone(tz)).strftime('%H:%M')
    return ", \u2600 \u2191 " + sunrise + " \u2193 " + sunset

def get_moon(forecast):
    if 'moonPhase' not in forecast:
        return ""
    moonphase = forecast['moonPhase']
    if moonphase == 0:
        moon = "\U0001F311 | New Moon ({0:.0f}%)".format(moonphase * 100)
    elif (moonphase > 0) and (moonphase <=0.24):
        moon = "\U0001F312 | Waxing Crescent ({0:.0f}%)".format(moonphase * 100)
    elif moonphase == 0.25:
        moon = "\U0001F313 | First Quarter ({0:.0f}%)".format(moonphase * 100)
    elif (moonphase >0.25) and (moonphase <=0.49):
        moon = "\U0001F314 | Waxing Gibbous ({0:.0f}%)".format(moonphase * 100)
    elif moonphase == 0.50:
        moon = "\U0001F315 | Full Moon ({0:.0f}%)".format(moonphase * 100)
    elif (moonphase >0.50) and (moonphase <=0.74):
        moon = "\U0001F316 | Waning Gibbous ({0:.0f}%)".format(moonphase * 100)
    elif moonphase == 0.75:
        moon = "\U0001F317 | Last Quarter ({0:.0f}%)".format(moonphase * 100)
    elif (moonphase >0.75) and (moonphase <=0.99):
        moon = "\U0001F318 | Waning Crescent ({0:.0f}%)".format(moonphase * 100)
    else:
        return ""
    return ", Moon: {}".format(moon)

@commands('weather7', 'wea7', 'w7')
@example('.weather7 London')
def weather7(bot,trigger):
    location = trigger.group(2)
    if not location:
        location, forecast, error = get_forecast(bot,trigger)
    else:
        location, forecast, error = get_forecast(bot,trigger,location)
    if error:
        return
    summary = forecast.json()['daily']['summary']
    sevendays = []
    weekdays = {1:'M',2:'Tu',3:'W',4:'Th',5:'F',6:'Sa',7:'Su'}
    for day in forecast.json()['daily']['data']:
        wkday = weekdays[datetime.fromtimestamp(int(day['time'])).isoweekday()]
        maxtemp = round(day['temperatureMax'])
        mintemp = round(day['temperatureMin'])
        sevendays.append("{0}:({1}|{2})".format(wkday,mintemp,maxtemp))
    #del sevendays[0]
    sevendays = ", ".join(sevendays)
    bot.say("{0}: [{1}] {2}".format(location, summary, str(sevendays)))

@commands('weather', 'wea', 'w')
@example('.weather London')
def weather(bot, trigger):
    """.weather location - Show the weather at the given location."""
    location = trigger.group(2)
    if not location:
        location, forecast, error = get_forecast(bot,trigger)
    else:
        location, forecast, error = get_forecast(bot,trigger,location)
    if error:
        return
    summary = forecast.json()['currently']['summary']
    temp = get_temp(forecast)
    alert = get_alert(forecast)
    bot.say(u'%s: %s, %s %s' % (location, summary, temp,  alert))

@commands('weatherfull','fullweather', 'wf')
def weatherfull(bot, trigger):
    """.weather location - Show the weather at the given location."""
    location = trigger.group(2)
    if not location:
        location, forecast, error = get_forecast(bot,trigger)
    else:
        location, forecast, error = get_forecast(bot,trigger,location)
    if error:
        return
    summary = forecast.json()['currently']['summary']
    temp = get_temp(forecast)
    humidity = forecast.json()['currently']['humidity']
    wind = get_wind(forecast)
    alert = get_alert(forecast)
    uv = get_uv(forecast)
    sun = get_sun(forecast.json()['timezone'], forecast.json()['daily']['data'][0])
    bot.say(u'%s: %s, %s, Humidity: %s%%, %s%s%s%s' % (location, summary, temp, round(humidity*100), wind, sun, uv, alert))

@commands('moon')
def moon(bot,trigger):
    location = trigger.group(2)
    if not location:
        location, forecast, error = get_forecast(bot,trigger)
    else:
        location, forecast, error = get_forecast(bot,trigger,location)
    if error:
        return
    moon = get_moon(forecast.json()['daily']['data'][0])[1:]
    bot.say(moon)

@commands('setlocation')
@example('.setlocation Columbus, OH')
def update_location(bot, trigger):
    """Set your default weather location."""
    if not trigger.group(2):
        bot.reply('Give me a location, like "Washington, DC" or "London".')
        return NOLIMIT
    geo_object = geo_lookup(trigger.group(2))
    if geo_object is None:
        return bot.reply("I don't know where that is.")
    bot.db.set_nick_value(trigger.nick, 'wloc', geo_object['formatted_address'])
    bot.reply('I now have you at {}'.format(geo_object["formatted_address"]))

@commands('setunits', 'setunit')
def update_unit(bot,trigger):
    if not trigger.group(2):
        return bot.reply('Choose a unit like "imperial" or "metric".')
    unit_dict = {'imperial':'us','metric':'si','auto':'auto'}
    if trigger.group(2).lower() in unit_dict:
        bot.db.set_nick_value(trigger.nick, 'units', unit_dict[trigger.group(2).lower()])
        bot.reply('Unit Set.')
    else:
        return bot.reply('Use the following values: imperial, metric, auto')

@commands('aq', 'aqi', 'air')
def airquality(bot, trigger):
  global aqapi
  location = trigger.group(2)
  if not location:
    wloc = bot.db.get_nick_value(trigger.nick, 'wloc')
    if not wloc:
      return bot.msg(trigger.sender, "I don't know where you live.  Give me a location, like .aq London, or tell me where you live by saying .setlocation London, for example.")
    geo_object = geo_lookup(wloc)
    geo_loc = geo_object["geometry"]["location"]
    latlong = "&latitude={}&longitude={}".format(geo_loc["lat"],geo_loc["lng"])
  else:
    geo_object = geo_lookup(location)
    if not geo_object:
      return bot.reply("I don't know what that is.")
    geo_loc = geo_object["geometry"]["location"]
    latlong = "&latitude={}&longitude={}".format(geo_loc["lat"],geo_loc["lng"])
  location = geo_object["formatted_address"]
  results = requests.get("http://www.airnowapi.org/aq/observation/latLong/current/?format=application/json{}&distance=100&API_KEY={}".format(latlong, aqapi)).json()
  if not results:
    return bot.say("No monitoring stations with 100 miles.")
  ozone = "{} [{}]".format(results[0]['AQI'], results[0]['Category']['Name'])
  pm = "{} [{}]".format(results[1]['AQI'], results[1]['Category']['Name'])
  return bot.say("{} Air Quality: O3 (ozone): {} | PM2.5 (particles): {}".format(location, ozone, pm))