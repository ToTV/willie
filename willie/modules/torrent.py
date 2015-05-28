# coding=utf-8
from __future__ import absolute_import, print_function, unicode_literals
from willie.module import commands
from totv import tracker


@commands('torrent', 't')
def user(bot, trigger):
    if trigger.group(2):
        search = trigger.group(2)
    else:
        bot.reply('Please give me something to search!')
        return

    torrents = tracker.bot_api_request('/torrent_search/?search=' + search)

    if 'status_code' in torrents:
        bot.say(torrents['message'])
    else:
        for data in torrents:
            if int(data['episode_id']) is not 0:
                title = data['episode']
                url = 'series/' + data['series_id'] + '/episode/' + data['episode_id']
            else:
                title = data['season']
                url = 'series/' + data['series_id'] + '/season/' + data['season_id']
            output = "\00310[\0037 " + data['series'] + " " + title + " \00310] :: [\0033 " + data[
                'release_name'] + " \00310] " \
                                  ":: [\0037 " + data['container'] + " \00310|\0037 " + data[
                         'codec'] + " \00310|\0037 " + data['source'] + " \00310|\0037 " + data[
                         'resolution'] + " \00310|\0037 " + data['origin'] + " \00310] " \
                                                                             ":: [\00314 " + bot.config.site.url + url + " \00310] :: [\00314 " + bot.config.site.url + "api/torrents/" + \
                     data['id'] + "/download" + " \00310]\017"
            bot.write(('PRIVMSG', trigger.sender), output)
