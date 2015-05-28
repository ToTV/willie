# coding=utf-8
from totv import tracker
from willie import module
import humanize
from dateutil.parser import parse


@module.event('JOIN')
@module.rule('.*')
def helpJoin(bot, trigger):
    if trigger.admin or trigger.nick == bot.nick or trigger.sender.lower() != '#tot-help'.lower():
        return

    data = tracker.bot_api_request('/userinfo/' + trigger.nick)

    output = ''
    output_2 = ''

    if 'status_code' in data:
        output = data['message']
    else:
        output = "\00310[\0037 " + data['username'] + " \00310] :: [\0033 " + data['group'] + " \00310] " \
                                                                                              ":: [\0033 Uploaded:\0037 " + \
                 data['upload'] + " \00310|\0033 Downloaded:\0037 " + data['download'] + "  \00310|\0033 Bonus:\0037 " + \
                 data['bonus'] + " \00310] :: [\00314 " + bot.config.site.url + "user/" + \
                 data['username'] + " \00310]\017"

        donor = 'Yes' if data['donor'] == '1' else 'No'
        warned = 'No' if data['warned'] == 'Yes' else 'No'
        if data['enabled'] == "0":
            status = 'Unconfirmed'
        elif data['enabled'] == "1":
            status = 'Enabled'
        else:
            status = 'Disabled'

        time = humanize.naturaltime(parse(data['created_at']).strftime('%s'))

        output_2 = "\00310[\0033 Donor: \0037" + donor + " \00310] :: [\0033 Warned: \0037" + warned + " \00310] :: [\0033 Status: \0037" + status + " \00310] :: [\0033 Joined:\0037 " + time + " \00310]"

    bot.write(('NOTICE', 'trigger.nick'), trigger.nick + ', Welcome to ToTV support. Please type !help <your issue>. Replacing <your issue> with the problem you need help with. Once you have done this, please wait patiently for a staff member to arrive.')
    bot.write(('PRIVMSG', '#tot-help'), output)
    if output_2:
        bot.write(('PRIVMSG', '#tot-help'), output_2)


@module.commands('help')
def helpCommand(bot, trigger):
    if trigger.nick == bot.nick or trigger.sender.lower() != '#tot-help'.lower():
        return

    channels = bot.privileges
    online_users = []
    for channel in channels:
        if channel.lower() == '#tot-staff'.lower():
            online_users = bot.privileges[channel]

    bot.write(('PRIVMSG', '#tot-staff'), "!HELP REQUEST! " + ", ".join(online_users))
    bot.write(('PRIVMSG', '#tot-staff'),
              "!HELP REQUEST! " + trigger.nick + " needs help in #tot-help with request: " + trigger.group())

