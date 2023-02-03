from __future__ import annotations

from io import BytesIO
from typing import Literal, TYPE_CHECKING

from discord import File
from discord.ext.commands import Cog, command
from jishaku.codeblocks import codeblock_converter

if TYPE_CHECKING:
    from discord import MessageReference, TextChannel
    from discord.ext.commands import Context

    from .. import ReplBot


def sanitize_str_for_codeblock(string: str) -> str:
    return string.replace("`", "\u200B`\u200B")  # Zero-width space.


async def get_message_content(channel: TextChannel, ref: MessageReference) -> str:
    if ref.resolved:
        return ref.resolved.content
    else:
        message = await channel.fetch_message(ref.message_id)
        return message.content


class Playground(
    Cog,
    name = "Playground",
    description = "V Playground commands.",
):
    def __init__(self, bot: ReplBot) -> None:
        self.bot = bot

    async def run_test_common(
        self,
        ctx: Context,
        code: str | None,
        *,
        type: Literal["run"] | Literal["run_test"]
    ) -> None:
        if not code:
            if not (reply := ctx.message.reference):
                await ctx.reply("No code provided.")
                return

            content = await get_message_content(ctx.channel, reply)

            if (c_stripped := content.lstrip("https://")).startswith("play.vlang.io/?query="):
                query = c_stripped.lstrip("play.vlang.io/?query=").split(" ", 1)[0]
                code = await self.get_query_content(query)

                if not code:
                    await ctx.reply("Invalid query.")
                    return
            else:
                code = codeblock_converter(content).content

        async with await self.bot.session.post(
            f"https://play.vlang.io/{type}",
            data = { "code": code },
        ) as response:
            body = await response.json()
            text = sanitize_str_for_codeblock(body["output"])

            if len(text) + 7 > 2000:
                await ctx.reply(
                    "The output was too long to be sent as a message. Here is a file instead:",
                    file = File(BytesIO(text.encode()), filename = "output.txt")
                )
                return

            await ctx.reply(
                "```\n" + text + "```"
            )

    @command(
        aliases = ("eval", "repl"),
        brief = "Runs V code.",
        help = "Runs V code."
    )
    async def run(
        self,
        ctx: Context,
        *,
        query_or_code: str | None = None
    ) -> None:
        await self.run_test_common(ctx, query_or_code, type = "run")

    @command(
        brief = "Runs tests of V code.",
        help = "Runs tests of V code."
    )
    async def test(
        self,
        ctx: Context,
        *,
        query_or_code: str | None = None
    ) -> None:
        await self.run_test_common(ctx, query_or_code, type = "run_test")

    async def get_query_content(self, query: str) -> str | None:
        async with await self.bot.session.post(
            f"https://play.vlang.io/query",
            data = { "hash": query }
        ) as response:
            text = sanitize_str_for_codeblock(await response.text())

            if text == "Not found.":
                return None

            return text

    @command(
        aliases = ("download",),
        brief = "Shows the code in a V playground link.",
        help = "Shows the code in a V playground link."
    )
    async def show(self, ctx: Context, query: str | None = None) -> None:
        if not query:
            if not (reply := ctx.message.reference):
                await ctx.reply("No query provided.")
                return

            content = await get_message_content(ctx.channel, reply)

            if "play.vlang.io/?query=" in content:
                query = content.split("play.vlang.io/?query=", 1)[1].split(" ", 1)[0]
            else:
                query = content.split(" ", 1)[0]

        query = query.lstrip("https://").lstrip("play.vlang.io/?query=")

        if not query:
            await ctx.reply("No query provided.")
            return

        code = await self.get_query_content(query)

        if not code:
            await ctx.reply("Invalid link.")
            return

        if len(code) + 8 > 2000:
            await ctx.reply(
                "The code was too long to be sent as a message. Here is a file instead:",
                file = File(BytesIO(code.encode()), filename = "code.v")
            )
            return

        await ctx.reply(
            "```v\n" + code + "```"
        )


async def setup(bot: ReplBot) -> None:
    await bot.add_cog(Playground(bot))
