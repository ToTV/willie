# coding=utf-8
from willie.module import commands
from totv.theme import render, Entity, UNNUKE, UNDERLINE, NORMAL
from totv.theme import EntityGroup


@commands('themetest')
def torrent_info(bot, trigger):
    out = render(
        # title="User Stats",
        items=[
            EntityGroup([Entity("User Stats")]),
            EntityGroup([
                Entity("toor"),
                Entity("Custom Title"),
                Entity("Banned"),
            ]),
            EntityGroup([
                Entity("Uploaded", "12 MiB"),
                Entity("Downloaded", "83 TiB"),
                Entity("Bonus", "69133769 {}".format(UNNUKE))
            ]),
            Entity("{}http://zombo.com?user=toor{}".format(UNDERLINE, NORMAL))
        ]
    )
    bot.say(out)
