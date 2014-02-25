import re
import socket
import subprocess
import time

from util import hook, http

socket.setdefaulttimeout(10)  # global setting


def get_version():
    p = subprocess.Popen(['git', 'log', '--oneline'], stdout=subprocess.PIPE)
    stdout, _ = p.communicate()
    p.wait()

    revnumber = len(stdout.splitlines())

    shorthash = stdout.split(None, 1)[0]

    http.ua_gary = 'Gary/r%d %s (http://github.com/MikeRixWolfe/gary)' \
        % (revnumber, shorthash)

    return shorthash, revnumber


@hook.event('JOIN')
def onjoin(paraml, nick=None, conn=None):
    if nick == conn.nick and paraml[0] not in conn.channels:
            conn.channels.append(paraml[0])


@hook.event('PART')
def onpart(paraml, nick=None, conn=None):
    if nick == conn.nick and paraml[0] in conn.channels:
            conn.channels.remove(paraml[0])


@hook.event('KICK')
def onkick(paraml, conn=None, bot=None):
    if paraml[1] == conn.nick and paraml[0].lower() in conn.channels:
        if bot.config.get('rejoin', ''):
            conn.join(paraml[0])
        else:
            conn.channels.remove(paraml[0])


@hook.event('INVITE', adminonly=True)
def oninvite(paraml, conn=None):
    conn.join(paraml[-1])


@hook.event('004')
def onconnect(paraml, conn=None):
    # identify to services
    nickserv_password = conn.conf.get('nickserv_password', '')
    nickserv_name = conn.conf.get('nickserv_name', 'nickserv')
    nickserv_command = conn.conf.get('nickserv_command', 'IDENTIFY %s')
    if nickserv_password:
        conn.msg(nickserv_name, nickserv_command % nickserv_password)
        time.sleep(1)

    # set mode on self
    mode = conn.conf.get('mode')
    if mode:
        conn.cmd('MODE', [conn.nick, mode])

    # join channels
    for channel in conn.channels:
        conn.join(channel)
        time.sleep(1)  # don't flood JOINs

    # set user-agent
    ident, rev = get_version()


#@hook.regex(r'^\x01VERSION\x01$')
def version(inp, notice=None):
    ident, rev = get_version()
    notice('\x01VERSION Gary %s r%d - http://github.com/MikeRixWolfe/'
           'Gary/\x01' % (ident, rev))
