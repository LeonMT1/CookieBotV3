import asyncio
import platform
import random

import psutil
import cpuinfo

import discord
import requests
from discord import slash_command
from ezcord import commands
from discord import Option


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
        await ctx.defer()
        embed = discord.Embed(title=f"Skin von {username}", color=discord.Color.random())
        embed.set_image(url=f"https://starlightskins.lunareclipse.studio/render/{render}/{username}/full")
        embed.set_thumbnail(url=f"https://starlightskins.lunareclipse.studio/render/head/{username}/full")
        button = discord.ui.Button(label="Download", url=f"https://minotar.net/download/{username}")
        view = discord.ui.View()
        view.add_item(button)
        await ctx.send(embed=embed, view=view)
        print(f"{ctx.author} wurde der Skin von {username} gesendet mit den Render-Parameter {render}")

    @slash_command()
    async def avatar(self, ctx, user: Option(discord.Member, required=False)):
        print(f"{ctx.author} hat /avatar ausgeführt")
        if not user:
            user = ctx.author
        embed = discord.Embed(
            title=f"Avatar von {user}",
            color=discord.Color.random()
        )
        embed.set_image(url=user.display_avatar.url)

        button = discord.ui.Button(label="Download Avatar", url=user.display_avatar.url)
        view = discord.ui.View()
        view.add_item(button)

        await ctx.respond(embed=embed, view=view)
        print(f"{ctx.author} wurde der Avatar von {user} gesendet")

    @slash_command()
    async def server_info(self, ctx):
        await ctx.defer()

        embed = discord.Embed(
            title="Server Info",
            color=discord.Color.green())
        embed.add_field(name="OS", value=f" OS: {platform.platform()} / {platform.release()}")
        embed.add_field(name="CPU", value=f" CPU: {cpuinfo.get_cpu_info()['brand_raw']}")
        embed.add_field(name="CPU Cores",
                        value=f"Cores: {psutil.cpu_count(logical=False)} and Threads: {psutil.cpu_count()}")
        embed.add_field(name="CPU Usage", value=f"Usage: {psutil.cpu_percent(interval=1)}%")
        embed.add_field(name="CPU Frequency", value=f"Frequency: {round(psutil.cpu_freq().current)} MHz")
        embed.add_field(name="RAM", value=f" RAM: {round(psutil.virtual_memory().total / 1024 ** 3)} GB")
        embed.add_field(name="RAM Usage", value=f"Usage: {round(psutil.virtual_memory().percent)}%")
        embed.add_field(name="DISK", value=f" Disk: {round(psutil.disk_usage('/').total / 1024 ** 3)} GB")
        embed.add_field(name="DISK Usage", value=f"Usage: {round(psutil.disk_usage('/').percent)}%")
        embed.add_field(name="Python Version", value=" Python Version " + str(platform.python_version()))
        await ctx.respond(embed=embed)
        print(f"{ctx.author} wurde die Server Info gesendet")

    @slash_command(description="Töte jemanden")
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def kill(self, ctx, member: discord.Member):
        print(f"{ctx.author.name} hat den Befehl /kill genutzt")
        key = "AIzaSyDHmg80hvYQrUvrTEee8ARuq9X-6hIE1EM"
        params = {"q": "kill",
                  "key": key,
                  "limit": 30,
                  "media_filter": "gif"}

        result = requests.get(f"https://tenor.googleapis.com/v2/search", params=params)
        data = result.json()
        number = random.randint(0, 30)
        url = data["results"][number]["media_formats"]["gif"]["url"]

        if member == self.bot.user:
            embot = discord.Embed(title="Ich bekomme alles mit!", color=discord.Color.orange(),
                                  description="Der Bot so krass, das er dich umgebracht hat!")
            embot.set_footer(text="Gif von Tenor")
            embot.set_image(
                url="https://cookieattack.me/img/notbywebsite/cookiekiller.gif")

        embed = discord.Embed(title=f"{ctx.author.name} hat {member} umgebracht!", color=discord.Color.darker_gray())
        embed.set_image(url=url)
        embed.set_footer(text="Gif von Tenor")
        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(Commands(bot))
