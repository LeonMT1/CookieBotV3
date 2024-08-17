from discord import slash_command
import discord
from discord import Option
import asyncio
from discord.ext import commands


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await asyncio.sleep(0.3)
        print("""            commands.py      ✅""")

    @slash_command()
    async def ping(self, ctx):
        print(f"{ctx.author} hat /ping ausgeführt")

        ping = round(self.bot.latency * 1000)

        await ctx.respond(f"Pong! {ping}ms", ephemeral=True)
        print(f"{ctx.author} wurde ein Ping von {ping}ms gesendet")

    @slash_command()
    async def mc_skin(self, ctx, username: Option(required=True),
                      render: Option(required=False, choices=["default", "marching", "walking", "crouching", "crossed",
                                                              "criss_cross", "ultimate", "isometric", "cheering",
                                                              "relaxing", "trudging", "cowering", "pointing", "lunging",
                                                              "dungeons", "facepalm", "sleeping", "dead", "archer",
                                                              "kicking", "mojavatar", "reading", "bitzel", "pixel"],
                                     default="default")):
        print(f"{ctx.author} hat /mc_skin ausgeführt")
        async with ctx.typing():
            embed = discord.Embed(title=f"Skin von {username}", color=discord.Color.random())
            embed.set_image(url=f"https://starlightskins.lunareclipse.studio/render/{render}/{username}/full")
            embed.set_thumbnail(url=f"https://starlightskins.lunareclipse.studio/render/head/{username}/full")
            button = discord.ui.Button(label="Download", url=f"https://minotar.net/download/{username}")
            view = discord.ui.View()
            view.add_item(button)
            await ctx.respond("Loading...", ephemeral=True)
            await ctx.send(embed=embed, view=view)
        print(f"{ctx.author} wurde der Skin von {username} gesendet mit den Render-Parameter {render}")


def setup(bot):
    bot.add_cog(Commands(bot))
