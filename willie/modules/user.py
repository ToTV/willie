# coding=utf-8
from __future__ import print_function, unicode_literals
import json
import re
import string
from willie import module
from totv import tracker
from totv.limit import RateLimit
from totv.theme import render, Entity, EntityGroup, UNDERLINE, NORMAL, render_error

_base_url = ""
_owner = ""


# A map of group_id -> irc access level granted by it
# TODO Move to config
group_levels = {
    0: 0,
    1: 9999,
    3: 10,
    4: 5,
    5: 4,
    6: 5,
    7: 5,
    8: 3,
    9: 3,
}


valid_chars = string.ascii_letters + string.digits


def normalize_name(username):
    return "".join(c for c in username if c in valid_chars)


def gen_host(username, group, host="titansof.tv"):
    return ".".join([normalize_name(username), group.replace(' ', ''), host])


def setup(bot):
    global _base_url, _owner
    _base_url = bot.config.api.url
    _owner = bot.config.core.owner
    tracker.configure(bot.config.api.url, bot.config.api.key)


# @willie.module.rule('(user|u)\s?(\w*)')
@RateLimit
@module.commands('user', 'u')
def user(bot, trigger):
    if trigger.group(2):
        user_search = trigger.group(2)
    else:
        user_search = trigger.nick

    data = tracker.bot_api_request('/userinfo/' + user_search)

    if 'status_code' in data:
        bot.say(data['message'])
    else:
        title_value = data.get('customtitle', None)
        title = Entity(title_value) if title_value else None
        url = bot.config.site.url + "user/" + data['username']
        out = render(
            # title="User Stats",
            items=[
                EntityGroup([Entity("User Stats")]),
                EntityGroup([
                    Entity(data['username']),
                    title,
                    Entity(data['group']),
                ]),
                EntityGroup([
                    Entity("Uploaded", data['upload']),
                    Entity("Downloaded", data['download']),
                    Entity("Bonus", data['bonus'])
                ]),
                EntityGroup([Entity("".join([UNDERLINE, url, NORMAL]))])
            ]
        )
        bot.say(out)


@module.require_privmsg
@module.rule('(AUTH) (\w+) (\w+)')
def user_auth(bot, trigger):
    username = trigger.group(2)
    irckey = trigger.group(3)
    try:
        if username is None or irckey is None:
            raise ValueError('Syntax: ENTER <username> <irckey>')

        data = tracker.bot_api_request('/userinfo/' + username)

        if 'status_code' in data:
            raise ValueError(data['message'])
        if 'irc_key' not in data['settings'].keys():
            raise ValueError('Please set your irc key in your profile')
        if data['enabled'] != "1":
            raise ValueError('You are not enabled, please join the support channel')
        if data['settings']['irc_key'] != irckey:
            raise ValueError('You have given me an invalid irc key')
    except ValueError as err:
        bot.say(render_error(str(err), "Auth"))
    else:
        host = gen_host(data["username"], data["group"])
        ident = data['id']
        bot.write(('PRIVMSG', 'HOSTSERV'), 'SET {} {}@{}'.format(trigger.sender, ident, host))
        for chan in data['settings']['irc_channels']:
            bot.write(('PRIVMSG', 'NickServ'), 'AJOIN ADD {} #{}'.format(trigger.sender, chan))
        msg = 'Thank you for authing. If everything worked right, and your nick is registered, ' \
              'you should be able to join our channels. If you need help, join #ToT-help'
        bot.say(render(items=[
            EntityGroup([Entity("Auth")]),
            EntityGroup([Entity(msg)]),
        ]))


@module.require_privmsg
@module.rule('(ENTER)')
def enter(bot, trigger):
    bot.reply(
        'We now have a new system for joining our channels. Please register with '
        'NickServ, then /msg Titan AUTH <nick> <irckey>.')
    bot.say('Then you can simply /join #TitansofTv. If you need help, please join #ToT-Help')


