# coding=utf8
"""
tld.py - Willie TLD Module
Copyright 2009-10, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""
from __future__ import unicode_literals
import re
import sys
from willie import web
from willie.module import commands, example
from totv.theme import render_error, EntityGroup, Entity, render
if sys.version_info.major >= 3:
    unicode = str

uri = 'https://en.wikipedia.org/wiki/List_of_Internet_top-level_domains'
r_tag = re.compile(r'<(?!!)[^>]+>')


@commands('tld')
@example('.tld ru')
def gettld(bot, trigger):
    """Show information about the given Top Level Domain."""
    page = web.get(uri)
    search = r'(?i)<td><a href="\S+" title="\S+">\.{0}</a></td>\n(<td><a href=".*</a></td>\n)?<td>([A-Za-z0-9].*?)</td>\n<td>(.*)</td>\n<td[^>]*>(.*?)</td>\n<td[^>]*>(.*?)</td>\n'
    search = search.format(trigger.group(2))
    re_country = re.compile(search)
    matches = re_country.findall(page)
    if not matches:
        search = r'(?i)<td><a href="\S+" title="(\S+)">\.{0}</a></td>\n<td><a href=".*">(.*)</a></td>\n<td>([A-Za-z0-9].*?)</td>\n<td[^>]*>(.*?)</td>\n<td[^>]*>(.*?)</td>\n'
        search = search.format(trigger.group(2))
        re_country = re.compile(search)
        matches = re_country.findall(page)
    if matches:
        matches = list(matches[0])
        i = 0
        while i < len(matches):
            matches[i] = r_tag.sub("", matches[i])
            i += 1
        desc = matches[2]
        if len(desc) > 400:
            desc = desc[:400] + "..."
        reply = "%s -- %s. IDN: %s, DNSSEC: %s" % (matches[1], desc,
                matches[3], matches[4])
        bot.reply(reply)
    else:
        search = r'<td><a href="\S+" title="\S+">.{0}</a></td>\n<td><span class="flagicon"><img.*?\">(.*?)</a></td>\n<td[^>]*>(.*?)</td>\n<td[^>]*>(.*?)</td>\n<td[^>]*>(.*?)</td>\n<td[^>]*>(.*?)</td>\n<td[^>]*>(.*?)</td>\n'
        search = search.format(unicode(trigger.group(2)))
        re_country = re.compile(search)
        matches = re_country.findall(page)
        if matches:
            matches = matches[0]
            dict_val = dict()
            dict_val["country"], dict_val["expl"], dict_val["notes"], dict_val["idn"], dict_val["dnssec"], dict_val["sld"] = matches
            for key in dict_val:
                if dict_val[key] == "&#160;":
                    dict_val[key] = "N/A"
                dict_val[key] = r_tag.sub('', dict_val[key])
            if len(dict_val["notes"]) > 400:
                dict_val["notes"] = dict_val["notes"][:400] + "..."
            items = [
                EntityGroup([Entity("TLD")]),
                EntityGroup([
                    Entity("Country", "{} ({}, {})".format(dict_val["country"], dict_val["expl"], dict_val["notes"])),
                    Entity("IDN", dict_val["idn"]),
                    Entity("DNSSEC", dict_val["dnssec"]),
                    Entity("SLD", dict_val["sld"])
                ])
            ]
            bot.say(render(items=items))
        else:
            bot.say(render_error("No matches found for TLD: {0}".format(unicode(trigger.group(2)))), "tld")
