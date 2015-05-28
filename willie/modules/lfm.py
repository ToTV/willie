# coding=utf-8
from __future__ import absolute_import, print_function, unicode_literals
import json

import requests
from willie.module import commands, example
from willie import web


def configure(config):
    if config.option('Configure last.fm', False):
        config.add_section('lastfm')
        config.interactive_add('lastfm', 'apikey', 'Last.fm API key')


@commands('fm', 'last', 'lastfm', 'lfm', 'np')
def lastfm(willie, trigger):
    user = trigger.group(2)
    apikey = str(willie.config.lastfm.apikey)
    if not (user and user != ''):
        user = willie.db.get_nick_value(trigger.nick, 'lastfm_user')
        if not user:
            willie.reply("Invalid username given or no username set. Use .fmset to set a username.")
            return
    # username variable prepared for insertion into REST string
    quoted_user = web.quote(user)
    # json formatted output for recent track
    recent_page = web.get(
        "http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user=%s&api_key=%s&format=json" % (
            quoted_user, apikey))
    recent_track = json.loads(recent_page)['recenttracks']['track'][0]
    #artist and track name pulled from recent_track
    quoted_artist = web.quote(recent_track['artist']['#text'])
    quoted_track = web.quote(recent_track['name'])
    #json formatted track info
    trackinfo = requests.get(
        "http://ws.audioscrobbler.com/2.0/?method=track.getInfo&artist=%s&track=%s&username=%s&api_key=%s&format=json" % (
            quoted_artist, quoted_track, quoted_user, apikey))
    print(trackinfo.text)
    if 'track' in trackinfo.json():
        trackinfo = trackinfo.json()['track']
        try:
            playcount = trackinfo['userplaycount']
        except KeyError:
            playcount = "unknown"
        loved = int(trackinfo['userloved'])
    else:
        loved = 0
        playcount = 'Unknown'

    try:
        if loved > 0:
            willie.say('\x035' + u'\u2665' + '\x03 %s - %s - (%s plays)' % (
                recent_track['artist']['#text'], recent_track['name'], playcount))
        else:
            willie.say(
                u'\u266A' + ' %s - %s (%s plays)' % (recent_track['artist']['#text'], recent_track['name'], playcount))
    except KeyError:
        willie.say("Couldn't find any recent tracks")


@commands('fmset')
@example('!fmset daftpunk69')
def update_lastfm_user(bot, trigger):
    user = trigger.group(2)
    bot.db.set_nick_value(trigger.nick, 'lastfm_user', user)
    bot.reply('Thanks, ' + user)