@module.require_privmsg
@module.rule('(AUTODL) (\w+) (\w+)')
def user_join(bot, trigger):
    method = trigger.group(1)
    username = trigger.group(2)
    irckey = trigger.group(3)

    if username is None or irckey is None:
        bot.say(render_error('Syntax: ENTER <username> <irckey>'), "Auth")

    data = tracker.bot_api_request('/userinfo/' + username)
    if 'status_code' in data:
        bot.say(data['message'])
    elif 'irc_key' not in data['settings'].keys():
        bot.say('Please set your irc key in your profile')
    elif data['enabled'] != "1":
        bot.say(render_error('You are not enabled, please join the support channel', "Auth"))
        return
    elif data['settings']['irc_key'] != irckey:
        bot.say(render_error('You have given me an invalid irc key', "Auth"))
        return
    else:
        bot.write(('SAJOIN', trigger.sender, '#tot-announce'))


@module.rule('\!lockdown (\S+) (\S+)')
def lock_down(bot, trigger):
    channel = trigger.group(1)
    level = trigger.group(2)

    if trigger.nick.lower() != _owner.lower():
        bot.say(render_error('nice try FBI', "Lockdown"))
        return

    if channel is None or level is None:
        bot.say(render_error('Syntax: !lockdown #channel level', "Lockdown"))

    bot.write(('MODE', channel, "+i"))

    excepts = tracker.bot_api_request('/get_levels/' + level)
    for ex in excepts:
        bot.write(('PRIVMSG', 'ChanServ'), 'mode {} lock add +I {}'.format(channel, ex))


@module.event('JOIN')
@module.rule('.*')
def user_join(bot, trigger):
    if not re.search('titansoftv|tot\-', trigger.sender.lower()):
        return
    if trigger.sender.lower() == '#tot-help':
        return
    # TODO no hardcode
    if bot.nick.lower() == "titan":
        return
    username = trigger.host.split('.')[0]

    ident = trigger.hostmask.split('!')[1].split('@')[0]

    if ident.isdigit() is True:
        data = tracker.bot_api_request('/userinfo/' + ident)
    else:
        data = tracker.bot_api_request('/userinfo/' + username)

    if 'status_code' in data:
        if data['message'].startswith('User Not Found'):
            bot.write(('NOTICE', trigger.nick), 'User not found, you are being joined to our help channel.')
            bot.write(('SAJOIN', trigger.nick), '#tot-help')
            bot.write(('SAPART', trigger.nick), str(trigger.sender))
            return
        else:
            bot.write(('PRIVMSG', '#tot-dev'), data['message'])
        return

    if data['enabled'] != "1":
        bot.write(('NOTICE', trigger.nick), 'You are not enabled, you are being joined to our help channel.')
        bot.write(('SAJOIN', trigger.nick), '#tot-help')
        bot.write(('SAPART', trigger.nick), str(trigger.sender))
        return

    if trigger.host.split('.')[1].lower() != data['group'].lower():
        host = gen_host(data["username"], data["group"])
        bot.write(('PRIVMSG', 'HOSTSERV'), 'SET {} {}@{}'.format(trigger.nick, data['id'], host))
        for chan in data['settings']['irc_channels']:
            bot.write(('PRIVMSG', 'NickServ'), "AJOIN ADD {} #{}".format(trigger.nick, chan))
            group_id = int(data.get('group_id', 0))
            if group_id > 0:
                bot.write(('PRIVMSG', 'ChanServ'), "ACCESS #{} ADD {} {}".format(
                    chan, trigger.nick, group_levels.get(group_id)
                ))
            else:
                bot.write(('PRIVMSG', 'ChanServ'), 'ACCESS #{} DEL {}'.format(chan, trigger.nick))


@module.interval(600)
def bonus(bot):
    online_users = [bot.privileges[c] for c in bot.privileges if c == '#TitansofTV']
    tracker.bot_api_request('/irc_bonus', 'POST', json.dumps(online_users))


def split_hostmask(hostmask):
    """
    Split a hostmask into its parts and return them.
    ValueError raised when the hostmask is not in the form "*!*@*"
    :param hostmask: Hostmask to parse
    :return: [user, ident, host]
    """
    posex = hostmask.find(u'!')
    posat = hostmask.find(u'@')
    if posex <= 0 or posat < 3 or posex + 1 == posat or posat + 1 == len(hostmask):
        # All parts must be > 0 in length
        raise ValueError("Hostmask must be in the form '*!*@*'")
    return [hostmask[0:posex], hostmask[posex + 1: posat], hostmask[posat + 1:]]
