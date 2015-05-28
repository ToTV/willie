# coding=utf-8
from __future__ import absolute_import, print_function, unicode_literals
import datetime
from urllib import parse

import humanize
import requests
from willie import module

from totv import site
from totv.theme import Entity, render, EntityGroup


_base_url = ""


def setup(bot):
    global _base_url
    _base_url = bot.config.site.url


@module.commands('series', 's')
def series(bot, trigger):
    if trigger.group(2) is None:
        bot.say('You need to give me a series to search!')
    else:
        data = site.callApi('/series/search?series=' + parse.quote(trigger.group(2)))
        if 'status_code' in data:
            bot.say(data['message'])
        else:
            items = [EntityGroup([Entity(data['title'])])]
            details = EntityGroup()
            details.append(Entity("Network", data['network']))
            details.append(Entity("Status", data['status']))
            details.append(Entity("Year", data['year']))
            if data['air_day'] is not None:
                details.append(Entity("Airs", "{} @ {}".format(data['air_day'], data['air_time'])))
            items.append(details)
            items.append(Entity(_base_url + "series/" + str(data['slug'] if data['slug'] else data['id'])))
            bot.say(render(items=items))

            if 'id' in data['next_episode']:
                items_next = [EntityGroup([Entity("Next Episode")])]
                next_details = EntityGroup()
                # next_episode = "\00310[\0037 Next Episode \00310]"
                if data['next_episode']['title'] is None:
                    data['next_episode']['title'] = 'N/A'
                next_details.append(Entity(data['next_episode']['title']))
                next_details.append(Entity("S{:02}E{:02}".format(
                    int(data['next_episode']['season']), int(data['next_episode']['episode']))))
                # next_episode += " :: [\0033 " + data['next_episode']['title'] + " \00310|\0033  + " \00310]"
                items_next.append(next_details)
                items_next.append(EntityGroup([Entity(humanize.naturaltime(
                    datetime.datetime.utcfromtimestamp(int(data['next_episode']['first_aired']))))]))
                bot.say(render(items=items_next))

            if 'id' in data['last_episode']:
                items_last = [EntityGroup([Entity("Last Episode")])]
                next_details = EntityGroup()
                # next_episode = "\00310[\0037 Next Episode \00310]"
                if data['last_episode']['title'] is None:
                    data['last_episode']['title'] = 'N/A'
                next_details.append(Entity(data['last_episode']['title']))
                next_details.append(Entity("S{:02d}E{:02d}".format(
                    int(data['last_episode']['season']), int(data['last_episode']['episode']))))
                # next_episode += " :: [\0033 " + data['next_episode']['title'] + " \00310|\0033  + " \00310]"
                items_last.append(next_details)
                items_last.append(EntityGroup([Entity(humanize.naturaltime(
                    datetime.datetime.utcfromtimestamp(int(data['last_episode']['first_aired']))))]))
                bot.say(render(items=items_last))


@module.commands('next', 'n')
def next(bot, trigger):
    if trigger.group(2) is None:
        bot.say('You need to give me a series to search!')
    else:
        r = requests.get('http://services.tvrage.com/tools/quickinfo.php?show=%s' % trigger.group(2))

        if r.text.startswith('No Show Results Were Found For'):
            bot.say(r.text)
            return

        showinfo = {}
        for rline in r.text[5:].splitlines():
            a, b = rline.split('@', 1)
            showinfo[a] = b

        items = [EntityGroup([Entity(showinfo['Show Name']), Entity(showinfo['Country'])])]
        details = EntityGroup()
        details.append(Entity("Status", showinfo['Status']))
        if 'Network' in showinfo:
            details.append(Entity("Network", showinfo['Network']))
        if 'Airtime' in showinfo:
            details.append(Entity("Airtime", showinfo['Airtime']))
        items.append(details)
        bot.say(render(items=items))

        # out = []
        # out.append('\x02%(Show Name)s (%(Country)s)\x02' % showinfo)
        # out.append('\x0307%(Status)s\x03' % showinfo)
        # if 'Airtime' in showinfo:
        # out.append('\x0307%(Airtime)s\x03' % showinfo)
        # if 'Network' in showinfo:
        #     out.append('\x0307on %(Network)s\x03' % showinfo)
        # bot.say(' / '.join(out))
        items_next = [EntityGroup([Entity("Next Episode")])]
        if 'Next Episode' in showinfo:
            if 'RFC3339' in showinfo:
                time = datetime.datetime.strptime(showinfo['RFC3339'].rsplit('-', 1)[0], '%Y-%m-%dT%H:%M:%S')
                from_now = humanize.naturaltime(time)
            else:
                from_now = None
            epnumber, epname, epdate = showinfo['Next Episode'].split('^')

            next_details = EntityGroup()
            next_details.append(Entity(epname))
            next_details.append(Entity(epnumber))
            next_details.append(Entity("Airs on", epdate))
            if from_now:
                next_details.append(Entity(from_now))
            # next_episode += " :: [\0033 " + data['next_episode']['title'] + " \00310|\0033  + " \00310]"
            items_next.append(next_details)
        else:
            items_next.append(Entity('No next episode found'))
        bot.say(render(items=items_next))

        items_last = [EntityGroup([Entity("Last Episode")])]
        if 'Latest Episode' in showinfo:
            epnumber, epname, epdate = showinfo['Latest Episode'].split('^')
            last_details = EntityGroup()
            last_details.append(Entity(epname))
            last_details.append(Entity(epnumber))
            last_details.append(Entity("Aired on", epdate))
            items_last.append(last_details)
        else:
            items_last.append(Entity('No last episode found'))
        bot.say(render(items=items_last))
