from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING

from discord import File
from discord.ext.commands import Cog, command, param
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
        *,
        code: Codeblock | None = param(converter = codeblock_converter, default = None)
    ) -> None:
        if code is None:
            await ctx.reply("No code provided.")
            return

        async with await self.bot.session.post(
            "https://play.vlang.io/run",
            data = { "code": code.content },
        ) as response:
            text = await response.text()
            text = text.replace("`", "\u200B`\u200B")  # Zero-width space.

            if len(text) + 6 > 2000:
                await ctx.reply(
                    "The output was too long to be sent as a message. Here is a file instead:",
                    file = File(BytesIO(text.encode()), filename = "output.txt")
                )
            else:
                await ctx.reply(
                    "```" + text + "```"
                )


async def setup(bot: ReplBot) -> None:
    await bot.add_cog(REPL(bot))
