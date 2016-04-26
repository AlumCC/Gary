from util import hook, http

wunder_url = "http://api.wunderground.com/api/{}/{}/q/{}.json"
cards = {
    0: "N",
    22.5: "NNE",
    45: "NE",
    67.5: "ENE",
    90: "E",
    112.5: "ESE",
    135: "SE",
    157.5: "SSE",
    180: "S",
    202.5: "SSW",
    225: "SW",
    257.5: "WSW",
    270: "W",
    292.5: "WNW",
    315: "NW",
    337.5: "NNW",
    360: "N"
}

alerts = {
    'HUR': 'Hurricane Local Statement',
    'TOR': 'Tornado Warning',
    'TOW': 'Tornado Watch',
    'WRN': 'Severe Thunderstorm Warning',
    'SEW': 'Severe Thunderstorm Watch',
    'WIN': 'Winter Weather Advisory',
    'FLO': 'Flood Warning',
    'WAT': 'Flood Watch / Statement',
    'WND': 'High Wind Advisory',
    'SVR': 'Severe Weather Statement',
    'HEA': 'Heat Advisory',
    'FOG': 'Dense Fog Advisory',
    'FIR': 'Fire Weather Advisory',
    'VOL': 'Volcanic Activity Statement',
    'HWW': 'Hurricane Wind Warning'
}


@hook.api_key('wunder')
@hook.command('w')
@hook.command
def weather(inp, say=None, api_key=None):
    """.w[eather] <zip code|location> - Gets the current weather conditions."""
    if api_key is None:
        return "Error: API key not set."

    try:
        weather = http.get_json(wunder_url.format(api_key, 'forecast/geolookup/conditions', http.quote(inp)))
        alert = http.get_json(wunder_url.format(api_key, 'alerts', http.quote(inp)))
        if weather.get('current_observation', None) is None and len(weather['response'].get('results', [])) > 0:
            weather = http.get_json(wunder_url.format(api_key,
                'forecast/geolookup/conditions', 'zmw:' + weather['response']['results'][0]['zmw']))
            alert = http.get_json(wunder_url.format(api_key, 'alerts', 'zmw:' + alert['response']['results'][0]['zmw']))
    except:
        return "Weather Underground API error, please try again in a few minutes."

    try:
        direction = cards.get(float(weather['current_observation']['wind_degrees']),
            cards[min(cards.keys(), key=lambda k: abs(k - float(weather['current_observation']['wind_degrees'])))])
        alert = [a for a in alert['alerts'] if a['type'] in alerts.keys()]  # Get only alerts we care about
        alert = "\x02{description}\x0F until {expires}.".format(**alert[0]) if alert else ""

        say("\x02{location[city]}, {location[state]}\x0F: {current_observation[temp_f]}*F " \
            "and {current_observation[weather]}, feels like {current_observation[feelslike_f]}*F, " \
            "wind at {current_observation[wind_mph]} MPH {}, humidity at {current_observation[relative_humidity]}. " \
            "{}".format(direction, alert, **weather))
    except:
        try:
            return "Ambiguous location, please try one of the following: {}".format(
                ", ".join(["{} {}".format(i['city'], i['state']) for i in weather['response']['results']]))
        except:
            return "Error: unable to find weather data for location."


@hook.api_key('wunder')
@hook.command('f')
@hook.command
def forecast(inp, say=None, api_key=None):
    """.f[orecast] <zip code|location> - Gets the weather forecast."""
    if api_key is None:
        return "Error: API key not set."

    try:
        weather = http.get_json(wunder_url.format(api_key, 'forecast/geolookup/conditions', http.quote_plus(inp)))
        if weather.get('current_observation', None) is None and len(weather['response'].get('results', [])) > 0:
            weather = http.get_json(wunder_url.format(api_key,
                'forecast/geolookup/conditions', 'zmw:' + weather['response']['results'][0]['zmw']))
    except:
        return "Weather Underground API error, please try again in a few minutes."
    try:
        say("\x02{location[city]}, {location[state]}\x0F: ".format(**weather) +
            '; '.join(["\x02{date[weekday]}\x0F: L {low[fahrenheit]}*F, H {high[fahrenheit]}*F, {conditions}".format(**day)
            for day in weather['forecast']['simpleforecast']['forecastday']]))
    except:
        try:
            return "Ambiguous location, please try one of the following: {}".format(
                ", ".join(["{} {}".format(i['city'], i['state']) for i in weather['response']['results']]))
        except:
            return "Error: unable to find weather data for location."


@hook.api_key('wunder')
@hook.command('h')
@hook.command
def hourly(inp, say=None, api_key=None):
    """.h[ourly] <zip code|location> - Gets the 12 hour weather forecast."""
    if api_key is None:
        return "Error: API key not set."

    try:
        weather = http.get_json(wunder_url.format(api_key, 'hourly/geolookup/conditions', http.quote_plus(inp)))
        if weather.get('hourly_forecast', None) is None and len(weather['response'].get('results', [])) > 0:
            weather = http.get_json(wunder_url.format(api_key,
                'hourly/geolookup/conditions', 'zmw:' + weather['response']['results'][0]['zmw']))
    except:
        return "Weather Underground API error, please try again in a few minutes."
    try:
        say("\x02{location[city]}, {location[state]}\x0F: ".format(**weather) +
            '; '.join(["\x02{FCTTIME[civil]}\x0F: {temp[english]}*F, {condition}".format(**day)
            for day in weather['hourly_forecast'][:12]]))
    except:
        try:
            return "Ambiguous location, please try one of the following: {}".format(
                ", ".join(["{} {}".format(i['city'], i['state']) for i in weather['response']['results']]))
        except:
            return "Error: unable to find weather data for location."
