from util import hook, http


@hook.api_key('domainr')
@hook.command
def domainr(inp, say='', api_key=None):
    """.domainr <domain> - Use domai.nr's API to search for a domain, and similar domains."""
    try:
        data = http.get_json('https://api.domainr.com/v1/search', q=inp, client_id=api_key)
    except (http.URLError, http.HTTPError) as e:
        return "Unable to get data for some reason. Try again later."
    if data['query'] == "":
        return "An error occurrred: {status} - {message}".format(**data['error'])
    domains = []
    for domain in data['results']:
        domains.append(("\x034" if domain['availability'] == "taken" else (
            "\x033" if domain['availability'] == "available" else "\x038")) + domain['domain'] + "\x0f" + domain['path'])
    say(u"Domains: {}".format(u", ".join(domains) or "None found"))
