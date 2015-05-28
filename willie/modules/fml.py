# coding=utf8
"""
fml.py - Willie FMyLife Module, now in a very compact form!
Original author: Meicceli
Licensed under the GNU Lesser General Public License Version 3 (or greater at your wish).
"""
from __future__ import absolute_import, print_function, unicode_literals
import xml.etree.ElementTree as ET
import logging
from willie import web
from willie.module import commands
from totv.theme import EntityGroup, Entity, render

log = logging.getLogger()


@commands('fml')
def fmylife(bot, trigger):
    try:
        fml = ET.fromstring(web.get('http://api.fmylife.com/view/random?language=en&key=53637bae986a8')).find(
            'items/item/text').text
    except Exception as err:
        log.exception("Failed to fetch fml data")
        bot.say("error! :`(")
    else:
        bot.say(render(items=[EntityGroup([Entity("FML")]), EntityGroup([Entity(fml)])]))
