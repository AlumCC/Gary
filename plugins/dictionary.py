import re
import random
from util import hook, http, text


@hook.command('ud')
@hook.command
def urban(inp):
    """.ud/.urban <phrase> - Looks up <phrase> on urbandictionary.com."""
    base_url = 'http://api.urbandictionary.com/v0'
    define_url = base_url + "/define"

    # fetch the definitions
    try:
        page = http.get_json(define_url, term=inp, referer="http://m.urbandictionary.com")
    except:
        return "Error reading the Urban Dictionary API; please try again later.."

    if page['result_type'] == 'no_results':
        return 'Not found.'

    definitions = page['list']
    definition = random.choice(definitions)

    def_text = " ".join(definition['definition'].split())  # remove excess spaces
    def_text = text.truncate_str(def_text, 200)

    name = definition['word']
    url = definition['permalink']
    out = u"\x02{}\x02: {}".format(name, def_text)

    return out


@hook.command
def define(inp):
    """.define/.dict <word> - fetches definition of <word>."""
    url = 'http://ninjawords.com/'

    try:
        h = http.get_html(url + http.quote_plus(inp))
    except:
        return "API error; please try again in a few minutes."

    definition = h.xpath('//dd[@class="article"] | '
                         '//div[@class="definition"] |'
                         '//div[@class="example"]')

    if not definition:
        return 'No results for ' + inp

    def format_output(show_examples):
        result = '%s: ' % h.xpath('//dt[@class="title-word"]/a/text()')[0]

        correction = h.xpath('//span[@class="correct-word"]/text()')
        if correction:
            result = 'definition for "%s": ' % correction[0]

        sections = []
        for section in definition:
            if section.attrib['class'] == 'article':
                sections += [[section.text_content() + ': ']]
            elif section.attrib['class'] == 'example':
                if show_examples:
                    sections[-1][-1] += ' ' + section.text_content()
            else:
                sections[-1] += [section.text_content()]

        for article in sections:
            result += article[0]
            if len(article) > 2:
                result += ' '.join('%d. %s' % (n + 1, section)
                                   for n, section in enumerate(article[1:]))
            else:
                result += article[1] + ' '

        synonyms = h.xpath('//dd[@class="synonyms"]')
        if synonyms:
            result += synonyms[0].text_content()

        result = re.sub(r'\s+', ' ', result)
        result = re.sub('\xb0', '', result)
        return result

    result = format_output(True)
    if len(result) > 450:
        result = format_output(False)

    if len(result) > 450:
        result = text.truncate_str(result, 450)

    return result


@hook.command
def etymology(inp):
    """.etymology <word> - Retrieves the etymology of chosen word."""
    url = 'http://www.etymonline.com/index.php'
    h = http.get_html(url, term=inp)
    etym = h.xpath('//dl')

    if not etym:
        return 'No etymology found for ' + inp

    etym = etym[0].text_content()
    etym = ' '.join(etym.split())

    return text.truncate_str(etym, 400)

