# coding=utf-8
from __future__ import absolute_import, print_function, unicode_literals
import threading
import json
import redis


botInstance = ''


def setup(bot):
    global botInstance
    botInstance = bot
    t = threading.Thread(name='announce', target=queue)
    t.start()


def queue():
    global botInstance
    redis_conn = redis.StrictRedis(host='localhost', port=6379, db=0)
    p = redis_conn.pubsub(ignore_subscribe_messages=True)
    p.subscribe('irc-announce')
    for message in p.listen():
        if message:
            # do something with the message
            data = json.loads(message['data'].decode('utf8'))
            botInstance.write(('PRIVMSG', data['channel']), data['msg'])
