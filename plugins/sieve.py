import re
from time import time
from util import hook

timeouts = {}
timeouts_active = False


def is_admin(bot, input):
    nick = input.nick.lower()
    admins = bot.config.get('admins', [])
    if nick in admins and input.conn.users.get(nick, False):
        return True
    else:
        return False


def is_mod(bot, input):
    nick = input.nick.lower()
    moded = bot.config.get('moded', [])
    if nick in moded and input.conn.users.get(nick, False):
        return True
    else:
        return False


@hook.command(autohelp=False, modonly=True)
def cmdtimeout(inp):
    """.cmdtimeout - Toggles if command timeouts are active."""
    global timeouts_active
    timeouts_active = not timeouts_active
    return "Command timeouts are now \x02{}abled\x0f.".format("en"
        if timeouts_active else "dis")



@hook.sieve
def sieve_suite(bot, input, func, kind, args):
    allowed = bot.config.get('allowed', [])
    disabled = bot.config.get('disabled', [])
    ignored = bot.config.get('ignored', [])
    muted = bot.config.get('muted', [])
    restricted = bot.config.get('restricted', [])
    acl = bot.config.get('acls', {})
    channels_only = bot.config.get('channels_only', False)

    # log everything
    #if func.__name__.lower() == "log":
    #    return input

    # channels only
    if kind in ("command", "regex") and input.chan[0] != '#' and channels_only:
        if not is_mod(bot, input) and not is_admin(bot, input):
            return None

    # disable function
    if kind in ("event", "regex"):
        if func.__name__.lower() in disabled:
            return None

    if kind in ("command"):
        if any(x in disabled for x in [func.__name__.lower(), input.trigger]):
            if not is_admin(bot, input):
                return None

    # disable plugin
    fn = re.match(r'^plugins/(.+\.py$)', func._filename)
    if fn and fn.group(1).lower() in disabled:
        return None

    # acls
    if acl:
        if 'deny-except' in acl:
            allowed_channels = map(unicode.lower, acl['deny-except'])
            if input.chan.lower() not in allowed_channels:
                return None
        if 'allow-except' in acl:
            denied_channels = map(unicode.lower, acl['allow-except'])
            if input.chan.lower() in denied_channels:
                return None

    # admins
    if args.get('adminonly'):
        if not is_admin(bot, input):
            return None

    # mods
    if args.get('modonly'):
        if not is_mod(bot, input) and not is_admin(bot, input):
            return None

    # restricted
    if kind in ("command", "regex") and input.chan in restricted:
        if input.nick.lower() not in allowed:
            if not is_mod(bot, input) and not is_admin(bot, input):
                return None

    # ignores
    if any(x in ignored for x in map(lambda y:y.lower(),
            [input.host, input.user, input.nick, input.chan])):
        if not is_mod(bot, input) and not is_admin(bot, input):
            return None

    # mutes
    if kind in ("command", "regex") and input.chan in muted:
        if kind == "command":
            if not is_mod(bot, input) and not is_admin(bot, input):
                return None
        else:
            return None

    # rate limiting
    if kind == "command" and input.chan[0] == '#' and timeouts_active:
        if not is_mod(bot, input) and not is_admin(bot, input):
            global timeouts
            limit = 3
            timeout = 5

            if timeouts.get(input.server, None) is None:
                timeouts[input.server] = {}

            # user timeouts
            if timeouts[input.server].get(input.user, None) is None:
                timeouts[input.server][input.user] = {}
                timeouts[input.server][input.user]['msgs'] = [time()]
                timeouts[input.server][input.user]['timeout'] = 0
            else:
                timeouts[input.server][input.user]['msgs'].append(time())
                timeouts[input.server][input.user]['msgs'] = [msg for msg in
                    timeouts[input.server][input.user]['msgs'] if time() - msg < 60]

            if time() - timeouts[input.server][input.user]['timeout'] < timeout * 60:
                return None
            else:
                timeouts[input.server][input.user]['timeout'] = 0

            if len(timeouts[input.server][input.user]['msgs']) > limit:
                timeouts[input.server][input.user]['timeout'] = time()
                input.reply("You have been timed out for {} minutes " \
                    "for using commands too quickly. Feel free to PM me " \
                    "to explore my functions freely.".format(timeout))
                return None

            # command timeouts
            chan_cmd = "{}_{}".format(input.chan, func.__name__.lower())
            if timeouts[input.server].get(chan_cmd, None) is None:
                timeouts[input.server][chan_cmd] = {}
                timeouts[input.server][chan_cmd]['msgs'] = [time()]
                timeouts[input.server][chan_cmd]['timeout'] = 0
            else:
                timeouts[input.server][chan_cmd]['msgs'].append(time())
                timeouts[input.server][chan_cmd]['msgs'] = [msg for msg in
                    timeouts[input.server][chan_cmd]['msgs'] if time() - msg < 60 * 2]

            if time() - timeouts[input.server][chan_cmd]['timeout'] < timeout * 60:
                return None
            else:
                timeouts[input.server][chan_cmd]['timeout'] = 0

            if len(timeouts[input.server][chan_cmd]['msgs']) > limit * 2:
                timeouts[input.server][chan_cmd]['timeout'] = time()
                input.say(".{} has been temporarily disabled to control spam. " \
                    "I will enable it again in {} minutes.".format(func.__name__.lower(), timeout))
                return None

    return input

