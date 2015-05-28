# coding=utf-8
from __future__ import absolute_import, print_function, unicode_literals
from totv import tracker
from willie import module


@module.event('001')
@module.rule('.*')
def start(bot, trigger):
    bot.write(('oper', bot.config.core.oper_name, bot.config.core.oper_pass))


@module.event('251')
@module.rule('.*')
def start1(bot, trigger):
    try:
        channels = tracker.bot_api_request('/get_channels')
    except ValueError:
        print("OPER api not available")
    else:
        bot.write(('PRIVMSG', 'NickServ'), 'IDENTIFY ' + bot.config.core.auth_password)
        # bot.write(('PRIVMSG', 'OperServ', 'SET', 'SuperAdmin', 'ON'))
        for channel in channels:
            bot.write(('SAJOIN', 'Titan', '#' + channel))

        for channel in channels:
            bot.write(('SAMODE', '#' + channel, '+ao', bot.config.core.nick, bot.config.core.nick))

