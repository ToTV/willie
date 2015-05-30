# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals, absolute_import
from os.path import join
from willie.module import commands
from totv import bet, lib_dir
from totv import db
from totv.theme import render_error


@commands("bet")
def bet_user_place(bot, trigger):
    session = db.Session()
    if not trigger.group(2):
        return bot.say(render_error("Incomplete command", "Bet"))
    args = trigger.split(" ", 3)
    bet_instance = bet.Bet(*args[1:])
    b = bet.place(session, bet_instance)
    bot.say(repr(bet_instance))


def setup(bot):
    db_file = join(lib_dir, "db.sqlite")
    db.make_engine("sqlite+pysqlite:///{}".format(db_file))
