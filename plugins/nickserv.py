"""
These functions are entirely for tracking NickServ status of users. NickServ
status of users is used for admin functions which require the user to be
identified for security reasons. This may be useful if the adminonly concept
is expanded to a full permissions manager for security on priveleged groups.
"""

from time import sleep
from util import hook, text


@hook.singlethread  # Don't flood nickserv
@hook.command(autohelp=False)
def status(inp, nick=None, say=None, conn=None):
    """.status [all|green|red] - Gets your perceived NickServ status or a specified group."""
    if inp == 'all':
        users = conn.users
    elif inp == 'green':
        users = {k:v for k,v in conn.users.items() if v}
    elif inp == 'red':
        users = {k:v for k,v in conn.users.items() if not v}
    elif inp == 'bot':
        return "I am %s." % ("\x033identified\x0f" if conn.users.get(conn.nick.lower(), None)
            else "\x034unidentified\x0f")
    else:
        return "You look %s to me." % ("\x033identified\x0f" if conn.users.get(nick.lower(), None)
            else "\x034unidentified\x0f")

    outs = text.chunk_str(', '.join(sorted(["\x033%s\x0f" % k if v else "\x034%s\x0f" % k
        for k, v in users.items()], key=lambda x: x)))

    for out in outs: say(out)


@hook.command(autohelp=False)
def statusreset(inp, conn=None):
    conn.users = {k:v for k,v in conn.users.items() if v}
    return "Done."


@hook.command()
def reauth(inp, conn=None):
    # wipe user list (useful for server restarts)
    conn.users = {}

    # identify to services
    nickserv_password = conn.conf.get('nickserv_password', '')
    nickserv_name = conn.conf.get('nickserv_name', 'nickserv')
    nickserv_command = conn.conf.get('nickserv_command', 'IDENTIFY %s')
    nickserv_info = conn.conf.get('nickserv_info_command', 'STATUS %s')
    if nickserv_password:
        conn.msg(nickserv_name, nickserv_command % nickserv_password)
        sleep(1)
        conn.msg(nickserv_name, nickserv_info % conn.nick)
        sleep(1)


@hook.singlethread
@hook.event('*')
def nickserv_tracking(paraml, nick=None, input=None, conn=None):
    sleep(1)
    if input.command in ('QUIT', 'NICK', 'PART', 'PRIVMSG', 'KICK') and \
            conn.users.get(conn.nick.lower(), False):
        nick = nick.lower()
        nickserv_name = conn.conf.get('nickserv_name', 'nickserv')
        nickserv_info = conn.conf.get('nickserv_info_command', 'STATUS %s')
        if input.command == 'JOIN':
            if not conn.users.get(nick, False):
                conn.msg(nickserv_name, nickserv_info % nick)
        elif input.command == 'PRIVMSG':
            if nick not in conn.users.keys():
                 conn.msg(nickserv_name, nickserv_info % nick)
        elif input.command in ('QUIT', 'PART', 'NICK', 'KICK') and \
                nick.lower() != conn.nick.lower():
            if input.command == 'KICK':
                nick = paraml[1].lower()
            conn.users.pop(nick, None)


@hook.event('NOTICE')
def noticed(paraml, chan='', conn=None):
    if paraml[0] == conn.nick and \
            chan.lower() == conn.conf.get('nickserv_name', 'nickserv'):
            if conn.conf.get('service_style') == 'anope':
                if paraml[1].split()[0] == 'STATUS':
                    user = str(paraml[1].split()[1]).lower()
                    if paraml[1].split()[2] == '3':
                        conn.users[user] = True
                        print(">>> {} identified.".format(user))
                    else:
                        conn.users[user] = False
                        print(">>> {} not identified.".format(user))
            elif conn.conf.get('service_style') == 'hybserv':
                if "Nickname:" in paraml[1]:
                    if "ONLINE" in paraml[1]:
                        user = str(paraml[1].split()[1]).lower()
                        conn.users[user] = True
                        print(">>> {} identified.".format(user))
                    else:
                        conn.users[user] = False
                        print(">>> {} not identified.".format(user))
                elif "not registered" in paraml[1] or "is private" in paraml[1]:
                    user = str(paraml[1].split()[2]).lower()[2:-2]
                    conn.users[user] = False
                    print(">>> {} not identified.".format(user))

