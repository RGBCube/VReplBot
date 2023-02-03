from __future__ import annotations

import json
from io import BytesIO
from typing import Literal, TYPE_CHECKING

from discord import File
from discord.ext.commands import Cog, command
from jishaku.codeblocks import codeblock_converter

from .error_handler import StopCommandExecution

if TYPE_CHECKING:
    from discord import MessageReference, TextChannel
    from discord.ext.commands import Context

    from .. import ReplBot


class Playground(
    Cog,
    name = "Playground",
    description = "V Playground commands.",
):
    def __init__(self, bot: ReplBot) -> None:
        self.bot = bot

    async def get_code(self, ctx: Context, query: str) -> str:
        async with await self.bot.session.post(
            f"https://play.vlang.io/query",
            data = { "hash": query }
        ) as response:
            text = await response.text()

            if text == "Not found.":
                await ctx.reply("Invalid query.")
                raise StopCommandExecution()

            return text

    async def share_code(self, code: str) -> str:
        async with await self.bot.session.post(
            f"https://play.vlang.io/share",
            data = { "code": code },
        ) as response:
            return await response.text()

    async def run_code(self, code: str) -> tuple[bool, str]:
        async with await self.bot.session.post(
            f"https://play.vlang.io/run",
            data = { "code": code },
        ) as response:
            body = json.loads(await response.text())

            return body["ok"], body["output"]

    async def test_code(self, code: str) -> tuple[bool, str]:
        async with await self.bot.session.post(
            f"https://play.vlang.io/run_test",
            data = { "code": code },
        ) as response:
            body = json.loads(await response.text())

            return body["ok"], body["output"]

    @staticmethod
    async def get_message_content(channel: TextChannel, ref: MessageReference) -> str:
        if ref.resolved:
            return ref.resolved.content
        else:
            message = await channel.fetch_message(ref.message_id)
            return message.content

    @staticmethod
    def grep_code(content: str) -> str:
        content = "`" + content.split("`", 1)[1].rsplit("`", 1)[0] + "`"

        return codeblock_converter(content).content

    @staticmethod
    def grep_link_query(content: str) -> str | None:
        if "play.vlang.io/?query=" not in content:
            return None

        query = content.split("play.vlang.io/?query=", 1)[1].split(" ", 1)[0]

        if not query:  # Empty string.
            return None

        return query

    @staticmethod
    def extract_link_query(content: str) -> str | None:
        if (no_http_content := content.lstrip("https://")).startswith("play.vlang.io/?query="):
            return no_http_content.lstrip("play.vlang.io/?query=").split(" ", 1)[0]

    @staticmethod
    def sanitize(string: str) -> str:
        return string.replace("`", "\u200B`\u200B")  # Zero-width space.

    async def run_test_common(
        self,
        ctx: Context,
        query_or_code: str | None,
        *,
        type: Literal["run", "test"],
    ):
        if not query_or_code:
            if not (ref := ctx.message.reference):
                await ctx.reply("No code provided.")
                return

            content = await self.get_message_content(ctx.channel, ref)

            if query := self.grep_link_query(content):
                code = await self.get_code(ctx, query)
            else:
                code = self.grep_code(content)

        elif query := self.extract_link_query(query_or_code):
            code = await self.get_code(ctx, query)
        else:
            code = codeblock_converter(query_or_code).content

        ok, output = await (self.run_code(code) if type == "run" else self.test_code(code))
        sanitized_output = self.sanitize(output)

        sentence = "Success!" if ok else "Failure!"

        if len(sanitized_output) > 1900:
            await ctx.reply(
                f"**{sentence}**",
                file = File(BytesIO(output.encode()), "output.txt")
            )
        else:
            await ctx.reply(
                f"**{sentence}**\n"
                f"```v\n{self.sanitize(sanitized_output)}```"
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
        await self.run_test_common(ctx, query_or_code, type = "test")

    @command(
        aliases = ("download",),
        brief = "Shows the code in a V playground link.",
        help = "Shows the code in a V playground link."
    )
    async def show(self, ctx: Context, query: str | None = None) -> None:
        if not query:
            if not (ref := ctx.message.reference):
                await ctx.reply("No query provided.")
                return

            content = await self.get_message_content(ctx.channel, ref)

            query = self.grep_link_query(content)
        else:
            query = self.extract_link_query(query)

        if not query:
            await ctx.reply("No query provided.")
            return

        code = await self.get_code(ctx, query)
        sanitized_code = self.sanitize(code)

        if len(sanitized_code) > 1900:
            await ctx.reply(
                "The code is too long to be shown. Here's a file instead:",
                file = File(BytesIO(code.encode()), "code.v")
            )
        else:
            await ctx.reply(f"```v\n{sanitized_code}```")

    @command(
        aliases = ("upload",),
        brief = "Uploads code to V playground.",
        help = "Uploads code to V playground."
    )
    async def share(self, ctx: Context, *, code: str | None = None) -> None:
        if not code:
            if not (ref := ctx.message.reference):
                await ctx.reply("No code provided.")
                return

            content = await self.get_message_content(ctx.channel, ref)
            code = self.grep_code(content)
        else:
            code = codeblock_converter(code).content

        link = await self.share_code(code)

        await ctx.reply(f"<{link}>")


async def setup(bot: ReplBot) -> None:
    await bot.add_cog(Playground(bot))
