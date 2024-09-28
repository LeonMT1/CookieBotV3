import discord
from discord import Option
from discord import slash_command
from discord.ext import commands


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("""            moderation.py    ✅""")

    @slash_command()
    @commands.has_permissions(administrator=True)
    async def activity(self, ctx,
                       typ: Option(str, choices=["game", "stream"]), name: Option(str),
                       status: Option(str, choices=["online", "abwesend", "Bitte nicht Stören", "offline"]),
                       streamer: Option(str, default='https://twitch.tv/leonmt1_', required=False)):
        print(f"{ctx.author} hat /activity ausgeführt")

        if typ == "game":
            typ = discord.Game(name=name)

        if typ == "stream":
            typ = discord.Streaming(
                name=name,
                url=f"https://twitch.tv/{streamer}")

        if status == "online":
            status = discord.Status.online
        if status == "abwesend":
            status = discord.Status.idle
        if status == "Bitte nicht Stören":
            status = discord.Status.dnd
        if status == "offline":
            status = discord.Status.offline

        embed = discord.Embed(
            title="Aktivität erfolgreich geändert",
            description=f"Typ: {typ}\nName: {name}\nStatus: {status}",
            color=discord.Color.green()
        )

        await self.bot.change_presence(activity=typ, status=status)
        await ctx.respond(embed=embed, ephemeral=True)
        print(f"{ctx.author} hat die Aktivität auf folgende Parameter geändert: typ = {typ}, name = {name}, status = "
              f"{status}, streamer = {streamer}")


def setup(bot):
    bot.add_cog(Moderation(bot))
