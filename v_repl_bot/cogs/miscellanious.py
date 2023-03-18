from __future__ import annotations

from datetime import timedelta as TimeDelta
from inspect import cleandoc as strip
from platform import python_version
from time import monotonic as get_monotonic, time as get_time
from typing import TYPE_CHECKING

from discord.ext.commands import Cog, command

if TYPE_CHECKING:
    from discord.ext.commands import Context

    from .. import ReplBot


class Miscellaneous(
    Cog,
    name = "Miscellaneous",
    description = "Miscellaneous commands.",
):
    def __init__(self, bot: ReplBot) -> None:
        self.bot = bot
        self.bot.help_command.cog = self

    def cog_unload(self) -> None:
        self.bot.help_command.cog = None
        self.bot.help_command.hidden = True

    @command(
        brief = "Sends the bots ping.",
        help = "Sends the bots ping."
    )
    async def ping(self, ctx: Context) -> None:
        ts = get_monotonic()
        message = await ctx.reply("Pong!")
        ts = get_monotonic() - ts
        await message.edit(content = f"Pong! `{int(ts * 1000)}ms`")

    @command(
        brief = "Sends the GitHub repository link for the bot.",
        help = "Sends the GitHub repository link for the bot.",
    )
    async def github(self, ctx: Context) -> None:
        # Not a button since I want the embed.
        await ctx.reply("https://github.com/RGBCube/VReplBot")

    @command(
        brief = "Sends info about the bot.",
        help = "Sends info about the bot."
    )
    async def info(self, ctx: Context) -> None:
        await ctx.reply(
            strip(
                f"""
            ```
            Bot Info
            ========
            Python Version: v{python_version()}
            Uptime:         {TimeDelta(seconds = int(get_time() - self.bot.ready_timestamp))}
            ```
            """
            )
        )


async def setup(bot: ReplBot) -> None:
    await bot.add_cog(Miscellaneous(bot))
