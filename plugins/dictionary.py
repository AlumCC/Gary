import re
import random
from util import hook, http, text


API_URL = 'http://api.wordnik.com/v4/'


@hook.api_key('wordnik')
@hook.command
def define(inp, say=None, api_key=None):
    """define <word> - Returns a definition for <word> from wordnik.com."""
    # based on edwardslabs/cloudbot's wordnik.py
    if not api_key:
        return "This command requires an API key from wordnik.com."
    word = inp.split(' ')[0]
    url = API_URL + u"word.json/{}/definitions".format(word)

    try:
        params = {
            'api_key': api_key,
            'limit': 10,
            'useCanonical': 'false'
        }
        json = http.get_json(url, query_params=params)
    except:
        return "Wordnik API error; please try again in a few minutes."

    json = [j for j in json if j.get('text')]
    if json:
        data = json[0]
        text = re.sub('<[^<]+>', "", data['text'])
        say(u"\x02{}\x02: {}".format(data['word'], text))
    else:
        return "I could not find a definition for \x02{}\x02.".format(word)


@hook.api_key('wordnik')
@hook.command("wotd", autohelp=False)
def wordoftheday(inp, say=None, api_key=None):
    """wotd - Returns the word of the day from wordnik.com."""
    # based on edwardslabs/cloudbot's wordnik.py
    if not api_key:
        return "This command requires an API key from wordnik.com."
    url = API_URL + "words.json/wordOfTheDay"

    params = {
        'api_key': api_key
    }
    json = http.get_json(url, query_params=params)

    if json:
        word = json['word']
        note = json['note']
        pos = json['definitions'][0]['partOfSpeech']
        definition = re.sub('<[^<]+>', "", json['definitions'][0]['text'])
        say(u"The word the day is \x02{}\x0F: ({}) {} {}".format(word, pos, definition, note))
    else:
        return "Sorry I couldn't find the word of the day."


@hook.command('ud')
def urban(inp, say=None):
    """ud <phrase> - Looks up <phrase> on Urban Dictionary."""
    base_url = 'http://api.urbandictionary.com/v0'
    define_url = base_url + "/define"

    try:
        page = http.get_json(define_url, term=inp, referer="http://m.urbandictionary.com")
    except:
        return "Error reading the Urban Dictionary API; please try again in a few minutes."

    if page['result_type'] == 'no_results':
        return 'Not found.'

    definition = random.choice(page['list'])
    def_text = " ".join(definition['definition'].split())  # remove excess spaces
    name = definition['word']

    say(text.truncate_str(u"\x02{}\x02: {}".format(name, def_text), 400))


@hook.command
def etymology(inp, say=None):
    """etymology <word> - Retrieves the etymology of chosen word."""
    url = 'http://www.etymonline.com/search'
    try:
        params = {'q': inp}
        h = http.get_html(url, query_params=params)
    except:
        return "Error fetching etymology."
    etym = h.xpath('//section')

    if not etym:
        return 'No etymology found for ' + inp

    etym = etym[0].text_content()
    etym = ' '.join(etym.split())

    say(text.truncate_str(etym, 450))

