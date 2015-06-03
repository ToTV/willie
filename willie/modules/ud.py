# coding=utf-8
from __future__ import absolute_import, print_function, unicode_literals
import logging
from urllib import parse
import requests
from willie.module import commands
from totv.theme import render, EntityGroup, Entity, render_error

logger = logging.getLogger()


@commands('ud', 'urbandictionary')
def urbandictionary(bot, trigger):
    if not trigger.group(2):
        return bot.say('What?')
    term = parse.quote(trigger.group(2))
    url = "http://api.urbandictionary.com/v0/define?term=" + term
    data = requests.get(url).json()
    if str(data['result_type']) != 'no_results':
        show_ud(bot, data)
    else:
        bot.say(render_error("No definition found"))


@commands('udr', 'urbandictionaryrandom', 'udrandom')
def urbandictionaryrandom(bot, trigger):
    try:
        data = requests.get("http://api.urbandictionary.com/v0/random").json()
    except Exception:
        logger.exception("Failed to fetch UD api data")
        render_error("Failed to fetch data over API, server down probably")
    else:
        show_ud(bot, data)


def show_ud(bot, data):
    if str(data['list'][0]['example']) != "":
        example = str(data['list'][0]['example'])
    else:
        example = "I can't come up with a funny example."
    bot.say(render(items=[
        EntityGroup([Entity("UrbanDic")]),
        EntityGroup([Entity(data['list'][0]['word'], str(data['list'][0]['definition']))])
    ]))
    bot.say(render(items=[
        EntityGroup([Entity("UrbanDic")]),
        EntityGroup([Entity("Example", example)])
    ]))
