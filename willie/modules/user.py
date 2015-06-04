# coding=utf-8
from __future__ import print_function, unicode_literals
import json
import re
from totv.limit import RateLimit
from willie import module

from totv import tracker
from totv.theme import render, Entity, EntityGroup, UNDERLINE, NORMAL

_base_url = ""
_owner = ""


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
    method = trigger.group(1)
    username = trigger.group(2)
    irckey = trigger.group(3)

    if username is None or irckey is None:
        bot.say('Syntax: ENTER <username> <irckey>')

    data = tracker.bot_api_request('/userinfo/' + username)
    if 'status_code' in data:
        bot.say(data['message'])
        return

    if 'irc_key' not in data['settings'].keys():
        bot.say('Please set your irc key in your profile')
        return

    if data['enabled'] != "1":
        bot.say('You are not enabled, please join the support channel')
        return

    if data['settings']['irc_key'] != irckey:
        bot.say('You have given me an invalid irc key')
        return

    host = data['username'] + '.' + data['group'].replace(' ', '') + '.titansof.tv'
    ident = data['id']
    bot.write(('PRIVMSG', 'HOSTSERV'), 'SET ' + trigger.sender + ' ' + ident + '@' + host)
    for chan in data['settings']['irc_channels']:
        bot.write(('PRIVMSG', 'NickServ'), 'AJOIN ADD ' + trigger.sender + ' #' + chan)
    bot.reply(
        'Thank you for authing. If everything worked right, and your nick is registered, you should be able to join our channels. If you need help, join #ToT-help')


@module.require_privmsg
@module.rule('(ENTER)')
def enter(bot, trigger):
    bot.reply(
        'We now have a new system for joining our channels. Please register with NickServ, then /msg Titan AUTH <nick> <irckey>.')
    bot.say('Then you can simply /join #TitansofTv. If you need help, please join #ToT-Help')


@module.require_privmsg
@module.rule('(AUTODL) (\w+) (\w+)')
def userJoin(bot, trigger):
    method = trigger.group(1)
    username = trigger.group(2)
    irckey = trigger.group(3)

    if username is None or irckey is None:
        bot.say('Syntax: ENTER <username> <irckey>')

    data = tracker.bot_api_request('/userinfo/' + username)
    if 'status_code' in data:
        bot.say(data['message'])
        return

    if 'irc_key' not in data['settings'].keys():
        bot.say('Please set your irc key in your profile')
        return

    if data['enabled'] != "1":
        bot.say('You are not enabled, please join the support channel')
        return

    if data['settings']['irc_key'] != irckey:
        bot.say('You have given me an invalid irc key')
        return

    if method.lower() == 'autodl':
        bot.write(('SAJOIN', trigger.sender, '#tot-announce'))


@module.rule('\!lockdown (\S+) (\S+)')
def lock_down(bot, trigger):
    channel = trigger.group(1)
    level = trigger.group(2)

    if trigger.nick.lower() != _owner.lower():
        bot.say('nice try FBI')
        return

    if channel is None or level is None:
        bot.say('Syntax: !lockdown #channel level')

    bot.write(('MODE', channel, "+i"))

    excepts = tracker.bot_api_request('/get_levels/' + level)
    for ex in excepts:
        bot.write(('PRIVMSG', 'ChanServ'), 'mode ' + channel + ' lock add +I ' + ex)


@module.event('JOIN')
@module.rule('.*')
def userJoin(bot, trigger):
    if re.search('titansof\.tv', trigger.host.lower()):
        username = trigger.host.split('.')[0]

        data = tracker.bot_api_request('/userinfo/' + username)
        if 'status_code' in data:
            if data['message'].startswith('User Not Found'):
                bot.write(('NOTICE', trigger.nick), 'You are not enabled, please join the support channel')
                bot.write(('SAJOIN', trigger.nick), '#tot-help')
                bot.write(('SAPART', trigger.nick), trigger.sender())
                return
            else:
                bot.write(('PRIVMSG', '#tot-dev'), data['message'])
            return

        if trigger.sender.lower() == '#tot-help':
            print("channel is #tot-help")
            return

        if re.search('titansoftv|tot\-', trigger.sender.lower()):
            if data['enabled'] != "1":
                bot.write(('NOTICE', trigger.nick), 'You are not enabled, please join the support channel')
                bot.write(('SAJOIN', trigger.nick), '#tot-help')
                bot.write(('SAPART', trigger.nick), trigger.sender())
                return

            if trigger.host.split('.')[1].lower() != data['group'].lower():
                host = data['username'] + '.' + data['group'].replace(' ', '') + '.titansof.tv'
                ident = data['id']
                bot.write(('PRIVMSG', 'HOSTSERV'), 'SET ' + trigger.nick + ' ' + ident + '@' + host)
                for chan in data['settings']['irc_channels']:
                    bot.write(('PRIVMSG', 'NickServ'), 'AJOIN ADD ' + trigger.nick + ' #' + chan)
                    if data['group_id'] == '1':
                        bot.write(('PRIVMSG', 'ChanServ'), 'ACCESS #' + chan + ' ADD ' + trigger.nick + ' 9999')
                    elif data['group_id'] == '3':
                        bot.write(('PRIVMSG', 'ChanServ'), 'ACCESS #' + chan + ' ADD ' + trigger.nick + ' 10')
                    elif data['group_id'] == '6' or data['group_id'] == '4' or data['group_id'] == '7':
                        bot.write(('PRIVMSG', 'ChanServ'), 'ACCESS #' + chan + ' ADD ' + trigger.nick + ' 5')
                    elif data['group_id'] == '8' or data['group_id'] == '9':
                        bot.write(('PRIVMSG', 'ChanServ'), 'ACCESS #' + chan + ' ADD ' + trigger.nick + ' 3')
                    elif data['group_id'] == '5':
                        bot.write(('PRIVMSG', 'ChanServ'), 'ACCESS #' + chan + ' ADD ' + trigger.nick + ' 4')
                    else:
                        bot.write(('PRIVMSG', 'ChanServ'), 'ACCESS #' + chan + ' DEL ' + trigger.nick)


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
    if posex <= 0 or posat < 3 or posex + 1 == posat or posat + 1 == len(
            hostmask):  # All parts must be > 0 in length
        raise ValueError("Hostmask must be in the form '*!*@*'")
    return [hostmask[0:posex], hostmask[posex + 1: posat],
            hostmask[posat + 1:]]
