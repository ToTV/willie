# coding=utf8
"""GeoIP lookup module"""
# Copyright 2011, Dimitri Molenaars, TyRope.nl,
# Copyright © 2013, Elad Alfassa <elad@fedoraproject.org>
# Licensed under the Eiffel Forum License 2.

from __future__ import unicode_literals

import pygeoip
import socket
import os
import gzip
from totv.theme import EntityGroup, Entity, render

urlretrieve = None
try:
    from urllib import urlretrieve
except ImportError:
    try:
        # urlretrieve has been put under urllib.request in Python 3.
        # It's also deprecated so this should probably be replaced with
        # urllib2.
        from urllib.request import urlretrieve
    except ImportError:
        pass

from willie.config.types import StaticSection, FilenameAttribute
from willie.module import commands, example
from willie.logger import get_logger

LOGGER = get_logger(__name__)


class GeoipSection(StaticSection):
    GeoIP_db_path = FilenameAttribute('GeoIP_db_path', directory=True)
    """Path of the directory containing the GeoIP db files."""


def configure(config):
    config.define_section('ip', GeoipSection)
    config.ip.configure_setting('GeoIP_db_path',
                                'Path of the GeoIP db files')


def _decompress(source, target, delete_after_decompression=True):
    """ Decompress a GZip file """
    f_in = gzip.open(source, 'rb')
    f_out = open(target, 'wb')
    f_out.writelines(f_in)
    f_out.close()
    f_in.close()
    if delete_after_decompression:
        os.remove(source)


def _find_geoip_db(bot):
    """ Find the GeoIP database """
    config = bot.config
    if config.has_section('ip') and config.ip.GeoIP_db_path is not None:
        cities_db = os.path.join(config.ip.GeoIP_db_path, 'GeoLiteCity.dat')
        ipasnum_db = os.path.join(config.ip.GeoIP_db_path, 'GeoIPASNum.dat')
        if os.path.isfile(cities_db) and os.path.isfile(ipasnum_db):
            return config.ip.GeoIP_db_path
        else:
            LOGGER.warning(
                'GeoIP path configured but DB not found in configured path'
            )
    if (os.path.isfile(os.path.join(bot.config.core.homedir, 'GeoLiteCity.dat')) and
            os.path.isfile(os.path.join(bot.config.core.homedir, 'GeoIPASNum.dat'))):
        return bot.config.core.homedir
    elif (os.path.isfile(os.path.join('/usr/share/GeoIP', 'GeoLiteCity.dat')) and
            os.path.isfile(os.path.join('/usr/share/GeoIP', 'GeoIPASNum.dat'))):
        return '/usr/share/GeoIP'
    elif urlretrieve:
        LOGGER.warning('Downloading GeoIP database')
        bot.say('Downloading GeoIP database, please wait...')
        geolite_city_url = 'http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz'
        geolite_ASN_url = 'http://download.maxmind.com/download/geoip/database/asnum/GeoIPASNum.dat.gz'
        geolite_city_filepath = os.path.join(bot.config.core.homedir, 'GeoLiteCity.dat.gz')
        geolite_ASN_filepath = os.path.join(bot.config.core.homedir, 'GeoIPASNum.dat.gz')
        urlretrieve(geolite_city_url, geolite_city_filepath)
        urlretrieve(geolite_ASN_url, geolite_ASN_filepath)
        _decompress(geolite_city_filepath, geolite_city_filepath[:-3])
        _decompress(geolite_ASN_filepath, geolite_ASN_filepath[:-3])
        return bot.config.core.homedir
    else:
        return False


@commands('iplookup', 'ip')
@example('.ip 8.8.8.8',
         r'[IP/Host Lookup] Hostname: google-public-dns-a.google.com | Location: United States | Region: CA | ISP: AS15169 Google Inc.',
         re=True,
         ignore='Downloading GeoIP database, please wait...')
def ip(bot, trigger):
    """IP Lookup tool"""
    if not trigger.group(2):
        return bot.reply("No search term.")
    query = trigger.group(2)
    db_path = _find_geoip_db(bot)
    if db_path is False:
        LOGGER.error('Can\'t find (or download) usable GeoIP database')
        bot.say('Sorry, I don\'t have a GeoIP database to use for this lookup')
        return False
    geolite_city_filepath = os.path.join(_find_geoip_db(bot), 'GeoLiteCity.dat')
    geolite_ASN_filepath = os.path.join(_find_geoip_db(bot), 'GeoIPASNum.dat')
    gi_city = pygeoip.GeoIP(geolite_city_filepath)
    gi_org = pygeoip.GeoIP(geolite_ASN_filepath)
    host = socket.getfqdn(query)

    items = [EntityGroup([Entity("Host Lookup")])]
    grouping = EntityGroup()
    grouping.append(Entity("Hostname", host))

    try:
        location = gi_city.country_name_by_name(query)
    except AttributeError:
        location = 'Unknown'
    grouping.append(Entity("Location", location))

    region_data = gi_city.region_by_name(query)
    try:
        region = region_data['region_code']  # pygeoip >= 0.3.0
    except KeyError:
        region = region_data['region_name']  # pygeoip < 0.3.0
    if region:
        grouping.append(Entity("Region", region))

    isp = gi_org.org_by_name(query)
    if isp:
        grouping.append(Entity("ISP", isp))
    items.append(grouping)

    bot.say(render(items=items))


if __name__ == "__main__":
    from willie.test_tools import run_example_tests
    run_example_tests(__file__)
