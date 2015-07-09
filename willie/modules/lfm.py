# coding=utf-8
from __future__ import absolute_import, print_function, unicode_literals
import json

import requests
from totv.theme import render_error, render, EntityGroup, Entity
from willie.module import commands, example
from willie import web


def configure(config):
    if config.option('Configure last.fm', False):
        config.add_section('lastfm')
        config.interactive_add('lastfm', 'apikey', 'Last.fm API key')


@commands('fm', 'last', 'lastfm', 'lfm', 'np')
def lastfm(bot, trigger):
    user = trigger.group(2)
    apikey = str(bot.config.lastfm.apikey)
    if not (user and user != ''):
        user = bot.db.get_nick_value(trigger.nick, 'lastfm_user')
        if not user:
            bot.reply(render_error("Invalid username given or no username set. "
                                   "Use {}fmset to set a username.".format(bot.config.core.prefix), "lfm"))
            return
    # username variable prepared for insertion into REST string
    quoted_user = web.quote(user)
    # json formatted output for recent track
    recent_page = web.get(
        "http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user=%s&api_key=%s&format=json" % (
            quoted_user, apikey))
    try:
        recent_track = json.loads(recent_page)['recenttracks']['track'][0]
    except KeyError:
        return bot.say(render_error("Failed to fetch user data", "lastfm"))
    #artist and track name pulled from recent_track
    quoted_artist = web.quote(recent_track['artist']['#text'])
    quoted_track = web.quote(recent_track['name'])
    #json formatted track info
    trackinfo = requests.get(
        "http://ws.audioscrobbler.com/2.0/?method=track.getInfo&artist=%s&track=%s&username=%s&api_key=%s&format=json" % (
            quoted_artist, quoted_track, quoted_user, apikey))

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
            prefix = '\x035' + u'\u2665' + '\x03'
        else:
            prefix = '\u266A'
        bot.say(render(items=[
            EntityGroup([Entity("LastFM")]),
            EntityGroup([
                Entity("{} {}".format(prefix, recent_track['artist']['#text'])),
                Entity(recent_track['name'])
            ]),
            EntityGroup([Entity("Plays", playcount)])
        ]))
    except KeyError:
        bot.say(render_error("Couldn't find any recent tracks", "lastfm"))


@commands('fmset')
@example('!fmset daftpunk69')
def update_lastfm_user(bot, trigger):
    user = trigger.group(2)
    bot.db.set_nick_value(trigger.nick, 'lastfm_user', user)
    bot.say(render(items=[
        EntityGroup([Entity("LastFM")]),
        EntityGroup([Entity("User set successfully")])
    ]))
