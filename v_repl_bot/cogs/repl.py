from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands
from discord.ext.commands import Cog, command
from jishaku.codeblocks import Codeblock, codeblock_converter

if TYPE_CHECKING:
    from discord.ext.commands import Context

    from .. import ReplBot


class REPL(
    Cog,
    name = "REPL",
    description = "REPL (Read, Eval, Print, Loop) commands.",
):
    def __init__(self, bot: ReplBot) -> None:
        self.bot = bot

    @command(
        aliases = ("run", "repl"),
        brief = "Runs V code.",
        help = "Runs V code."
    )
    async def eval(
        self,
        ctx: Context,
        code: Codeblock | None = commands.param(converter = codeblock_converter, default = None)
    ) -> None:
        if code is None:
            await ctx.reply("No code provided.")

        with self.bot.session.post(
            "https://vlang.io/play",
            data = { "code": code.content },
        ) as response:
            await ctx.reply(
                "```\n" + response.text.replace("`", "\u200B`\u200B") + "\n```"
            )  # Zero-width space.


async def setup(bot: ReplBot) -> None:
    await bot.add_cog(REPL(bot))
