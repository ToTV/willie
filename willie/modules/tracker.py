# coding=utf-8
"""
Simple client to interact with the backend tracker instance.
"""
from __future__ import print_function, unicode_literals, absolute_import
import requests
from willie.module import commands
from guessit import guess_file_info
from totv.theme import render_error, render, Entity, EntityGroup


class TrackerClient(object):
    def __init__(self, host):
        self._host = host

    def _request(self, path, method='get', payload=None):
        if method == "get":
            resp = requests.get(self._make_url(path), verify=False)
        elif method == "post":
            resp = requests.post(self._make_url(path), json=payload, verify=False)
        elif method == "delete":
            resp = requests.delete(self._make_url(path), verify=False)
        else:
            raise Exception("no")
        return resp

    def _make_url(self, path):
        url = "{}{}".format(self._host, path)
        return url

    def torrent_get(self, info_hash):
        resp = self._request("/torrent/{}".format(info_hash.lower()))
        if resp.ok:
            return resp.json()
        return None

    def torrent_get_all(self, torrent_ids):
        pass

    def torrent_add(self, info_hash, torrent_id):
        return self._request("/torrent", method='post', payload={
            'info_hash': info_hash,
            'torrent_id': torrent_id
        })

    def torrent_del(self, torrent_id):
        return self._request("/torrent/{}".format(torrent_id), method='delete').ok

    def user_get_active(self, user_id):
        pass

    def user_get_incomplete(self, user_id):
        pass

    def user_get_complete(self, user_id):
        pass

    def user_get_hnr(self, user_id):
        pass

    def user_update(self, user_id, uploaded=None, downloaded=None, passkey=None, can_leech=None):
        user = self.user_get(user_id)
        if not user:
            return False
        updated_data = {
            'uploaded': uploaded if uploaded is not None else user['uploaded'],
            'downloaded': downloaded if downloaded is not None else user['downloaded'],
            'can_leech': can_leech if can_leech is not None else user['can_leech'],
            'passkey': passkey if passkey is not None else user['passkey'],
        }

        resp = self._request("/user/{}".format(user_id), 'post', payload=updated_data)
        return resp.ok

    def user_get(self, user_id):
        resp = self._request("/user/{}".format(user_id))
        return resp.json() if resp.ok else None

    def user_add(self, user_id, passkey):
        resp = self._request("/user", method='post', payload={
            'user_id': user_id,
            'passkey': passkey
        })
        return resp.ok

    def whitelist_del(self, prefix):
        resp = self._request("/whitelist/{}".format(prefix), method='delete')
        return resp.ok

    def whitelist_add(self, prefix, client_name):
        resp = self._request("/whitelist", method='post', payload={
            'prefix': prefix,
            'client': client_name
        })
        return resp.ok


@commands('swarm')
def torrent_info(bot, trigger):
    client = TrackerClient(bot.config.tracker.host)
    info_hash = trigger.group(2).strip()
    torrent = client.torrent_get(info_hash)
    if torrent and torrent.get("enabled", False):
        top_speed_up = 0
        top_speed_dn = 0
        uid_up = 0
        uid_dn = 0
        torrent_id = torrent.get("torrent_id", False)
        for peer in torrent.get("peers", []):
            if peer.get('speed_up_max', 0):
                top_speed_up = peer.get('speed_up_max', 0)
                uid_up = peer.get('username', "n/a")
            if peer.get('speed_dn_max', 0):
                top_speed_dn = peer.get('speed_dn_max', 0)
                uid_dn = peer.get('username', "n/a")
        resp = render(items=[
            EntityGroup([Entity("Swarm")]),
            EntityGroup([Entity(torrent.get("name", info_hash[0:4]))]),
            EntityGroup([
                Entity("Seeders", torrent.get("seeders", 0)),
                Entity("Leechers", torrent.get("leechers", 0)),
                Entity("Snatches", torrent.get("snatches", 0)),
                Entity("Top Speed Up [{}]".format(uid_up), "{:.2f} MiB/s".format(top_speed_up / 1024.0 / 1024.0)),
                Entity("Top Speed Dn [{}]".format(uid_dn), "{:.2f} MiB/s".format(top_speed_dn / 1024.0 / 1024.0))
            ]),
            EntityGroup([Entity("{}api/torrents/{}/download".format(bot.config.site.url, torrent_id))])
        ])
        bot.say(resp)
    else:
        bot.say(render_error("Infohash Not found", "swarm"))


@commands("parse")
def parse(bot, trigger):
    release_name = trigger.group(2).strip()
    attrs = guess_file_info(release_name.lower(), options={'name_only': True})
    items = [EntityGroup([Entity("RlsParse")])]

    for k, v in attrs.items():
        items.append(EntityGroup([Entity(k, v)]))
    bot.say("{}".format(render(items=items)))
